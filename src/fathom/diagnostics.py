"""Diagnostics about the data for a declared task (spec 035 slice 1; FT-DX35-R1..R5, Kate, independent).

Slice 1: the configuration block, the registry, the five statuses, the context gate, and the
checks W1 (duplicate rows with different targets), W5 (possible target-derived features),
T1 (class support) and T3 (count target range and dispersion). Every check reads the table
alone; nothing here estimates a model (R3). Nothing runs unless `diagnostics` is declared.
"""

import math
import statistics
from collections import Counter, defaultdict

from .parsing import finite_number
from .target import CATEGORY, NUMERIC, cell
from .type_pairs import spearman

TASKS = ("classification", "regression", "count", "forecast")
FAMILIES = ("linear", "tree", "distance", "time_series")
ROLES = ("split", "entity", "time", "exposure")
UNITS = ("hour", "day", "week", "month", "year")
STATUSES = ("signal", "no_signal", "not_applicable", "insufficient_data", "failed")
MIN_SUPPORT, RANK_LIMIT, EXAMPLES, CLASS_LIST = 30, 0.98, 5, 50
LEAKAGE_SENTENCE = ("These checks can't show that the data is free of leakage; "
                    "that needs when each value becomes available.")
TYPE_NOTE = (" Column types used here are inferred, not declared (see type_basis); which W5 rule applies and how T1 "
             "reads the target rest on that inference, and declaring a task does not confirm column types.")
UNCERTAINTY = ("Computed from this table alone, for the declared task. A signal is a reason to look, "
               "not a defect verdict; an absent signal is not a certificate.")

REGISTRY = (
    {"id": "W1", "title": "Duplicate rows with different targets", "tasks": TASKS, "families": "any",
     "roles": ("target",), "inputs": "declared features and the target, as stored",
     "computation": "group rows by exact feature values; count groups whose present target values differ",
     "threshold": "any such group", "limitations": "exact matches only; near-duplicates and reformatted values are not grouped",
     "finding": "observation"},
    {"id": "W5", "title": "Possible target-derived features", "tasks": TASKS, "families": "any",
     "roles": ("target", "task"), "inputs": "each declared feature against the target",
     "computation": ("equal to the target on every complete row (any task); classification: levels map one-to-one "
                     "onto classes, or one level maps to a single class; regression and count: absolute Spearman rho"),
     "threshold": (f"one-to-one and single-class rules need at least {MIN_SUPPORT} rows per level and class; "
                   f"absolute rho >= {RANK_LIMIT}"),
     "limitations": "a match says nothing about when a value becomes available; a genuine strong predictor can fire",
     "finding": "observation, then question"},
    {"id": "T1", "title": "Class support", "tasks": ("classification",), "families": "any",
     "roles": ("target", "task"), "inputs": "the target",
     "computation": "count and share of each present class",
     "threshold": f"classes under {MIN_SUPPORT} rows are named",
     "limitations": "missing targets are counted apart, not as a class", "finding": "observation"},
    {"id": "T3", "title": "Count target range and dispersion", "tasks": ("count",), "families": "any",
     "roles": ("target", "task"), "inputs": "the target, and the declared exposure if any",
     "computation": "mean, sample variance, variance-to-mean ratio, share of zeros; exposure at or below 0, or missing",
     "threshold": "negative or non-whole target values, or exposure at or below 0 or missing, are the condition looked for; the dispersion figures are reported either way",
     "limitations": "the ratio describes the stored values; it does not choose a count family",
     "finding": "observation"},
)


def validate(raw, columns=None, target=None):
    """Return the cleaned `diagnostics` block; raise ValueError on undeclared keys or malformed roles."""
    if raw is None:
        return None
    allowed = {"task", "families", "features", "split", "entity", "time", "exposure", "horizon"}
    if not isinstance(raw, dict) or set(raw) - allowed:
        raise ValueError("diagnostics must be a mapping with keys: " + ", ".join(sorted(allowed)))
    known = (lambda name: columns is None or name in columns)
    out = {}
    if "task" in raw:
        if raw["task"] not in TASKS:
            raise ValueError("diagnostics.task must be one of: " + ", ".join(TASKS))
        out["task"] = raw["task"]
    families = raw.get("families", [])
    if not isinstance(families, list) or any(f not in FAMILIES for f in families) or len(set(families)) != len(families):
        raise ValueError("diagnostics.families must list distinct names from: " + ", ".join(FAMILIES))
    out["families"] = [f for f in FAMILIES if f in families]
    for key in ("entity", "time", "exposure"):
        if key in raw:
            if not isinstance(raw[key], str) or not known(raw[key]):
                raise ValueError(f"diagnostics.{key} must name a column in the table")
            out[key] = raw[key]
    if "split" in raw:
        split = raw["split"]
        if not isinstance(split, dict) or set(split) != {"column", "train", "evaluation"}:
            raise ValueError("diagnostics.split must be {column, train, evaluation}")
        if not isinstance(split["column"], str) or not known(split["column"]):
            raise ValueError("diagnostics.split.column must name a column in the table")
        sides = []
        for side in ("train", "evaluation"):
            values = split[side]
            if not isinstance(values, list) or not values or any(not isinstance(v, str) for v in values):
                raise ValueError(f"diagnostics.split.{side} must list one or more values")
            sides.append(set(values))
        if sides[0] & sides[1]:
            raise ValueError("diagnostics.split.train and evaluation must not share a value")
        out["split"] = {"column": split["column"], "train": list(split["train"]), "evaluation": list(split["evaluation"])}
    if "horizon" in raw:
        horizon = raw["horizon"]
        if (not isinstance(horizon, dict) or set(horizon) != {"value", "unit"} or type(horizon["value"]) is not int
                or horizon["value"] < 1 or horizon["unit"] not in UNITS):
            raise ValueError("diagnostics.horizon must be {value: positive integer, unit: " + "|".join(UNITS) + "}")
        if out.get("task") != "forecast":
            raise ValueError("diagnostics.horizon applies only to task: forecast")
        out["horizon"] = dict(horizon)
    if "exposure" in out and out.get("task") != "count":
        raise ValueError("diagnostics.exposure applies only to task: count")
    structural = {target} | {out.get(k) for k in ("entity", "time", "exposure")} | {out.get("split", {}).get("column")}
    if "features" in raw:
        features = raw["features"]
        if (not isinstance(features, list) or not features or any(not isinstance(f, str) for f in features)
                or len(set(features)) != len(features)):
            raise ValueError("diagnostics.features must list distinct column names")
        if any(not known(f) for f in features):
            raise ValueError("diagnostics.features references an unknown column")
        if any(f in structural for f in features):
            raise ValueError("diagnostics.features must not include the target or a declared structural role")
        out["features"] = list(features)
    return out


def feature_set(columns, cfg, block):
    """Declared features, or every column except the target, structural roles and exclude_from_target."""
    if "features" in block:
        return list(block["features"]), "declared"
    roles = {cfg.get("target"), block.get("entity"), block.get("time"), block.get("exposure"),
             block.get("split", {}).get("column")}
    return [c["name"] for c in columns if c["name"] not in roles and not c.get("exclude_from_target")], "default"


def finite(value):
    """True when every number in a result is finite (the artifact refuses NaN and infinity)."""
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(finite(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return all(finite(v) for v in value)
    return True


def result(row, status, **detail):
    return {"id": row["id"], "title": row["title"], "status": status, **detail}


def w1(rows, index, features, target):
    ti = index[target]
    fi = [index[f] for f in features]
    groups = defaultdict(list)
    for position, r in enumerate(rows, 1):
        if r[ti] is not None:
            groups[tuple(r[i] for i in fi)].append((position, r[ti]))
    present = sum(len(g) for g in groups.values())
    if present < 2:
        return "insufficient_data", {"usable_rows": present, "minimum": 2}
    conflicted = [g for g in groups.values() if len({t for _, t in g}) > 1]
    examples = sorted(p for g in conflicted for p, _ in g)[:EXAMPLES]
    detail = {"checked": f"{present} rows with a target, grouped on {len(features)} features",
              "groups": len(conflicted), "rows": sum(len(g) for g in conflicted), "example_rows": examples}
    return ("signal" if conflicted else "no_signal"), detail


def mapping_rules(pairs):
    """Classification rules for one feature: one-to-one relabelling, then single-class levels."""
    by_level, by_class = defaultdict(Counter), defaultdict(Counter)
    for x, y in pairs:
        by_level[x][y] += 1
        by_class[y][x] += 1
    if (len(by_level) >= 2 and all(len(c) == 1 for c in by_level.values()) and all(len(c) == 1 for c in by_class.values())
            and all(sum(c.values()) >= MIN_SUPPORT for c in by_level.values())
            and all(sum(c.values()) >= MIN_SUPPORT for c in by_class.values())):
        return {"rule": "levels map one-to-one onto classes", "levels": len(by_level)}
    single = sorted((str(level), sum(c.values()), next(iter(c))) for level, c in by_level.items()
                    if len(c) == 1 and sum(c.values()) >= MIN_SUPPORT)
    if single:
        return {"rule": "a level maps to a single class",
                "levels": [{"level": lv, "rows": n, "class": cls} for lv, n, cls in single[:EXAMPLES]],
                "levels_total": len(single)}
    return None


def w5(rows, index, columns, features, target, task):
    ti = index[target]
    ttype = columns[ti]["effective_type"]
    hits, checked, unevaluated = [], 0, []
    for name in features:
        fi = index[name]
        complete = [(r[fi], r[ti]) for r in rows if r[fi] is not None and r[ti] is not None]
        if len(complete) < 2:
            unevaluated.append(name)
            continue
        if len({y for _, y in complete}) >= 2 and all(x == y for x, y in complete):
            hits.append({"feature": name, "rule": "equal to the target on every complete row", "rows": len(complete)})
            checked += 1
            continue
        if task == "classification":
            # Classes as T1 counts them: Boolean spellings are case-folded, other labels kept as stored.
            found = mapping_rules([(x, y.casefold()) for x, y in complete] if ttype == "boolean" else complete)
            if found:
                hits.append({"feature": name, **found, "rows": len(complete)})
            checked += 1
        elif task in ("regression", "count") and ttype in NUMERIC and columns[fi]["effective_type"] in NUMERIC:
            cases = [(cell(x, "numeric"), cell(y, "numeric")) for x, y in complete]
            cases = [(x, y) for x, y in cases if x is not None and y is not None]
            rho = spearman([x for x, _ in cases], [y for _, y in cases]) if len(cases) >= 3 else None
            if rho is None:  # the rank rule could not be computed: not a negative result
                unevaluated.append(name)
                continue
            checked += 1
            if abs(rho) >= RANK_LIMIT:
                hits.append({"feature": name, "rule": f"absolute Spearman rho >= {RANK_LIMIT}",
                             "spearman_rho": round(rho, 4), "rows": len(cases)})
        else:
            checked += 1
    if not checked and not hits:
        return "insufficient_data", {"usable_features": 0, "minimum": 1, "not_evaluated": unevaluated}
    detail = {"checked": f"{checked} features against the target"
              + (f"; {len(unevaluated)} could not be evaluated" if unevaluated else ""),
              "features": hits, "not_evaluated": unevaluated}
    return ("signal" if hits else "no_signal"), detail


def t1(rows, index, columns, target):
    ti = index[target]
    boolean = columns[ti]["effective_type"] == "boolean"
    # Class labels stay as stored text (no float parsing, which can merge distinct labels).
    values = [r[ti].casefold() if boolean and r[ti] is not None else r[ti] for r in rows]
    counts = Counter(v for v in values if v is not None)
    present = sum(counts.values())
    if len(counts) < 2:
        return "insufficient_data", {"classes": len(counts), "minimum": 2, "rows_with_target": present}
    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    small = sorted(k for k, n in counts.items() if n < MIN_SUPPORT)
    detail = {"checked": f"{len(counts)} classes over {present} rows with a target",
              "classes": [{"class": k, "rows": n, "share": round(n / present, 4)} for k, n in ordered[:CLASS_LIST]],
              "classes_total": len(counts), "missing_target": sum(r[ti] is None for r in rows),
              "smallest": ordered[-1][1], "under_minimum": small}
    return ("signal" if small else "no_signal"), detail


def t3(rows, index, target, exposure):
    ti = index[target]
    raw = [r[ti] for r in rows if r[ti] is not None]
    values = [v for v in (finite_number(x) for x in raw) if v is not None]
    if len(values) < 2:
        return "insufficient_data", {"usable_rows": len(values), "minimum": 2}
    mean, variance = statistics.fmean(values), statistics.variance(values)
    negative = sum(v < 0 for v in values)
    fractional = sum(not float(v).is_integer() for v in values)
    detail = {"checked": f"{len(values)} numeric target values", "mean": round(mean, 6), "variance": round(variance, 6),
              "variance_to_mean": round(variance / mean, 6) if mean > 0 else None,
              "zero_share": round(sum(v == 0 for v in values) / len(values), 4),
              "negative": negative, "not_whole": fractional, "unparsed": len(raw) - len(values)}
    flags = negative + fractional
    if exposure is not None:
        ei = index[exposure]
        exp = [finite_number(r[ei]) if r[ei] is not None else None for r in rows]
        detail["exposure_missing"] = sum(r[ei] is None for r in rows)
        detail["exposure_unparsed"] = sum(r[ei] is not None and e is None for r, e in zip(rows, exp))
        detail["exposure_at_or_below_zero"] = sum(e is not None and e <= 0 for e in exp)
        flags += detail["exposure_missing"] + detail["exposure_unparsed"] + detail["exposure_at_or_below_zero"]
    return ("signal" if flags else "no_signal"), detail


CHECKS = {"W1": lambda ctx: w1(ctx["rows"], ctx["index"], ctx["features"], ctx["target"]),
          "W5": lambda ctx: w5(ctx["rows"], ctx["index"], ctx["columns"], ctx["features"], ctx["target"], ctx["task"]),
          "T1": lambda ctx: t1(ctx["rows"], ctx["index"], ctx["columns"], ctx["target"]),
          "T3": lambda ctx: t3(ctx["rows"], ctx["index"], ctx["target"], ctx["block"].get("exposure"))}

ASK = {"target": "Declare `target` to run {ids}.",
       "task": "Declare `diagnostics.task` (one of classification, regression, count, forecast) to run {ids}; Fathom does not infer the task.",
       "time": "Declare `diagnostics.time` to check temporal ordering, history and cadence; no time-series check runs without it."}


def run(rows, columns, cfg, block):
    """Run every registered check through the context gate; each ends in exactly one status."""
    if block is None:
        return None
    index = {c["name"]: i for i, c in enumerate(columns)}
    features, basis = feature_set(columns, cfg, block)
    declared = {"target": cfg.get("target"), "task": block.get("task")}
    ctx = {"rows": rows, "columns": columns, "index": index, "features": features, "block": block, **declared}
    results, missing = [], defaultdict(list)
    for row in REGISTRY:
        if declared["task"] is not None and declared["task"] not in row["tasks"]:
            results.append(result(row, "not_applicable", reason=f"task is {declared['task']}; applies to " + ", ".join(row["tasks"])))
            continue
        absent = [r for r in row["roles"] if declared.get(r) is None]
        if absent:
            for role in absent:
                missing[role].append(row["id"])
            results.append(result(row, "not_applicable", reason="needs " + " and ".join(absent)))
            continue
        if not features and row["id"] in ("W1", "W5"):
            results.append(result(row, "insufficient_data", usable_features=0, minimum=1))
            continue
        try:
            status, detail = CHECKS[row["id"]](ctx)
            if not finite(detail):
                raise ArithmeticError("non-finite result")
        except Exception as error:  # R2: a failed computation is its own status; the run continues
            status, detail = "failed", {"error": type(error).__name__}
        results.append(result(row, status, **detail))
    if (block.get("task") == "forecast" or "time_series" in block["families"]) and "time" not in block:
        missing["time"] = []
    questions = [{"role": role, "unlocks": ids, "question": ASK[role].format(ids=", ".join(ids))} for role, ids in missing.items()]
    warning_signal = any(r["id"].startswith("W") and r["status"] == "signal" for r in results)
    target_col = next((c for c in columns if c["name"] == cfg.get("target")), None)
    target_inferred = target_col is not None and not target_col.get("override")
    inferred = [cfg["target"]] if target_inferred else []
    if target_col is not None and block.get("task") in ("regression", "count"):  # W5's rank rule reads feature types too
        inferred += [c["name"] for c in columns if c["name"] in features and not c.get("override")]
    return {"context": {"task": block.get("task"), "families": block["families"], "target": cfg.get("target"),
                        **{k: block[k] for k in ("split", "entity", "time", "exposure", "horizon") if k in block}},
            "features": {"basis": basis, "columns": features},
            "registry": [{k: (list(v) if isinstance(v, tuple) else v) for k, v in row.items()} for row in REGISTRY],
            "statuses": list(STATUSES), "results": results, "questions": questions,
            "leakage_note": None if warning_signal else LEAKAGE_SENTENCE,
            "type_basis": {"target": None if target_col is None else ("inferred" if target_inferred else "human-declared"),
                           "inferred_columns": inferred},
            "uncertainty": UNCERTAINTY + (TYPE_NOTE if inferred else "")}


def describe(r):
    """One line per result; the five statuses never share wording."""
    status = r["status"]
    if status == "no_signal":
        return f"{r['id']} {r['title']}: checked, not found ({r['checked']}{figures(r)})."
    if status == "not_applicable":
        return f"{r['id']} {r['title']}: not applicable, {r['reason']}."
    if status == "insufficient_data":
        count = next((f"{k.replace('_', ' ')} {v}" for k, v in r.items() if k not in ("id", "title", "status", "minimum")), "")
        return f"{r['id']} {r['title']}: too little data to compute ({count}; minimum {r['minimum']})."
    if status == "failed":
        return f"{r['id']} {r['title']}: computation failed ({r['error']}); the other checks still ran."
    return signal_message(r)


def figures(r):
    """The descriptive figures a check reports whatever its status (T1 class support, T3 dispersion)."""
    if r["id"] == "T1":
        return f"; smallest class {r['smallest']} rows"
    if r["id"] == "T3":
        ratio = "undefined" if r["variance_to_mean"] is None else r["variance_to_mean"]
        return (f"; mean {r['mean']}, variance {r['variance']}, variance-to-mean {ratio}, "
                f"zero share {r['zero_share']}")
    return ""


def signal_message(r):
    if r["id"] == "W1":
        return (f"W1: {r['groups']} groups of rows ({r['rows']} rows) share every feature value but have different targets; "
                "example rows (1-based): " + ", ".join(map(str, r["example_rows"])) + ".")
    if r["id"] == "W5":
        return "W5 possible target-derived features: " + "; ".join(f"{h['feature']} ({h['rule']})" for h in r["features"]) + "."
    if r["id"] == "T1":
        return (f"T1: {len(r['under_minimum'])} of {r['classes_total']} classes have fewer than {MIN_SUPPORT} rows: "
                + ", ".join(r["under_minimum"][:EXAMPLES]) + (" and more" if len(r["under_minimum"]) > EXAMPLES else "")
                + f"; the smallest has {r['smallest']}.")
    parts = [f"{r['negative']} negative" if r["negative"] else "", f"{r['not_whole']} not whole" if r["not_whole"] else "",
             f"{r.get('exposure_missing', 0)} missing exposure" if r.get("exposure_missing") else "",
             f"{r.get('exposure_unparsed', 0)} exposure not a number" if r.get("exposure_unparsed") else "",
             f"{r.get('exposure_at_or_below_zero', 0)} exposure at or below 0" if r.get("exposure_at_or_below_zero") else ""]
    ratio = "undefined" if r["variance_to_mean"] is None else r["variance_to_mean"]
    return (f"T3: count target values a count cannot hold or unusable exposure: " + ", ".join(p for p in parts if p)
            + f". Mean {r['mean']}, variance {r['variance']}, variance-to-mean {ratio}, zero share {r['zero_share']}.")


def emit(diagnostics, finding):
    """Findings: one observation per signal, a question per W5 feature and per missing role, one status line."""
    if not diagnostics:
        return
    for i, r in enumerate(diagnostics["results"]):
        if r["status"] != "signal":
            continue
        cols = [h["feature"] for h in r.get("features", [])]
        finding(f"diagnostics-{r['id']}", "observation", signal_message(r),
                [{"path": f"diagnostics.results.{i}", "value": {k: v for k, v in r.items() if k not in ("title",)}}],
                diagnostics["uncertainty"], "rule:diagnostics-v1", rule=f"diagnostic_{r['id']}",
                **({"columns": cols} if cols else {}))
        for name in cols:
            finding(f"diagnostics-W5-{name}-timing", "question",
                    f"When is the value of {name} known relative to the target?",
                    [{"finding": "diagnostics-W5"}], "The table cannot show when a value becomes available.",
                    "rule:diagnostics-v1", rule="diagnostic_W5", columns=[name])
    for q in diagnostics["questions"]:
        finding(f"diagnostics-needs-{q['role']}", "question", q["question"],
                [{"path": "diagnostics.questions", "value": q}], "Fathom does not infer task, target or structural roles.",
                "rule:diagnostics-v1", rule="diagnostic_context_gate")
    lines = [describe(r) for r in diagnostics["results"] if r["status"] != "signal"]
    if diagnostics["leakage_note"]:
        lines.append(diagnostics["leakage_note"])
    if lines:
        finding("diagnostics-checks", "observation", "Diagnostics: " + " ".join(lines),
                [{"path": f"diagnostics.results.{i}", "value": {k: v for k, v in r.items() if k != "title"}}
                 for i, r in enumerate(diagnostics["results"]) if r["status"] != "signal"],
                diagnostics["uncertainty"], "rule:diagnostics-v1", rule="diagnostic_status")
