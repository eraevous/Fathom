"""Diagnostics about the data for a declared task (spec 035; FT-DX35-R1..R5, Kate, independent).

Slice 1: the configuration block, the registry, the five statuses, the context gate, and the
checks W1 (duplicate rows with different targets), W5 (possible target-derived features),
T1 (class support) and T3 (count target range and dispersion).
Slice 2: the declared train/evaluation split and entity: W2 (duplicates across the split),
W3 (entity crossing the split), W4 (temporal order across the split), T2 (class support by
split), T4 (target range by split) and E4 (tree family: evaluation range and level coverage).
Slice 3: the linear and tree families: L1 (design rank and conditioning), L2 (sparse levels), L3 (complete
separation in the data), E1 (rare-level support), E2 (identifier-like features) and E3 (missingness against
the target). Each reports a condition of this table for the family; none ranks families or says which to use (R5).
Every check reads the table alone; nothing here estimates a model (R3). Nothing runs unless
`diagnostics` is declared.
"""

import math
import statistics
from collections import Counter, defaultdict

from .identifiers import is_identifier
from .parsing import finite_number, parse_date, parse_datetime
from .target import CATEGORY, NUMERIC, cell
from .type_pairs import spearman

TASKS = ("classification", "regression", "count", "forecast")
FAMILIES = ("linear", "tree", "distance", "time_series")
ROLES = ("split", "entity", "time", "exposure")
UNITS = ("hour", "day", "week", "month", "year")
STATUSES = ("signal", "no_signal", "not_applicable", "insufficient_data", "failed")
MIN_SUPPORT, RANK_LIMIT, EXAMPLES, CLASS_LIST = 30, 0.98, 5, 50
DESIGN_CAP, DEPENDENT_TOL, CONDITION_LIMIT, VIF_LIMIT = 12, 1e-6, 30.0, 10.0
DISTINCT_SHARE, MISSING_GAP, MEAN_GAP = 0.9, 0.10, 0.2
LEAKAGE_SENTENCE = ("These checks can't show that the data is free of leakage; "
                    "that needs when each value becomes available.")
TYPE_NOTE = (" Column types used here are inferred, not declared (see type_basis); which W5 rule applies, how T1 "
             "reads the target, whether E4 compares ranges or levels, and which features the linear and tree checks treat as "
             "numeric or categorical rest on that inference, and declaring a task does "
             "not confirm column types.")
TYPED = ("E4", "L1", "L2", "L3", "E1", "E2", "E3")
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
    {"id": "L1", "title": "Design rank and conditioning", "tasks": TASKS, "families": ("linear",),
     "roles": ("features",), "inputs": f"the declared numeric features, at most {DESIGN_CAP} in feature order, on rows where all parse",
     "computation": ("standardize each feature; constant features, features that are a linear combination of earlier ones, "
                     "the condition number of the standardized design and each feature's variance inflation factor"),
     "threshold": (f"a constant or dependent feature, or a condition number of at least {CONDITION_LIMIT:g}; "
                   f"features with a variance inflation factor of at least {VIF_LIMIT:g} are named"),
     "limitations": "numeric features only, as stored; categorical indicators and transformations are not part of the design",
     "finding": "observation"},
    {"id": "L2", "title": "Sparse levels", "tasks": TASKS, "families": ("linear",),
     "roles": ("features",), "inputs": "each declared categorical or boolean feature",
     "computation": "count the rows of each level; levels under the minimum would become near-empty indicator columns",
     "threshold": f"any level under {MIN_SUPPORT} rows", "limitations": "missing cells are not a level; identifier features are listed as not evaluated",
     "finding": "observation"},
    {"id": "L3", "title": "Complete separation in the data", "tasks": ("classification",), "families": ("linear",),
     "roles": ("target", "task"), "inputs": "each declared feature against the target, on complete rows",
     "computation": ("categorical: levels whose rows all hold one class; numeric: a class whose values all lie below, or all "
                     "above, every other class's values"),
     "threshold": "any such level or threshold",
     "limitations": "one feature at a time; separation by a combination of features is not searched",
     "finding": "observation"},
    {"id": "E1", "title": "Rare-level support", "tasks": TASKS, "families": ("tree",),
     "roles": ("features",), "inputs": "each declared categorical or boolean feature",
     "computation": "count the rows of each level; the share of rows that sit in rare levels",
     "threshold": f"any level under {MIN_SUPPORT} rows", "limitations": "missing cells are not a level; identifier features are listed as not evaluated",
     "finding": "observation"},
    {"id": "E2", "title": "Identifier-like features", "tasks": TASKS, "families": ("tree",),
     "roles": ("features",), "inputs": "each declared feature",
     "computation": ("the identifier role (declared or inferred), or, for features not read as numeric, the share of "
                     "distinct values among present cells"),
     "threshold": f"identifier role, or a distinct share of at least {DISTINCT_SHARE} over at least {MIN_SUPPORT} present cells",
     "limitations": "numeric features are judged by the identifier role only; many distinct measurements are not memorisation",
     "finding": "observation"},
    {"id": "E3", "title": "Missingness against the target", "tasks": ("classification", "regression", "count"),
     "families": ("tree",), "roles": ("target", "task"), "inputs": "each declared feature's missing cells against the target",
     "computation": ("classification: the feature's missing share within each class; regression and count: the target "
                     "mean where the feature is missing against where it is present, over the target's standard deviation"),
     "threshold": (f"a gap of at least {MISSING_GAP} in missing share between classes with {MIN_SUPPORT} or more rows; "
                   f"a standardized mean gap of at least {MEAN_GAP} with {MIN_SUPPORT} or more rows on each side"),
     "limitations": "describes association with missingness in this table; it does not say why values are missing",
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
        if is_identifier(columns[fi]) or (typ not in NUMERIC and typ not in CATEGORY):
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


def symmetric_eigenvalues(matrix):
    """Eigenvalues of a small symmetric matrix by cyclic Jacobi rotations (standard library; at most 12 x 12)."""
    a, n = [row[:] for row in matrix], len(matrix)
    for _ in range(100):
        if sum(a[i][j] ** 2 for i in range(n) for j in range(n) if i != j) < 1e-24:
            break
        for p in range(n):
            for q in range(p + 1, n):
                if a[p][q] == 0.0:
                    continue
                theta = (a[q][q] - a[p][p]) / (2 * a[p][q])
                t = (1.0 if theta >= 0 else -1.0) / (abs(theta) + math.sqrt(theta * theta + 1))
                c = 1 / math.sqrt(t * t + 1)
                s = t * c
                for k in range(n):
                    a[k][p], a[k][q] = c * a[k][p] - s * a[k][q], s * a[k][p] + c * a[k][q]
                for k in range(n):
                    a[p][k], a[q][k] = c * a[p][k] - s * a[q][k], s * a[p][k] + c * a[q][k]
    return sorted(a[i][i] for i in range(n))


def inverse_diagonal(matrix):
    """Diagonal of the inverse of a positive definite matrix (Gauss-Jordan with partial pivoting)."""
    n = len(matrix)
    a = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(a[r][col]))
        a[col], a[pivot] = a[pivot], a[col]
        lead = a[col][col]
        a[col] = [v / lead for v in a[col]]
        for r in range(n):
            if r != col and a[r][col] != 0.0:
                factor = a[r][col]
                a[r] = [v - factor * w for v, w in zip(a[r], a[col])]
    return [a[i][n + i] for i in range(n)]


def usable_type(column):
    """'numeric', 'categorical' or None (identifier, text, date), from the effective type."""
    if is_identifier(column):
        return None
    typ = column["effective_type"]
    return "numeric" if typ in NUMERIC else "categorical" if typ in CATEGORY else None


def l1(rows, index, columns, features):
    numeric = [f for f in features if usable_type(columns[index[f]]) == "numeric"]
    design, over_cap = numeric[:DESIGN_CAP], numeric[DESIGN_CAP:]
    unevaluated = [f for f in features if f not in numeric] + over_cap
    if len(design) < 2:
        return "insufficient_data", {"numeric_features": len(design), "minimum": 2, "not_evaluated": unevaluated}
    fi = [index[f] for f in design]
    data = []
    for r in rows:
        values = [cell(r[i], "numeric") for i in fi]
        if all(v is not None for v in values):
            data.append(values)
    if len(data) < MIN_SUPPORT:
        return "insufficient_data", {"complete_rows": len(data), "minimum": MIN_SUPPORT, "not_evaluated": unevaluated}
    n = len(data)
    z, constant, kept = [], [], []
    for j, name in enumerate(design):
        col = [row[j] for row in data]
        if len(set(col)) == 1:  # before centering: a rounded mean can leave a constant column a tiny spread
            constant.append(name)
            continue
        mean = math.fsum(col) / n
        sd = math.sqrt(math.fsum((v - mean) ** 2 for v in col) / n)
        if sd == 0.0 or not math.isfinite(sd):
            constant.append(name)
            continue
        z.append([(v - mean) / sd for v in col])
        kept.append(name)
    basis, dependent = [], []
    for name, col in zip(kept, z):
        rest = col[:]
        for b in basis:
            proj = math.fsum(x * y for x, y in zip(rest, b))
            rest = [x - proj * y for x, y in zip(rest, b)]
        norm = math.sqrt(math.fsum(x * x for x in rest))
        if norm * norm < DEPENDENT_TOL * n:
            dependent.append(name)
        else:
            basis.append([x / norm for x in rest])
    corr = [[math.fsum(x * y for x, y in zip(a, b)) / n for b in z] for a in z]
    condition, vifs = None, []
    if not dependent and kept:
        eig = symmetric_eigenvalues(corr)
        if eig[0] > 0:
            condition = math.sqrt(eig[-1] / eig[0])
            vifs = [{"feature": name, "vif": round(v, 4)} for name, v in zip(kept, inverse_diagonal(corr)) if v >= VIF_LIMIT]
    involved = sorted({*constant, *dependent, *(v["feature"] for v in vifs)}, key=design.index)
    detail = {"checked": f"{len(design)} numeric features over {n} complete rows"
              + (f"; {len(unevaluated)} not in the design" if unevaluated else ""),
              "design": design, "complete_rows": n, "constant": constant, "dependent": dependent,
              "condition_number": None if condition is None else round(condition, 4), "high_vif": vifs,
              "features": [{"feature": f} for f in involved], "not_evaluated": unevaluated}
    flagged = constant or dependent or (condition is not None and condition >= CONDITION_LIMIT)
    return ("signal" if flagged else "no_signal"), detail


def level_counts(rows, index, columns, features):
    """Per categorical feature: level counts over present cells (Boolean spellings case-folded); others not evaluated."""
    tables, unevaluated = {}, []
    for name in features:
        column = columns[index[name]]
        if usable_type(column) != "categorical":
            unevaluated.append(name)
            continue
        fi, typ = index[name], column["effective_type"]
        counts = Counter(c for c in (cell(r[fi], typ) for r in rows) if c is not None)
        if counts:
            tables[name] = counts
        else:
            unevaluated.append(name)
    return tables, unevaluated


def sparse(rows, index, columns, features):
    tables, unevaluated = level_counts(rows, index, columns, features)
    if not tables:
        return "insufficient_data", {"categorical_features": 0, "minimum": 1, "not_evaluated": unevaluated}
    hits = []
    for name, counts in tables.items():
        small = sorted((k for k, c in counts.items() if c < MIN_SUPPORT), key=lambda k: (counts[k], k))
        if small:
            present = sum(counts.values())
            hits.append({"feature": name, "levels": len(counts), "sparse_levels": len(small),
                         "rows_in_sparse_levels": sum(counts[k] for k in small),
                         "share_of_rows": round(sum(counts[k] for k in small) / present, 4),
                         "example_levels": [{"level": k, "rows": counts[k]} for k in small[:EXAMPLES]]})
    detail = {"checked": f"{len(tables)} categorical features" + (f"; {len(unevaluated)} not evaluated" if unevaluated else ""),
              "features": hits, "not_evaluated": unevaluated}
    return ("signal" if hits else "no_signal"), detail


def target_class(value, boolean):
    return value.casefold() if boolean else value


def l3(rows, index, columns, features, target):
    ti = index[target]
    boolean = columns[ti]["effective_type"] == "boolean"
    hits, checked, unevaluated = [], 0, []
    for name in features:
        fi, column = index[name], columns[index[name]]
        kind = usable_type(column)
        pairs = [(cell(r[fi], column["effective_type"]), target_class(r[ti], boolean)) for r in rows
                 if r[fi] is not None and r[ti] is not None] if kind else []
        pairs = [(x, y) for x, y in pairs if x is not None]
        if len({y for _, y in pairs}) < 2:
            unevaluated.append(name)
            continue
        checked += 1
        if kind == "categorical":
            by_level = defaultdict(Counter)
            for x, y in pairs:
                by_level[x][y] += 1
            pure = sorted(((lv, sum(c.values()), next(iter(c))) for lv, c in by_level.items() if len(c) == 1),
                          key=lambda t: (-t[1], t[0]))
            if pure:
                hits.append({"feature": name, "kind": "level", "levels": len(pure),
                             "rows": sum(n for _, n, _ in pure),
                             "example_levels": [{"level": lv, "rows": n, "class": cls} for lv, n, cls in pure[:EXAMPLES]]})
            continue
        by_class = defaultdict(list)
        for x, y in pairs:
            by_class[y].append(x)
        classes = sorted(by_class)
        for cls in classes[:1] if len(classes) == 2 else classes:
            own = by_class[cls]
            rest = [v for k in classes if k != cls for v in by_class[k]]
            if max(own) < min(rest):
                hits.append({"feature": name, "kind": "threshold", "class": cls, "side": "below", "between": [max(own), min(rest)]})
            elif min(own) > max(rest):
                hits.append({"feature": name, "kind": "threshold", "class": cls, "side": "above", "between": [max(rest), min(own)]})
    if not checked:
        return "insufficient_data", {"usable_features": 0, "minimum": 1, "not_evaluated": unevaluated}
    detail = {"checked": f"{checked} features against the target" + (f"; {len(unevaluated)} not evaluated" if unevaluated else ""),
              "features": hits, "not_evaluated": unevaluated}
    return ("signal" if hits else "no_signal"), detail


def e2(rows, index, columns, features):
    hits, checked = [], 0
    for name in features:
        column = columns[index[name]]
        checked += 1
        if is_identifier(column):
            hits.append({"feature": name, "rule": "identifier role"})
            continue
        if column["effective_type"] in NUMERIC:
            continue
        present = [r[index[name]] for r in rows if r[index[name]] is not None]
        if len(present) >= MIN_SUPPORT:
            share = len(set(present)) / len(present)
            if share >= DISTINCT_SHARE:
                hits.append({"feature": name, "rule": f"distinct share >= {DISTINCT_SHARE}", "distinct_share": round(share, 4),
                             "present_cells": len(present)})
    detail = {"checked": f"{checked} features", "features": hits}
    return ("signal" if hits else "no_signal"), detail


def e3(rows, index, columns, features, target, task):
    ti = index[target]
    boolean = columns[ti]["effective_type"] == "boolean"
    known = [r for r in rows if r[ti] is not None]
    if task == "classification":
        classes = Counter(target_class(r[ti], boolean) for r in known)
        large = sorted(k for k, c in classes.items() if c >= MIN_SUPPORT)
        if len(large) < 2:
            return "insufficient_data", {"classes_with_minimum_rows": len(large), "minimum": 2}
    else:
        ys = [finite_number(r[ti]) for r in known]
        known = [r for r, y in zip(known, ys) if y is not None]
        ys = [y for y in ys if y is not None]
        if len(ys) < 2 * MIN_SUPPORT:
            return "insufficient_data", {"numeric_targets": len(ys), "minimum": 2 * MIN_SUPPORT}
        mean = math.fsum(ys) / len(ys)
        sd = math.sqrt(math.fsum((y - mean) ** 2 for y in ys) / len(ys))
        if sd == 0.0:
            return "insufficient_data", {"target_spread": 0, "minimum": "a non-constant target"}
    hits, with_missing, compared = [], 0, 0
    for name in features:
        fi = index[name]
        if not any(r[fi] is None for r in known):
            continue
        with_missing += 1
        if task == "classification":
            shares = {}
            for k in large:
                group = [r for r in known if target_class(r[ti], boolean) == k]
                shares[k] = sum(r[fi] is None for r in group) / len(group)
            compared += 1
            gap = max(shares.values()) - min(shares.values())
            if gap >= MISSING_GAP:
                hits.append({"feature": name, "missing_share_by_class": {k: round(v, 4) for k, v in shares.items()},
                             "gap": round(gap, 4)})
            continue
        missing = [y for r, y in zip(known, ys) if r[fi] is None]
        present = [y for r, y in zip(known, ys) if r[fi] is not None]
        if len(missing) < MIN_SUPPORT or len(present) < MIN_SUPPORT:
            continue
        compared += 1
        m_missing, m_present = math.fsum(missing) / len(missing), math.fsum(present) / len(present)
        gap = abs(m_missing - m_present) / sd
        if gap >= MEAN_GAP:
            hits.append({"feature": name, "target_mean_missing": round(m_missing, 6), "target_mean_present": round(m_present, 6),
                         "rows_missing": len(missing), "standardized_gap": round(gap, 4)})
    if with_missing and not compared:  # every feature with missing cells fell under the minimum: nothing was compared
        return "insufficient_data", {"features_compared": 0, "minimum": 1, "features_with_missing": with_missing,
                                     "rows_per_group_minimum": MIN_SUPPORT}
    detail = {"checked": f"{len(features)} features, {with_missing} with missing cells, {compared} compared",
              "features_with_missing": with_missing, "compared": compared, "features": hits}
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
          "E4": lambda ctx: e4(ctx["rows"], ctx["index"], ctx["columns"], ctx["features"], ctx["split"]),
          "L1": lambda ctx: l1(ctx["rows"], ctx["index"], ctx["columns"], ctx["features"]),
          "L2": lambda ctx: sparse(ctx["rows"], ctx["index"], ctx["columns"], ctx["features"]),
          "L3": lambda ctx: l3(ctx["rows"], ctx["index"], ctx["columns"], ctx["features"], ctx["target"]),
          "E1": lambda ctx: sparse(ctx["rows"], ctx["index"], ctx["columns"], ctx["features"]),
          "E2": lambda ctx: e2(ctx["rows"], ctx["index"], ctx["columns"], ctx["features"]),
          "E3": lambda ctx: e3(ctx["rows"], ctx["index"], ctx["columns"], ctx["features"], ctx["target"], ctx["task"])}

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
        absent = [r for r in row["roles"] if r != "features" and declared.get(r) is None]  # features: declared or default
        if absent:
            for role in absent:
                missing[role].append(row["id"])
            results.append(result(row, "not_applicable", reason="needs " + " and ".join(absent)))
            continue
        if not features and row["id"] in ("W1", "W5", "W2", "E4", "L1", "L2", "L3", "E1", "E2", "E3"):
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
    typed = any(r["id"] in TYPED and r["status"] in ("signal", "no_signal") for r in results)  # these read feature types
    if rank_rule or typed:
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
    if r["id"] == "L1" and r["condition_number"] is not None:
        return f"; condition number {r['condition_number']}"
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
    if r["id"] in ("L2", "E1"):
        lead = ("L2 linear: levels under {m} rows would become near-empty indicator columns: " if r["id"] == "L2"
                else "E1 tree: levels under {m} rows give splits little support: ").format(m=MIN_SUPPORT)
        return lead + "; ".join(f"{h['feature']} ({h['sparse_levels']} of {h['levels']} levels, {h['share_of_rows']} of rows)"
                                for h in r["features"]) + "."
    if r["id"] == "L1":
        parts = ([f"constant: {', '.join(r['constant'])}"] if r["constant"] else []) + \
                ([f"a linear combination of earlier features: {', '.join(r['dependent'])}"] if r["dependent"] else []) + \
                ([f"condition number {r['condition_number']}"] if r["condition_number"] is not None else []) + \
                ([f"variance inflation at or above {VIF_LIMIT:g}: " + ", ".join(f"{v['feature']} {v['vif']}" for v in r["high_vif"])]
                 if r["high_vif"] else [])
        return f"L1 linear: the standardized design of {len(r['design'])} numeric features is " + \
            ("rank deficient" if r["constant"] or r["dependent"] else "ill-conditioned") + "; " + "; ".join(parts) + "."
    if r["id"] == "L3":
        def sep(h):
            if h["kind"] == "level":
                return f"{h['feature']} ({h['levels']} levels whose rows all hold one class, {h['rows']} rows)"
            return f"{h['feature']} (class {h['class']} lies entirely {h['side']} the other classes, between {h['between'][0]} and {h['between'][1]})"
        return "L3 linear: features that separate the classes on their own, with no overlap: " + "; ".join(sep(h) for h in r["features"]) + "."
    if r["id"] == "E2":
        return "E2 tree: features a tree can memorise row by row: " + "; ".join(
            f"{h['feature']} ({h['rule']}" + (f", {h['distinct_share']}" if "distinct_share" in h else "") + ")" for h in r["features"]) + "."
    if r["id"] == "E3":
        def gap(h):
            if "gap" in h:
                return f"{h['feature']} (missing share differs by {h['gap']} between classes)"
            return f"{h['feature']} (target mean {h['target_mean_missing']} where missing, {h['target_mean_present']} where present)"
        return "E3 tree: missing cells that go with the target: " + "; ".join(gap(h) for h in r["features"]) + "."
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
