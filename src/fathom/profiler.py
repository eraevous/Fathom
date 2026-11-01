"""Measured evidence, labelled readings and conditional review suggestions."""

from collections import Counter
from dataclasses import asdict
from datetime import date
import math
import re
import statistics

from .config import validate_config
from .models import GuideDataFrame, ProfilingResult


def number(value: str) -> float | None:
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (TypeError, ValueError, OverflowError):
        return None


def iso_date(value: str) -> str | None:
    try:
        parsed = date.fromisoformat(value)
        return parsed.isoformat() if parsed.isoformat() == value else None
    except (TypeError, ValueError):
        return None


def rounded(n: float | None) -> float | None:
    return round(n, 10) if n is not None and math.isfinite(n) else None


def infer(values: list[str]) -> dict:
    distinct = set(values)
    if not values:
        typ, reason = "string", "No nonmissing values; type is unknown, string is the storage fallback."
    elif all(v.lower() in {"true", "false"} for v in values):
        typ, reason = "boolean", "All nonmissing values are lexical true/false."
    elif all(iso_date(v) is not None for v in values):
        typ, reason = "temporal", "All nonmissing values are strict ISO calendar dates."
    elif all(number(v) is not None for v in values) and not any(re.match(r"^[+-]?0\d", v.strip()) for v in values):
        typ, reason = "numeric", "All nonmissing values parse as finite numbers without leading-zero codes."
    elif len(distinct) <= 20 and len(distinct) < len(values) and len(distinct) / len(values) <= 0.8:
        typ, reason = "categorical", "At most 20 distinct strings, with repetition and distinct fraction <= 0.8."
    else:
        typ, reason = "string", "No conservative lexical rule established another reading."
    alternatives = {
        "numeric": ["categorical codes", "identifier", "quantity with unknown units"],
        "temporal": ["date-like code", "unknown timezone or collection timing"],
        "boolean": ["two category labels with unknown domain meaning"],
        "categorical": ["free text", "identifier", "unobserved category levels"],
        "string": ["identifier", "categorical", "unrecognized encoded measurement"],
    }
    return {"type": typ, "confidence": "rule-based, uncalibrated" if values else "unknown",
            "reasons": [reason], "alternatives": alternatives[typ]}


def summarize(values: list[str], typ: str) -> dict:
    if typ == "numeric":
        nums = [n for v in values if (n := number(v)) is not None]
        stats = {"valid": len(nums), "invalid": len(values) - len(nums),
                 "min": rounded(min(nums)) if nums else None,
                 "max": rounded(max(nums)) if nums else None,
                 "mean": rounded(statistics.mean(nums)) if nums else None,
                 "median": rounded(statistics.median(nums)) if nums else None,
                 "population_std": rounded(statistics.pstdev(nums)) if nums else None,
                 "zeros": sum(n == 0 for n in nums), "negatives": sum(n < 0 for n in nums)}
        return stats
    if typ == "temporal":
        dates = [d for v in values if (d := iso_date(v)) is not None]
        return {"valid": len(dates), "invalid": len(values) - len(dates),
                "min": min(dates) if dates else None, "max": max(dates) if dates else None}
    if typ == "boolean":
        return {"valid": sum(v.lower() in {"true", "false"} for v in values),
                "invalid": sum(v.lower() not in {"true", "false"} for v in values),
                "true": sum(v.lower() == "true" for v in values),
                "false": sum(v.lower() == "false" for v in values)}
    return {}


def profile(data: GuideDataFrame, config: dict | None = None) -> ProfilingResult:
    names = list(data.frame.columns)
    cfg = validate_config(config, names)
    schema = data.schema.resolve(names)
    rows = data.frame.values.tolist()
    if any(v is not None and not isinstance(v, str) for row in rows for v in row):
        raise ValueError("GuideDataFrame cells must be raw strings or None")
    nrows = len(rows)
    findings, columns = [], []
    provenance = {"source_sha256": data.source["sha256"], "rule_version": 1}

    def finding(fid, kind, message, evidence, uncertainty, generator="rule:profile-v1"):
        findings.append({"id": fid, "kind": kind, "message": message, "generator": generator,
                         "evidence": evidence, "uncertainty": uncertainty, "provenance": provenance})

    def diagnostic(fid, message, evidence, action):
        finding(fid, "observation", message, evidence, "Measured in the supplied snapshot only.")
        finding(fid + "-review", "action", action, [{"finding": fid}],
                "Review suggestion, not a defect verdict or permission to alter data.", "rule:review-v1")

    duplicates = nrows - len({tuple(row) for row in rows})
    overview = {"rows": nrows, "columns": len(names), "duplicate_rows": duplicates,
                "missing_cells": sum(v is None for row in rows for v in row)}
    finding("shape", "observation", f"The snapshot contains {nrows} rows and {len(names)} columns.",
            [{"path": "overview", "value": overview.copy()}], "Row unit is not inferred from shape.")
    if duplicates:
        diagnostic("duplicates", f"{duplicates} full rows repeat beyond their first occurrence.",
                   [{"path": "overview.duplicate_rows", "value": duplicates}],
                   "Review whether repeated rows are expected before removing any; confirm the row unit.")
    for index, name in enumerate(names):
        raw = [row[index] for row in rows]
        values = [v for v in raw if v is not None]
        counts = Counter(values)
        reading = infer(values)
        meta = cfg["columns"].get(name, {})
        typ = meta.get("type", reading["type"])
        stats = summarize(values, typ)
        col = {"name": name, "observed_type": "CSV text" if values else "empty",
               "count": nrows, "missing": nrows - len(values), "distinct": len(counts),
               "examples": list(dict.fromkeys(values))[:3],
               "frequencies": [{"value": v, "count": c} for v, c in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))[:10]],
               "inference": reading, "override": {"type": typ, "generator": "human"} if "type" in meta else None,
               "effective_type": typ, "meaning": {"value": meta["meaning"], "generator": "human"} if "meaning" in meta else None,
               "statistics": stats}
        columns.append(col)
        prefix = f"column-{index}"
        finding(prefix + "-type", "interpretation", f"{name}: inferred {reading['type']}; effective {typ}"
                + (" (human override)." if col["override"] else " (inferred, not a domain fact)."),
                [{"path": f"columns.{index}.inference", "value": reading}],
                "Lexical reading only; alternatives remain possible. Human type overrides are declarations.")
        if col["missing"]:
            diagnostic(prefix + "-missing", f"{name}: {col['missing']} of {nrows} cells are missing.",
                       [{"path": f"columns.{index}.missing", "value": col["missing"]}],
                       f"Inspect missing values in {name} and ask how absence was generated before choosing a treatment.")
        if stats.get("invalid", 0):
            diagnostic(prefix + "-invalid", f"{name}: {stats['invalid']} values do not match the declared {typ} type.",
                       [{"path": f"columns.{index}.statistics.invalid", "value": stats["invalid"]}],
                       f"Review the declared type and incompatible values in {name}; do not coerce silently.")
        if col["meaning"] is None:
            finding(prefix + "-meaning", "question", f"What is the domain meaning of {name}?",
                    [{"path": f"columns.{index}.meaning", "value": None}], "The table cannot establish domain meaning.")
    for key, label in (("row_unit", "row unit"), ("generating_process", "generating process"),
                       ("missingness_mechanism", "missingness mechanism")):
        if cfg.get(key) is None:
            finding("unknown-" + key, "question", f"What is the {label}?",
                    [{"path": "working_record." + key, "value": None}],
                    "Unknown; requires information from the data owner or generating process.")
    selection, pairs, dependencies = select_pairs(rows, columns, cfg)
    for index, pair in enumerate(pairs):
        finding(f"pair-{index}", "observation", f"Selected relationship: {pair['left']} × {pair['right']} ({pair['semantics']}).",
                [{"path": f"bivariate.{index}.statistics", "value": pair["statistics"]}], pair["uncertainty"], "rule:pairs-v1")
    return ProfilingResult({"schema_version": 1, "kind": "profile", "source": data.source,
        "schema": asdict(schema), "context": cfg["context"],
        "purpose": {"question": cfg.get("question"), "target": cfg.get("target"),
                    "mode": "declared" if cfg.get("question") or cfg.get("target") else "documentation_qa",
                    "fallback": "Reference, understanding, QA and validation; no general fitness verdict."},
        "working_record": {"generator": "human", **{k: cfg.get(k) for k in ("row_unit", "generating_process", "missingness_mechanism")},
                           "decisions": cfg["decisions"]},
        "overview": overview, "columns": columns, "findings": findings,
        "selection": selection, "bivariate": pairs, "dependencies": dependencies, "annotations": {}})


def select_pairs(rows: list, columns: list, cfg: dict) -> tuple[dict, list, dict]:
    target, budget = cfg.get("target"), cfg["pair_budget"]
    selection = {"target": target, "budget": budget, "selected": [], "excluded": []}
    pairs, dependencies = [], {"scipy": "not requested"}
    if target is None:
        selection["excluded"] = [{"column": c["name"], "reason": "no target declared"} for c in columns]
        return selection, pairs, dependencies
    target_index = next(i for i, c in enumerate(columns) if c["name"] == target)
    tcol = columns[target_index]
    for index, col in enumerate(columns):
        reason, stats, method = None, None, None
        a, b = col["effective_type"], tcol["effective_type"]
        if index == target_index:
            reason = "target column"
        elif len(pairs) >= budget:
            reason = "pair budget exhausted"
        elif a == b == "numeric":
            cases = [(x, y) for row in rows if (x := number(row[index])) is not None
                     and (y := number(row[target_index])) is not None]
            xs, ys = [x for x, _ in cases], [y for _, y in cases]
            if len(cases) < 2:
                reason = "fewer than two complete finite cases"
            elif len(set(xs)) < 2 or len(set(ys)) < 2:
                reason = "constant numeric input"
            else:
                try:
                    r = rounded(statistics.correlation(xs, ys))
                except (ArithmeticError, statistics.StatisticsError):
                    r = None
                if r is None:
                    reason = "undefined numeric association"
                else:
                    method = "pearson"
                    stats = {"n": len(cases), "pearson_r": r, "p_value": None, "p_value_status": "unavailable"}
                    try:
                        from scipy.stats import pearsonr
                    except ImportError:
                        dependencies["scipy"] = "unavailable; p-values omitted"
                    else:
                        import warnings
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore", RuntimeWarning)
                            p = rounded(float(pearsonr(xs, ys).pvalue))
                        stats.update(p_value=p, p_value_status="available" if p is not None else "undefined")
                        dependencies["scipy"] = "available"
        elif (a in {"categorical", "boolean"} and b == "numeric") or (a == "numeric" and b in {"categorical", "boolean"}):
            gi, ni = (index, target_index) if a != "numeric" else (target_index, index)
            group_type = columns[gi]["effective_type"]
            groups = {}
            for row in rows:
                group, value = row[gi], number(row[ni])
                if group is None or value is None:
                    continue
                if group_type == "boolean":
                    group = group.lower()
                    if group not in {"true", "false"}:
                        continue
                groups.setdefault(group, []).append(value)
            if not groups:
                reason = "no complete cases"
            elif len(groups) > 20:
                reason = "more than twenty groups; summary omitted"
            else:
                method = "grouped_numeric"
                stats = {"n": sum(map(len, groups.values())), "group_column": columns[gi]["name"],
                         "numeric_column": columns[ni]["name"],
                         "groups": [{"value": g, "n": len(v), "mean": rounded(statistics.mean(v))}
                                    for g, v in sorted(groups.items())]}
        else:
            reason = f"unsupported type pair: {a} × {b}"
        if reason:
            selection["excluded"].append({"column": col["name"], "reason": reason})
        else:
            selection["selected"].append([col["name"], target])
            pairs.append({"left": col["name"], "right": target, "method": method, "statistics": stats,
                          "generator": "rule:pairs-v1", "semantics": "human-declared" if col["override"] and tcol["override"] else "inferred",
                          "uncertainty": "Descriptive complete-case association, not causation. Readings may be inferred. Pearson p-values assume independent paired observations and a suitable null model; the table cannot establish these assumptions."})
    return selection, pairs, dependencies


def compare(before: ProfilingResult, after: ProfilingResult) -> ProfilingResult:
    a, b = before.document, after.document
    if a["kind"] != "profile" or b["kind"] != "profile":
        raise ValueError("compare requires two profile artifacts")
    contexts = {"before": {"source": a["source"], "context": a["context"], "purpose": a["purpose"], "schema": a["schema"], "working_record": a["working_record"]},
                "after": {"source": b["source"], "context": b["context"], "purpose": b["purpose"], "schema": b["schema"], "working_record": b["working_record"]}}
    differences = {key: {"before": contexts["before"][key], "after": contexts["after"][key]}
                   for key in contexts["before"] if contexts["before"][key] != contexts["after"][key]}
    ac, bc = {c["name"]: c for c in a["columns"]}, {c["name"]: c for c in b["columns"]}
    return ProfilingResult({"schema_version": 1, "kind": "comparison", "contexts": contexts,
        "context_differences": differences,
        "deltas": {**{key: b["overview"][key] - a["overview"][key] for key in ("rows", "columns", "missing_cells", "duplicate_rows")},
                   "columns_added": [name for name in bc if name not in ac],
                   "columns_removed": [name for name in ac if name not in bc],
                   "shared_columns": [{"name": name, "missing": bc[name]["missing"] - c["missing"],
                                       "distinct": bc[name]["distinct"] - c["distinct"],
                                       "effective_type": {"before": c["effective_type"], "after": bc[name]["effective_type"]},
                                       "semantics_changed": any(c[k] != bc[name][k] for k in ("inference", "override", "meaning"))}
                                      for name, c in ac.items() if name in bc]},
        "limitations": ["Aggregate comparison only; row-level lineage is unknown.",
                        "Context and transformations are human declarations, not verified causes of deltas.",
                        "Type or meaning changes can make summaries incomparable; inspect shared-column semantics."],
        "annotations": {}})
