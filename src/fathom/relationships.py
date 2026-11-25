"""Declared association matrix (spec 034 slice 1, A1; FT-REL34-R1..R3, R5).

Pairs are computed only inside column sets the configuration declares, so the number of
pairs is fixed before any data is read (Kate's dissent: "a capped output is not a bounded
analysis"). An undeclared table gets nothing from this module and no new artifact key.
"""

from collections import Counter
from itertools import combinations

from .target import CATEGORY, NUMERIC, cell, association
from .type_pairs import cramers_v_corrected, spearman
from .univariate import coefficient

MAX_SETS, MAX_COLUMNS, MAX_LEVELS, MIN_CASES = 3, 12, 20, 3
SAMPLING = "all rows; complete cases per pair (no sampling)"
MEASURES = {
    "numeric×numeric": "Pearson r and Spearman rho (monotone; average ranks for ties)",
    "category×numeric": "correlation ratio eta: the square root of the between-group share of numeric variance (eta squared is that share)",
    "category×category": "bias-corrected Cramer's V (Bergsma 2013)",
}
UNCERTAINTY = ("Descriptive complete-case association inside a declared column set, not causation. "
               "Values from different measures are not interchangeable. Several pairs were computed, "
               "so a few sizeable values can arise by chance; this matrix is for review, not selection.")


def validate(raw, columns=None, target=None):
    """Return the cleaned `relationships` block; raise ValueError on anything undeclared or over the bound."""
    if raw is None:
        return None
    if not isinstance(raw, dict) or not raw or set(raw) - {"sets", "condition_on", "controls"}:
        raise ValueError("relationships must be a mapping with keys: sets, condition_on, controls (at least one)")
    from .adjusted import validate as validate_adjusted
    extra = validate_adjusted(raw, columns, target)
    if "sets" not in raw:
        return extra
    sets = raw["sets"]
    if not isinstance(sets, list) or not 1 <= len(sets) <= MAX_SETS:
        raise ValueError(f"relationships.sets must be a list of 1 to {MAX_SETS} {{name, columns}} mappings")
    cleaned, names = [], set()
    for item in sets:
        if not isinstance(item, dict) or set(item) != {"name", "columns"}:
            raise ValueError("relationships.sets items must be {name, columns} mappings")
        name, cols = item["name"], item["columns"]
        if not isinstance(name, str) or not name.strip() or name in names:
            raise ValueError("relationships.sets names must be unique nonempty text")
        if (not isinstance(cols, list) or not 2 <= len(cols) <= MAX_COLUMNS
                or any(not isinstance(c, str) for c in cols) or len(set(cols)) != len(cols)):
            raise ValueError(f"relationships.sets.{name}.columns must list 2 to {MAX_COLUMNS} distinct column names")
        if columns is not None and any(c not in columns for c in cols):
            raise ValueError(f"relationships.sets.{name} references an unknown column")
        names.add(name)
        cleaned.append({"name": name, "columns": list(cols)})
    return {"sets": cleaned, **extra}


def skip_reason(column, values, raw):
    kind = column["effective_type"]
    present = [v for v in values if v is not None]
    if not any(v is not None for v in raw):
        return "all values missing"
    if not present:
        return f"no values usable as {kind} (cells present but none parse)"
    if kind not in NUMERIC | CATEGORY:
        return f"unsupported type: {kind}"
    if len(set(present)) < 2:
        return "constant column"
    if kind in CATEGORY and len(set(present)) > MAX_LEVELS:
        return f"more than {MAX_LEVELS} levels"
    if len(present) < MIN_CASES:
        return f"fewer than {MIN_CASES} non-missing values"
    return None


def measure(a, b, cases):
    """One pair's measures, or a named reason it has none (R2: undefined results are named)."""
    if len(cases) < MIN_CASES:
        return None, f"fewer than {MIN_CASES} complete cases"
    xs, ys = zip(*cases)
    if len(set(xs)) < 2 or len(set(ys)) < 2:
        return None, "constant within complete cases"
    if a in NUMERIC and b in NUMERIC:
        r = association(a, b, cases)
        rho = spearman(xs, ys)
        if r is None:
            return None, "Pearson r undefined"
        return {"pearson_r": r["value"], "spearman_rho": coefficient(rho) if rho is not None else None}, None
    if a in CATEGORY and b in CATEGORY:
        rows, cols = sorted(set(xs), key=str), sorted(set(ys), key=str)
        counts = Counter(cases)
        value = cramers_v_corrected([[counts[x, y] for y in cols] for x in rows])
        if value is None:
            return None, "bias-corrected Cramer's V not estimable"
        return {"cramers_v_corrected": coefficient(value)}, None
    eta = association(a, b, cases)
    if eta is None:
        return None, "correlation ratio eta undefined"
    return {"eta": eta["value"]}, None


def matrix(rows, columns, block):
    """Every pair inside each declared set, and nothing outside them."""
    if not block:
        return None
    index = {c["name"]: i for i, c in enumerate(columns)}
    out = []
    for item in block.get("sets", []):
        cols = item["columns"]
        values = {name: [cell(r[index[name]], columns[index[name]]["effective_type"]) for r in rows] for name in cols}
        skipped = [{"column": name, "reason": reason} for name in cols
                   if (reason := skip_reason(columns[index[name]], values[name], [r[index[name]] for r in rows]))]
        usable = [name for name in cols if name not in {s["column"] for s in skipped}]
        pairs = []
        for left, right in combinations(usable, 2):
            a, b = columns[index[left]]["effective_type"], columns[index[right]]["effective_type"]
            cases = [(x, y) for x, y in zip(values[left], values[right]) if x is not None and y is not None]
            kind = ("numeric×numeric" if a in NUMERIC and b in NUMERIC else
                    "category×category" if a in CATEGORY and b in CATEGORY else "category×numeric")
            result, reason = measure(a, b, cases)
            basis = "human-declared" if columns[index[left]].get("override") and columns[index[right]].get("override") else "inferred"
            pairs.append({"left": left, "right": right, "type_pair": kind, "semantics": basis, "n": len(cases),
                          "excluded_rows": len(rows) - len(cases), "measures": result,
                          **({"undefined": reason} if reason else {})})
        out.append({"name": item["name"], "columns": cols, "skipped": skipped,
                    "pairs_planned": len(cols) * (len(cols) - 1) // 2, "pairs_computed": len(pairs),
                    "pairs": pairs})
    return {"sets": out, "rows": len(rows), "sampling": SAMPLING, "measures": MEASURES,
            "threshold": "none: values are reported, not classified", "uncertainty": UNCERTAINTY,
            "bounds": {"sets": MAX_SETS, "columns_per_set": MAX_COLUMNS, "category_levels": MAX_LEVELS,
                       "min_cases": MIN_CASES}}


def message(item):
    """Observation wording (R5): no inferential, causal-claim or ranking language."""
    defined = [p for p in item["pairs"] if p["measures"]]
    text = (f"Declared relationship set {item['name']}: {item['pairs_computed']} pairs measured among "
            f"{len(item['columns']) - len(item['skipped'])} of {len(item['columns'])} declared columns; "
            f"{len(defined)} with a defined value.")
    inferred = sum(p["semantics"] == "inferred" for p in item["pairs"])
    if inferred:
        text += (f" {inferred} of {len(item['pairs'])} pairs use at least one inferred column type, so the measure chosen "
                 "for them rests on that inference; declaring a set does not confirm column types.")
    if item["skipped"]:
        text += " Skipped: " + "; ".join(f"{s['column']} ({s['reason']})" for s in item["skipped"]) + "."
    return text + " Descriptive, not causal."



# Slice 1b: the stored sets as report tables and a scalar CSV view (no new computation).
CSV_FIRST = ["set", "row_kind", "left", "right", "type_pair", "semantics", "n", "excluded_rows", "reason"]
LABELS = {"pearson_r": "Pearson r", "spearman_rho": "Spearman rho", "eta": "eta",
          "cramers_v_corrected": "Cramer's V (bias-corrected)"}


def measures_text(pair):
    """One cell naming each stored measure with its value, or the stored reason there is none."""
    from .presentation import formatted
    shown = [f"{LABELS.get(k, k)} {formatted(v)}" for k, v in sorted((pair["measures"] or {}).items()) if v is not None]
    return "; ".join(shown) or "undefined: " + pair.get("undefined", "no value")


def tables(d):
    """Report tables for each declared set: one row per measured pair, then any skipped columns."""
    out = []
    for item in (d.get("relationships") or {}).get("sets", []):
        out.append({"caption": (f"Declared set {item['name']}: {item['pairs_computed']} pairs measured "
                                f"({item['pairs_planned']} possible among {len(item['columns'])} declared columns); "
                                "complete cases per pair"),
                    "headers": ["Left", "Right", "Type pair", "Measures", "Complete n", "Excluded rows", "Type basis"],
                    "rows": [[p["left"], p["right"], p["type_pair"], measures_text(p), p["n"], p["excluded_rows"],
                              p["semantics"]] for p in item["pairs"]],
                    "numeric": [4, 5]})
        if item["skipped"]:
            out.append({"caption": f"Declared set {item['name']}: columns not measured",
                        "headers": ["Column", "Reason"],
                        "rows": [[s["column"], s["reason"]] for s in item["skipped"]], "numeric": []})
    return out


def notes(d):
    """Method lines shown under the tables: measures, sampling, threshold and uncertainty, as stored."""
    block = d.get("relationships") or {}
    if not block:
        return []
    return ([f"{kind}: {text}." for kind, text in sorted(block["measures"].items())]
            + [f"Sampling: {block['sampling']}.", f"Threshold: {block['threshold']}.", block["uncertainty"]])


def csv_rows(d):
    """Scalar rows for relationships.csv: one per pair, one per skipped column (row_kind says which).

    `reason` is the stored undefined reason for a pair, or the skip reason for a column.
    """
    rows = []
    for item in (d.get("relationships") or {}).get("sets", []):
        for p in item["pairs"]:
            rows.append({"set": item["name"], "row_kind": "pair", "left": p["left"], "right": p["right"],
                         "type_pair": p["type_pair"], "semantics": p["semantics"], "n": p["n"],
                         "excluded_rows": p["excluded_rows"], "reason": p.get("undefined"),
                         **{"measure." + k: v for k, v in sorted((p["measures"] or {}).items())}})
        for s in item["skipped"]:
            rows.append({"set": item["name"], "row_kind": "skipped_column", "left": s["column"], "reason": s["reason"]})
    return rows
