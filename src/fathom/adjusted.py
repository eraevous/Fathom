"""Conditional and partial association for selected target pairs (spec 034 slice 2a, A2 and A3).

FT-REL34-R3/R4/R5 (Kate, independent). Both analyses run only when the configuration declares
them (`relationships.condition_on`, `relationships.controls`) and only on the target pairs the
existing pair budget already selected, so nothing here widens the target screen or searches
subsets. Results are observations: "within levels of Z" or "with Z held linear", never an
adjustment for confounding.
"""

import math

from .relationships import measure
from .target import CATEGORY, NUMERIC, cell
from .univariate import coefficient

MAX_CONDITION, MIN_LEVELS, MAX_LEVELS, MIN_LEVEL_CASES, MAX_CONTROLS = 3, 2, 10, 30, 5
COLLINEAR = 1e-6  # unexplained share of a control (or pair column) below this counts as collinear
CONDITIONAL_ESTIMAND = ("the pair's measure computed separately within each level of the conditioning column "
                        "(complete cases of the pair and that column), shown beside the all-levels value")
PARTIAL_ESTIMAND = ("partial correlation: Pearson r of the residuals of both columns after a least-squares linear fit "
                    "on an intercept and the declared controls (complete cases of the pair and every control)")
UNCERTAINTY = ("Descriptive complete-case association inside declared groupings, not causation. A within-level or "
               "partial value shows how the association looks with the declared columns held fixed or linear; "
               "columns that were not declared are not held fixed, and a linear fit removes only linear structure.")


def validate(raw, columns, target):
    """Clean `condition_on` and `controls`; raise ValueError before any data is read."""
    out = {}
    for key, cap in (("condition_on", MAX_CONDITION), ("controls", MAX_CONTROLS)):
        if key not in raw:
            continue
        names = raw[key]
        if (not isinstance(names, list) or not 1 <= len(names) <= cap
                or any(not isinstance(c, str) or not c.strip() for c in names) or len(set(names)) != len(names)):
            raise ValueError(f"relationships.{key} must list 1 to {cap} distinct column names")
        if columns is not None and any(c not in columns for c in names):
            raise ValueError(f"relationships.{key} references an unknown column")
        if target is None:
            raise ValueError(f"relationships.{key} needs a declared target: it applies to the selected target pairs")
        if target in names:
            raise ValueError(f"relationships.{key} cannot include the target column")
        out[key] = list(names)
    return out


def _complete(rows, index, columns, names):
    """Parsed values for `names`, keeping only rows where every one parses."""
    kinds = [columns[index[n]]["effective_type"] for n in names]
    out = []
    for r in rows:
        vals = [cell(r[index[n]], k) for n, k in zip(names, kinds)]
        if all(v is not None for v in vals):
            out.append(vals)
    return out


def conditional(rows, columns, index, pair, z):
    left, right = pair
    a, b, kz = (columns[index[n]]["effective_type"] for n in (left, right, z))
    base = {"left": left, "right": right, "condition_on": z, "declared_as": "relationships.condition_on",
            "estimand": CONDITIONAL_ESTIMAND, **_basis({n: columns[index[n]] for n in (left, right, z)}, [left, right, z])}
    if z in pair:
        return {**base, "status": "skipped", "reason": "conditioning column is one of the pair"}
    if kz not in CATEGORY:
        return {**base, "status": "skipped", "reason": f"conditioning column type is {kz}; categorical or boolean needed"}
    cases = _complete(rows, index, columns, [left, right])
    triples = [(x, y, cell(r[index[z]], kz)) for r in rows
               if (x := cell(r[index[left]], a)) is not None and (y := cell(r[index[right]], b)) is not None]
    levels = sorted({t[2] for t in triples if t[2] is not None}, key=str)
    if not MIN_LEVELS <= len(levels) <= MAX_LEVELS:
        return {**base, "status": "skipped", "n": len(cases),
                "reason": f"conditioning column has {len(levels)} levels among complete cases; {MIN_LEVELS} to {MAX_LEVELS} needed"}
    marginal, why = measure(a, b, [tuple(c) for c in cases])
    within = []
    for level in levels:
        sub = [(x, y) for x, y, g in triples if g == level]
        if len(sub) < MIN_LEVEL_CASES:
            within.append({"level": level, "n": len(sub), "measures": None,
                           "reason": f"fewer than {MIN_LEVEL_CASES} complete cases: reported, not measured"})
            continue
        result, reason = measure(a, b, sub)
        within.append({"level": level, "n": len(sub), "measures": result, **({"reason": reason} if reason else {})})
    return {**base, "status": "computed", "n": len(cases), "excluded_rows": len(rows) - len(cases),
            "condition_missing": sum(t[2] is None for t in triples), "marginal": marginal,
            **({"marginal_reason": why} if why else {}), "levels": within}


def _residuals(values, basis):
    """Remove the projection of `values` onto an orthonormal basis (centered columns)."""
    out = list(values)
    for q in basis:
        dot = math.fsum(v * w for v, w in zip(out, q))
        out = [v - dot * w for v, w in zip(out, q)]
    return out


def _centered(values):
    """Center on the mean without losing small differences at a large offset (Codex on #80).

    Differences from a middle value are taken first (exact when values are close, by Sterbenz),
    then their own mean is removed, so the result has a zero sum up to rounding of the differences.
    """
    ref = sorted(values)[len(values) // 2]
    diffs = [v - ref for v in values]
    mean = math.fsum(diffs) / len(diffs)
    centered = [d - mean for d in diffs]
    scale = max(abs(v) for v in centered) or 1.0
    return [v / scale for v in centered]


def _basis(columns, names):
    """Type basis of the named columns (AGENTS: inferred is labelled, not hidden)."""
    inferred = [n for n in names if not columns[n].get("override")]
    return {"semantics": "inferred" if inferred else "human-declared", "inferred_columns": inferred}


def partial(rows, columns, index, pair, controls):
    left, right = pair
    base = {"left": left, "right": right, "controls": list(controls), "declared_as": "relationships.controls",
            "estimand": PARTIAL_ESTIMAND,
            **_basis({n: columns[index[n]] for n in (left, right, *controls)}, [left, right, *controls])}
    names = [left, right, *controls]
    if left in controls:
        return {**base, "status": "skipped", "reason": "a declared control is one of the pair"}
    kinds = {n: columns[index[n]]["effective_type"] for n in names}
    off = [n for n in names if kinds[n] not in NUMERIC]
    if off:
        return {**base, "status": "skipped", "reason": "not numeric: " + ", ".join(f"{n} ({kinds[n]})" for n in off)}
    cases = _complete(rows, index, columns, names)
    base.update(n=len(cases), excluded_rows=len(rows) - len(cases))
    if len(cases) < len(controls) + 3:
        return {**base, "status": "skipped", "reason": f"fewer than {len(controls) + 3} complete cases"}
    cols = [_centered([c[i] for c in cases]) for i in range(len(names))]
    basis = []
    for name, col in zip(controls, cols[2:]):
        size = math.fsum(v * v for v in col)
        res = _residuals(col, basis)
        rest = math.fsum(v * v for v in res)
        if size == 0 or rest <= COLLINEAR * size:
            return {**base, "status": "skipped",
                    "reason": f"controls are collinear: {name} is constant or a linear combination of the others"}
        norm = math.sqrt(rest)
        basis.append([v / norm for v in res])
    rx, ry = _residuals(cols[0], basis), _residuals(cols[1], basis)
    sxx, syy = math.fsum(v * v for v in rx), math.fsum(v * v for v in ry)
    sizes = [math.fsum(v * v for v in c) for c in cols[:2]]
    if min(sizes) == 0 or sxx <= COLLINEAR * sizes[0] or syy <= COLLINEAR * sizes[1]:
        return {**base, "status": "skipped", "reason": "a pair column is constant or fully explained by the controls"}
    value = max(-1.0, min(1.0, math.fsum(x * y for x, y in zip(rx, ry)) / math.sqrt(sxx * syy)))
    marginal, _ = measure(kinds[left], kinds[right], [(c[0], c[1]) for c in cases])
    return {**base, "status": "computed", "partial_r": coefficient(value),
            "marginal_pearson_r": (marginal or {}).get("pearson_r")}


def adjusted(rows, columns, block, selected, target):
    """A2 and A3 for each selected target pair; None when neither is declared."""
    if not block or not ({"condition_on", "controls"} & set(block)):
        return None
    index = {c["name"]: i for i, c in enumerate(columns)}
    pairs = [tuple(p) for p in selected if target in p and all(n in index for n in p)]
    pairs = [(l, r) if r == target else (r, l) for l, r in pairs]
    out = {"pairs_considered": [list(p) for p in pairs],
           "selection_route": "target pairs already selected by pair_budget; no other pairs are examined"}
    if "condition_on" in block:
        out["conditional"] = [conditional(rows, columns, index, p, z) for p in pairs for z in block["condition_on"]]
    if "controls" in block:
        out["partial"] = [partial(rows, columns, index, p, block["controls"]) for p in pairs]
    out["bounds"] = {"condition_on": MAX_CONDITION, "levels": [MIN_LEVELS, MAX_LEVELS],
                     "min_level_cases": MIN_LEVEL_CASES, "controls": MAX_CONTROLS}
    out["uncertainty"] = UNCERTAINTY
    return out


def _value(measures):
    from .presentation import formatted
    labels = {"pearson_r": "Pearson r", "spearman_rho": "Spearman rho", "eta": "eta",
              "cramers_v_corrected": "Cramer's V (bias-corrected)"}
    shown = [f"{labels.get(k, k)} {formatted(v)}" for k, v in sorted((measures or {}).items()) if v is not None]
    return ", ".join(shown) or "none"


def _inferred_note(item):
    cols = item.get("inferred_columns") or []
    if not cols:
        return ""
    return (f" Column types inferred, not declared, for {', '.join(cols)}; which columns were eligible and which "
            "measure was used rest on that inference, and declaring them here does not confirm their types.")


def conditional_message(item):
    head = f"{item['left']} and {item['right']} within levels of {item['condition_on']} (declared in relationships.condition_on)"
    if item["status"] != "computed":
        return f"{head}: not computed ({item['reason']})." + _inferred_note(item)
    shown = "; ".join(f"{lv['level']}: {_value(lv['measures'])} (n={lv['n']})" if lv["measures"] else
                      f"{lv['level']}: n={lv['n']}, {lv['reason']}" for lv in item["levels"])
    return (f"{head}: all levels {_value(item['marginal'])} (n={item['n']}); {shown}. "
            "Descriptive, not causal; other columns are not held fixed." + _inferred_note(item))


def partial_message(item):
    head = f"{item['left']} and {item['right']} with {', '.join(item['controls'])} held linear (declared in relationships.controls)"
    if item["status"] != "computed":
        return f"{head}: not computed ({item['reason']})." + _inferred_note(item)
    from .presentation import formatted
    return (f"{head}: partial r {formatted(item['partial_r'])} beside Pearson r {formatted(item['marginal_pearson_r'])} on the same "
            f"{item['n']} complete cases ({item['excluded_rows']} rows excluded). Descriptive, not causal; "
            "only linear structure in the declared controls is removed." + _inferred_note(item))
