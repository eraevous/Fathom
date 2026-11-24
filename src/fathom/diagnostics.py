"""Diagnostics about the data for a declared task (spec 035; FT-DX35-R1..R5, Kate, independent).

Slice 1: the configuration block, the registry, the five statuses, the context gate, and the
checks W1 (duplicate rows with different targets), W5 (possible target-derived features),
T1 (class support) and T3 (count target range and dispersion).
Slice 2: the declared train/evaluation split and entity: W2 (duplicates across the split),
W3 (entity crossing the split), W4 (temporal order across the split), T2 (class support by
split), T4 (target range by split) and E4 (tree family: evaluation range and level coverage).
Every check reads the table alone; nothing here estimates a model (R3). Nothing runs unless
`diagnostics` is declared.
"""

import math
import statistics
from collections import Counter, defaultdict

from .parsing import finite_number, parse_date, parse_datetime
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
TYPE_NOTE = (" Column types used here are inferred, not declared (see type_basis); which W5 rule applies, how T1 "
             "reads the target and whether E4 compares ranges or levels rest on that inference, and declaring a task does "
             "not confirm column types.")
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
    {"id": "W2", "title": "Duplicates across the split", "tasks": TASKS, "families": "any",
     "roles": ("split",), "inputs": "declared features, and the split column's stored values",
     "computation": "group rows by exact feature values; count groups with rows on both the train and the evaluation side",
     "threshold": "any such group", "limitations": "exact matches only; rows outside both declared sides are left out and counted",
     "finding": "observation"},
    {"id": "W3", "title": "Entity crossing the split", "tasks": TASKS, "families": "any",
     "roles": ("split", "entity"), "inputs": "the entity column and the split column, as stored",
     "computation": "entities with rows on both sides; rows per entity (min, median, max)",
     "threshold": "any entity on both sides", "limitations": "entity values are compared as stored; rows with no entity are counted apart",
     "finding": "observation"},
    {"id": "W4", "title": "Temporal order across the split", "tasks": TASKS, "families": "any",
     "roles": ("split", "time"), "inputs": "the time column and the split column",
     "computation": "evaluation rows dated before the latest train row, and the overlap window",
     "threshold": "any such row", "limitations": ("ISO dates and date-times, and other date spellings with one reading only; "
                                                   "ambiguous or unparsed values are counted and left out"),
     "finding": "observation"},
    {"id": "T2", "title": "Class support by split", "tasks": ("classification",), "families": "any",
     "roles": ("target", "task", "split"), "inputs": "the target on each side of the split",
     "computation": "count and share of each class per side; classes present on one side only",
     "threshold": f"a class missing from one side; classes under {MIN_SUPPORT} rows per side are named",
     "limitations": "missing targets are counted apart, not as a class", "finding": "observation"},
    {"id": "T4", "title": "Target range by split", "tasks": ("regression", "count"), "families": "any",
     "roles": ("target", "task", "split"), "inputs": "the numeric target on each side of the split",
     "computation": "evaluation target values below the train minimum or above the train maximum",
     "threshold": "any such value", "limitations": "describes the stored range only; it says nothing about how values are distributed inside it",
     "finding": "observation"},
    {"id": "E4", "title": "Evaluation range coverage", "tasks": TASKS, "families": ("tree",),
     "roles": ("split",), "inputs": "each declared numeric or categorical feature on each side of the split",
     "computation": "numeric: evaluation values outside the train range; categorical: evaluation levels unseen in train",
     "threshold": "any such value or level", "limitations": "text, date and identifier features are listed as not evaluated",
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


def sides(rows, index, split):
    """Row positions (0-based) on each declared side, and the count of rows on neither."""
    si, train, evaluation = index[split["column"]], set(split["train"]), set(split["evaluation"])
    out = {"train": [], "evaluation": []}
    for i, r in enumerate(rows):
        if r[si] in train:
            out["train"].append(i)
        elif r[si] in evaluation:
            out["evaluation"].append(i)
    return out, len(rows) - len(out["train"]) - len(out["evaluation"])


def split_counts(side, outside):
    return {"train_rows": len(side["train"]), "evaluation_rows": len(side["evaluation"]), "outside_split": outside}


def empty_side(side, outside):
    """insufficient_data detail when a declared side has no rows, else None."""
    if side["train"] and side["evaluation"]:
        return None
    return {"rows_on_smaller_side": min(len(side["train"]), len(side["evaluation"])), "minimum": 1, **split_counts(side, outside)}


def w2(rows, index, features, split):
    side, outside = sides(rows, index, split)
    if (short := empty_side(side, outside)):
        return "insufficient_data", short
    fi = [index[f] for f in features]
    groups = defaultdict(lambda: ([], []))
    for k, name in enumerate(("train", "evaluation")):
        for i in side[name]:
            groups[tuple(rows[i][j] for j in fi)][k].append(i + 1)
    crossing = [g for g in groups.values() if g[0] and g[1]]
    detail = {"checked": f"{len(side['train']) + len(side['evaluation'])} rows on the declared sides, grouped on {len(features)} features",
              **split_counts(side, outside), "groups": len(crossing),
              "train_rows_matched": sum(len(t) for t, _ in crossing), "evaluation_rows_matched": sum(len(e) for _, e in crossing),
              "example_rows": sorted(p for t, e in crossing for p in t + e)[:EXAMPLES]}
    return ("signal" if crossing else "no_signal"), detail


def w3(rows, index, split, entity):
    side, outside = sides(rows, index, split)
    if (short := empty_side(side, outside)):
        return "insufficient_data", short
    ei = index[entity]
    seen, counts, no_entity = defaultdict(set), Counter(), 0
    for name in ("train", "evaluation"):
        for i in side[name]:
            value = rows[i][ei]
            if value is None:
                no_entity += 1
                continue
            seen[value].add(name)
            counts[value] += 1
    if not counts:
        return "insufficient_data", {"entities": 0, "minimum": 1, "rows_without_entity": no_entity}
    crossing = sorted(e for e, s in seen.items() if len(s) == 2)
    per = sorted(counts.values())
    detail = {"checked": f"{len(counts)} entities on the declared sides", **split_counts(side, outside),
              "entities_total": len(counts), "entities_on_both_sides": len(crossing),
              "rows_of_crossing_entities": sum(counts[e] for e in crossing), "example_entities": crossing[:EXAMPLES],
              "rows_per_entity": {"min": per[0], "median": statistics.median(per), "max": per[-1]},
              "rows_without_entity": no_entity}
    return ("signal" if crossing else "no_signal"), detail


def moment(value):
    """A datetime from strict ISO text, or from a date spelling with a single reading; otherwise None."""
    from datetime import datetime
    parsed = parse_datetime(value)
    if parsed:
        return parsed[0]
    found = parse_date(value)
    if found and not found["alternatives"]:
        return datetime.fromisoformat(found["date"])
    return None


def w4(rows, index, split, time):
    side, outside = sides(rows, index, split)
    if (short := empty_side(side, outside)):
        return "insufficient_data", short
    ti = index[time]
    stamps, unparsed = {}, 0
    for name in ("train", "evaluation"):
        stamps[name] = []
        for i in side[name]:
            at = moment(rows[i][ti]) if rows[i][ti] is not None else None
            if at is None:
                unparsed += 1
            else:
                stamps[name].append(at)
    if not stamps["train"] or not stamps["evaluation"]:
        return "insufficient_data", {"dated_rows_on_smaller_side": min(len(stamps["train"]), len(stamps["evaluation"])),
                                     "minimum": 1, "undated_rows": unparsed}
    latest_train, earliest_eval = max(stamps["train"]), min(stamps["evaluation"])
    early = sum(t < latest_train for t in stamps["evaluation"])
    detail = {"checked": f"{len(stamps['train'])} dated train rows and {len(stamps['evaluation'])} dated evaluation rows",
              **split_counts(side, outside), "evaluation_rows_before_latest_train": early,
              "share_of_evaluation": round(early / len(stamps["evaluation"]), 4),
              "latest_train": latest_train.isoformat(), "earliest_evaluation": earliest_eval.isoformat(),
              "overlap_window": [earliest_eval.isoformat(), latest_train.isoformat()] if early else None,
              "undated_rows": unparsed}
    return ("signal" if early else "no_signal"), detail


def t2(rows, index, columns, target, split):
    side, outside = sides(rows, index, split)
    if (short := empty_side(side, outside)):
        return "insufficient_data", short
    ti = index[target]
    boolean = columns[ti]["effective_type"] == "boolean"
    tables = {}
    for name in ("train", "evaluation"):
        values = [rows[i][ti] for i in side[name]]
        tables[name] = Counter(v.casefold() if boolean else v for v in values if v is not None)
    if len(tables["train"] | tables["evaluation"]) < 2:
        return "insufficient_data", {"classes": len(tables["train"] | tables["evaluation"]), "minimum": 2}
    def table(counts):
        n = sum(counts.values())
        ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        return {"rows_with_target": n,
                "classes": [{"class": k, "rows": c, "share": round(c / n, 4)} for k, c in ordered[:CLASS_LIST]],
                "classes_total": len(counts), "smallest": min(counts.values()) if counts else 0, "under_minimum": sorted(k for k, c in counts.items() if c < MIN_SUPPORT)}
    only_train = sorted(set(tables["train"]) - set(tables["evaluation"]))
    only_eval = sorted(set(tables["evaluation"]) - set(tables["train"]))
    detail = {"checked": f"{len(tables['train'] | tables['evaluation'])} classes across both sides", **split_counts(side, outside),
              "train": table(tables["train"]), "evaluation": table(tables["evaluation"]),
              "missing_from_evaluation": only_train, "missing_from_train": only_eval}
    return ("signal" if only_train or only_eval else "no_signal"), detail


def outside_range(train, evaluation):
    lo, hi = min(train), max(train)
    return sum(v < lo for v in evaluation), sum(v > hi for v in evaluation), lo, hi


def t4(rows, index, target, split):
    side, outside = sides(rows, index, split)
    if (short := empty_side(side, outside)):
        return "insufficient_data", short
    ti = index[target]
    values = {name: [v for v in (finite_number(rows[i][ti]) for i in side[name] if rows[i][ti] is not None) if v is not None]
              for name in ("train", "evaluation")}
    if not values["train"] or not values["evaluation"]:
        return "insufficient_data", {"numeric_targets_on_smaller_side": min(len(values["train"]), len(values["evaluation"])), "minimum": 1}
    below, above, lo, hi = outside_range(values["train"], values["evaluation"])
    detail = {"checked": f"{len(values['evaluation'])} evaluation target values against the train range", **split_counts(side, outside),
              "train_min": lo, "train_max": hi, "below_train_min": below, "above_train_max": above,
              "share_outside": round((below + above) / len(values["evaluation"]), 4)}
    return ("signal" if below + above else "no_signal"), detail


def e4(rows, index, columns, features, split):
    side, outside = sides(rows, index, split)
    if (short := empty_side(side, outside)):
        return "insufficient_data", short
    hits, checked, unevaluated = [], 0, []
    for name in features:
        fi = index[name]
        typ = columns[fi]["effective_type"]
        if typ not in NUMERIC and typ not in CATEGORY:
            unevaluated.append(name)
            continue
        cells = {k: [c for c in (cell(rows[i][fi], typ) for i in side[k]) if c is not None] for k in ("train", "evaluation")}
        if not cells["train"] or not cells["evaluation"]:
            unevaluated.append(name)
            continue
        checked += 1
        if typ in NUMERIC:
            below, above, lo, hi = outside_range(cells["train"], cells["evaluation"])
            if below + above:
                hits.append({"feature": name, "kind": "numeric", "below_train_min": below, "above_train_max": above,
                             "train_min": lo, "train_max": hi})
        else:
            known = set(cells["train"])
            unseen = Counter(v for v in cells["evaluation"] if v not in known)
            if unseen:
                hits.append({"feature": name, "kind": "categorical", "unseen_levels": len(unseen),
                             "evaluation_rows": sum(unseen.values()), "example_levels": sorted(unseen)[:EXAMPLES]})
    if not checked:
        return "insufficient_data", {"usable_features": 0, "minimum": 1, "not_evaluated": unevaluated}
    detail = {"checked": f"{checked} features against the train side" + (f"; {len(unevaluated)} not evaluated" if unevaluated else ""),
              **split_counts(side, outside), "features": hits, "not_evaluated": unevaluated}
    return ("signal" if hits else "no_signal"), detail


CHECKS = {"W1": lambda ctx: w1(ctx["rows"], ctx["index"], ctx["features"], ctx["target"]),
          "W5": lambda ctx: w5(ctx["rows"], ctx["index"], ctx["columns"], ctx["features"], ctx["target"], ctx["task"]),
          "T1": lambda ctx: t1(ctx["rows"], ctx["index"], ctx["columns"], ctx["target"]),
          "T3": lambda ctx: t3(ctx["rows"], ctx["index"], ctx["target"], ctx["block"].get("exposure")),
          "W2": lambda ctx: w2(ctx["rows"], ctx["index"], ctx["features"], ctx["split"]),
          "W3": lambda ctx: w3(ctx["rows"], ctx["index"], ctx["split"], ctx["entity"]),
          "W4": lambda ctx: w4(ctx["rows"], ctx["index"], ctx["split"], ctx["time"]),
          "T2": lambda ctx: t2(ctx["rows"], ctx["index"], ctx["columns"], ctx["target"], ctx["split"]),
          "T4": lambda ctx: t4(ctx["rows"], ctx["index"], ctx["target"], ctx["split"]),
          "E4": lambda ctx: e4(ctx["rows"], ctx["index"], ctx["columns"], ctx["features"], ctx["split"])}

ASK = {"target": "Declare `target` to run {ids}.",
       "task": "Declare `diagnostics.task` (one of classification, regression, count, forecast) to run {ids}; Fathom does not infer the task.",
       "time": "Declare `diagnostics.time` to check temporal ordering, history and cadence; no time-series check runs without it.",
       "split": "Declare `diagnostics.split` ({{column, train, evaluation}}) to run {ids}; Fathom does not guess which rows are held out.",
       "entity": "Declare `diagnostics.entity` to run {ids}; Fathom does not guess which column identifies an entity."}


def run(rows, columns, cfg, block):
    """Run every registered check through the context gate; each ends in exactly one status."""
    if block is None:
        return None
    index = {c["name"]: i for i, c in enumerate(columns)}
    features, basis = feature_set(columns, cfg, block)
    declared = {"target": cfg.get("target"), "task": block.get("task"),
                **{k: block.get(k) for k in ("split", "entity", "time")}}
    ctx = {"rows": rows, "columns": columns, "index": index, "features": features, "block": block, **declared}
    results, missing = [], defaultdict(list)
    for row in REGISTRY:
        if declared["task"] is not None and declared["task"] not in row["tasks"]:
            results.append(result(row, "not_applicable", reason=f"task is {declared['task']}; applies to " + ", ".join(row["tasks"])))
            continue
        if row["families"] != "any" and not set(row["families"]) & set(block["families"]):
            results.append(result(row, "not_applicable", reason="family not declared; applies to " + ", ".join(row["families"])))
            continue
        absent = [r for r in row["roles"] if declared.get(r) is None]
        if absent:
            for role in absent:
                missing[role].append(row["id"])
            results.append(result(row, "not_applicable", reason="needs " + " and ".join(absent)))
            continue
        if not features and row["id"] in ("W1", "W5", "W2", "E4"):
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
        missing.setdefault("time", [])
    questions = [{"role": role, "unlocks": ids, "question": ASK[role].format(ids=", ".join(ids))} for role, ids in missing.items()]
    warning_signal = any(r["id"].startswith("W") and r["status"] == "signal" for r in results)
    target_col = next((c for c in columns if c["name"] == cfg.get("target")), None)
    target_inferred = target_col is not None and not target_col.get("override")
    inferred = [cfg["target"]] if target_inferred else []
    rank_rule = target_col is not None and block.get("task") in ("regression", "count")  # W5's rank rule reads feature types
    e4_ran = any(r["id"] == "E4" and r["status"] in ("signal", "no_signal") for r in results)  # E4 picks range or levels by type
    if rank_rule or e4_ran:
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
    if r["id"] == "W3":
        p = r["rows_per_entity"]
        return f"; rows per entity min {p['min']}, median {p['median']}, max {p['max']}"
    if r["id"] == "T2":
        return f"; smallest class train {r['train']['smallest']}, evaluation {r['evaluation']['smallest']} rows"
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
    if r["id"] == "W2":
        return (f"W2: {r['groups']} groups of identical feature values have rows on both sides of the split "
                f"({r['train_rows_matched']} train rows, {r['evaluation_rows_matched']} evaluation rows); example rows (1-based): "
                + ", ".join(map(str, r["example_rows"])) + ".")
    if r["id"] == "W3":
        p = r["rows_per_entity"]
        return (f"W3: {r['entities_on_both_sides']} of {r['entities_total']} entities have rows in both train and evaluation "
                f"({r['rows_of_crossing_entities']} rows), for example " + ", ".join(r["example_entities"])
                + f"; rows per entity min {p['min']}, median {p['median']}, max {p['max']}.")
    if r["id"] == "W4":
        return (f"W4: {r['evaluation_rows_before_latest_train']} evaluation rows ({r['share_of_evaluation']} of dated evaluation rows) "
                f"are dated before the latest train row; overlap window {r['overlap_window'][0]} to {r['overlap_window'][1]}.")
    if r["id"] == "T2":
        parts = ([f"missing from evaluation: {', '.join(r['missing_from_evaluation'][:EXAMPLES])}"] if r["missing_from_evaluation"] else []) + \
                ([f"missing from train: {', '.join(r['missing_from_train'][:EXAMPLES])}"] if r["missing_from_train"] else [])
        return "T2: classes present on one side of the split only; " + "; ".join(parts) + "."
    if r["id"] == "T4":
        return (f"T4: {r['below_train_min'] + r['above_train_max']} evaluation target values ({r['share_outside']}) fall outside "
                f"the train range {r['train_min']} to {r['train_max']} ({r['below_train_min']} below, {r['above_train_max']} above).")
    if r["id"] == "E4":
        def one(h):
            if h["kind"] == "numeric":
                return f"{h['feature']} ({h['below_train_min']} below, {h['above_train_max']} above the train range)"
            return f"{h['feature']} ({h['unseen_levels']} levels unseen in train, {h['evaluation_rows']} evaluation rows)"
        return "E4 tree: evaluation values the train side never covers: " + "; ".join(one(h) for h in r["features"]) + "."
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
        for name in (cols if r["id"] == "W5" else []):
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
