"""Measured evidence, labelled readings and conditional review suggestions."""

from collections import Counter
from dataclasses import asdict
from datetime import date
import math
import re
import statistics

from .config import validate_config
from .models import GuideDataFrame, ProfilingResult
from .quality import quality_profile, copy_evidence
from .parsing import finite_number, parse_date, temporal_failure, temporal_failure_message
from .univariate import enrich_columns, identity_and_samples, missingness_patterns, stored

SCHEMA_VERSION = 2
from .special import infer_special, enrich_special
from .rows import row_structure
from .timeseries import time_series


def number(value: str) -> float | None:
    return finite_number(value)


def iso_date(value: str) -> str | None:
    try:
        parsed = date.fromisoformat(value)
        return parsed.isoformat() if parsed.isoformat() == value else None
    except (TypeError, ValueError):
        return None


def rounded(n: float | None) -> float | None:
    return stored(n)


def infer(values: list[str], name="", meta=None) -> dict:
    meta=meta or {}
    special=infer_special(values,name)
    if special:
        typ,reason=special
        return {'type':typ,'confidence':'rule-based, uncalibrated','reasons':[reason],'alternatives':['identifier or category codes','another format or coordinate system; ask the owner']}
    distinct = set(values)
    if not values:
        typ, reason = "string", "No nonmissing values; type is unknown, string is the storage fallback."
    elif all(v.lower() in {"true", "false"} for v in values):
        typ, reason = "boolean", "All nonmissing values are lexical true/false."
    elif meta.get("date_format") or (sum(parse_date(v,meta.get("date_format")) is not None for v in values)>=len(values)*(.8 if re.search(r"date|release",name,re.I) else 1)):
        typ, reason = "temporal", "Local date formats recognized; ambiguous readings and format evidence are retained."
    elif (all(number(v) is not None for v in values) or (re.search(r"gross|amount|cost|price|revenue|rating|score|count|quantity",name,re.I) and sum(number(v) is not None for v in values)>=.8*len(values))) and not any(re.match(r"^[+-]?0\d", v.strip()) for v in values):
        typ, reason = "numeric", "Finite numeric readings (local currency/thousands syntax allowed); named numeric columns may retain up to 20% incompatible values, counted separately."
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


def summarize(values: list[str], typ: str, meta=None) -> dict:
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
        dates = [d["date"] for v in values if (d := parse_date(v,(meta or {}).get("date_format"))) is not None]
        stats={"valid": len(dates), "invalid": len(values) - len(dates),
               "min": min(dates) if dates else None, "max": max(dates) if dates else None}
        failure=temporal_failure(values,(meta or {}).get('date_format')) if not dates else None
        if failure:stats['parse_failure']=failure
        if (meta or {}).get('date_format')=='YEAR':stats['precision']='year; 1 January anchor, not an observed month/day'
        return stats
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
    if data.raw_rows is not None and (len(data.raw_rows)!=nrows or any(len(row)!=len(names) or any(not isinstance(v,str) for v in row) for row in data.raw_rows)):
        raise ValueError("raw_rows must align with frame and contain lexical strings")
    findings, columns = [], []
    provenance = {"source_sha256": data.source["sha256"], "rule_version": 1}

    def finding(fid, kind, message, evidence, uncertainty, generator="rule:profile-v1", **metadata):
        findings.append({"id": fid, "kind": kind, "message": message, "generator": generator,
                         "evidence": evidence, "uncertainty": uncertainty, "provenance": provenance, **metadata})

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
        meta = cfg["columns"].get(name, {})
        reading = infer(values,name,meta)
        typ = meta.get("type", reading["type"])
        stats = summarize(values, typ, meta)
        col = {"name": name, "observed_type": "CSV text" if values else "empty",
               "count": nrows, "missing": nrows - len(values), "distinct": len(counts),
               "examples": list(dict.fromkeys(values))[:3],
               "frequencies": [{"value": v, "count": c} for v, c in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))[:10]],
               "inference": reading, "override": {"type": typ, "generator": "human"} if "type" in meta else None,
               "effective_type": typ, "exclude_from_target":meta.get("exclude_from_target",False), "meaning": {"value": meta["meaning"], "generator": "human"} if "meaning" in meta else None,
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
            diagnostic(prefix + "-invalid", temporal_failure_message(name,stats['parse_failure'],include_advice=False) if stats.get('parse_failure') else f"{name}: {stats['invalid']} values do not match the effective {typ} type.",
                       [{"path": f"columns.{index}.statistics.invalid", "value": stats["invalid"]}]+([{"path":f"columns.{index}.statistics.parse_failure","value":stats['parse_failure']}] if stats.get('parse_failure') else []),
                       temporal_failure_message(name,stats['parse_failure']) if stats.get('parse_failure') else f"Review the type reading and incompatible values in {name}; do not coerce silently.")
        if col["meaning"] is None:
            finding(prefix + "-meaning", "question", f"What is the domain meaning of {name}?",
                    [{"path": f"columns.{index}.meaning", "value": None}], "The table cannot establish domain meaning.")
    for key, label in (("row_unit", "row unit"), ("generating_process", "generating process"),
                       ("missingness_mechanism", "missingness mechanism")):
        if cfg.get(key) is None:
            finding("unknown-" + key, "question", f"What is the {label}?",
                    [{"path": "working_record." + key, "value": None}],
                    "Unknown; requires information from the data owner or generating process.")
    dataset_summary, quality, quality_pairs = quality_profile(rows, columns, cfg, finding)
    structure = row_structure(rows, columns, cfg, finding)
    if structure["duplicate_rows"]["count"]:
        dup = next(f for f in findings if f["id"] == "duplicates")
        dup["message"] += " Repeating rows (1-based): " + ", ".join(map(str, structure["duplicate_rows"]["positions"])) + (f", first 10 of {duplicates}" if duplicates > 10 else "") + "."
        dup["evidence"].append({"path": "row_structure.duplicate_rows", "value": structure["duplicate_rows"]})
    temporal_structure = time_series(rows, columns, cfg, finding)
    enrich_columns(columns,rows,data.raw_rows if data.raw_rows is not None else rows,cfg,finding,findings)
    enrich_special(columns,rows,finding)
    dataset,samples=identity_and_samples(data,cfg,columns)
    selection, pairs, dependencies = select_pairs(rows, columns, cfg, quality, quality_pairs)
    from .target import build_target_analysis
    target_analysis=build_target_analysis(rows,columns,cfg,selection,pairs,finding)
    quality["coverage"]["reported_missingness_candidates"] = sum(p["method"] == "missingness_by_group" for p in pairs)
    for index, pair in enumerate(pairs):
        is_missingness = pair["method"] == "missingness_by_group"
        message = (f"Missingness in {pair['left']} varies across {pair['right']} groups by {pair['statistics']['spread']:.1%}."
                   if is_missingness else f"Selected relationship: {pair['left']} × {pair['right']} ({pair['semantics']}); {pair['association']['measure']}={pair['association']['value']}, complete n={pair['statistics']['n']}. Descriptive, not causal.")
        finding(f"pair-{index}", "observation", message,
                [{"path": f"bivariate.{index}.statistics", "value": pair["statistics"]}], pair["uncertainty"],
                "rule:quality-v1" if is_missingness else "rule:pairs-v1",
                rule="conditional_missingness" if is_missingness else "selected_relation", columns=[pair["left"],pair["right"]])
        if not is_missingness:
            finding(f"pair-{index}-review", "action", f"Review the meanings, measurement timing and possible leakage in {pair['left']} and {pair['right']} before using their association to make decisions.", [{"finding": f"pair-{index}"}],pair['uncertainty'],"rule:target-v1",rule="target_relationship_review",columns=[pair['left'],pair['right']])
        if is_missingness:
            finding(f"pair-{index}-review", "action", f"Investigate collection differences across {pair['right']} before choosing a missing-value treatment for {pair['left']}.",
                    [{"finding": f"pair-{index}"}], "A descriptive contrast does not establish the missingness mechanism.", "rule:quality-v1",
                    rule="conditional_missingness", columns=[pair["left"],pair["right"]])
    for f in findings:
        rule=f.get('rule')
        gate=quality.get('rules',{}).get(rule) or structure.get('rules',{}).get(rule)
        if rule=='univariate_skew':gate='absolute skew >=2 (tail asymmetry only); strong-skew verdict additionally requires n>=8 and displacement>=half IQR'
        if rule=='implausible_zero':gate='n>=5; 0<zero share<=20%; median positive>=100; >=80% of nonzero values>=100'
        if rule=='univariate_gap':gate='observed date gap >3 times median observed gap'
        if rule=='temporal_structure':gate=temporal_structure['rules']['signal']+'; '+temporal_structure['rules']['reliability']
        if gate and f['kind']=='observation':f['gate']=gate
    return ProfilingResult({"schema_version": SCHEMA_VERSION, "kind": "profile", "source": data.source,
        "schema": asdict(schema), "context": cfg["context"],
        "purpose": {"question": cfg.get("question"), "target": cfg.get("target"), "group_by":cfg.get("group_by"),
                    "mode": "declared" if cfg.get("question") or cfg.get("target") else "documentation_qa",
                    "fallback": "Reference, understanding, QA and validation; no general fitness verdict."},
        "working_record": {"generator": "human", **{k: cfg.get(k) for k in ("row_unit", "generating_process", "missingness_mechanism")},
                           "decisions": cfg["decisions"]},
        "overview": overview, "columns": columns, "findings": findings,
        "selection": selection, "bivariate": pairs, "dependencies": dependencies, "annotations": {},
        "dataset_summary": dataset_summary, "quality": quality, "dataset":dataset, "samples":samples,
        "target_analysis":target_analysis,"row_structure":structure,"time_series":temporal_structure,"missingness_patterns":missingness_patterns(columns,rows),
        "report":report_settings(cfg)})


def report_settings(cfg: dict) -> dict:
    """Human rendering choices (spec012). Omitted sections stay computed in this artifact."""
    from .config import OPTIONAL_SECTIONS
    from .univariate import bin_rule
    return {"generator": "human" if cfg.get("bins") or not all(cfg["sections"].values()) else "system default",
            "bins": cfg.get("bins"), "bin_rule": bin_rule(cfg.get("bins")),
            "omitted_sections": [{"key": k, "title": OPTIONAL_SECTIONS[k]} for k, on in cfg["sections"].items() if not on]}


def select_pairs(rows: list, columns: list, cfg: dict, quality=None, quality_pairs=None) -> tuple[dict, list, dict]:
    target, budget = cfg.get("target"), cfg["pair_budget"]
    selection = {"target": target, "budget": budget, "selected": [], "excluded": []}
    pairs, dependencies = [], {"scipy": "not requested"}
    blocked = (quality or {}).get("value_exclusions", {})
    if target is None:
        selection["excluded"] = [{"column": c["name"], "reason": "no target declared"} for c in columns]
        return rank_pairs(rows, columns, cfg, selection, quality_pairs or [], dependencies)
    from .target import target_candidates
    selection,pairs=target_candidates(rows,columns,cfg,quality or {})
    return rank_pairs(rows,columns,cfg,selection,pairs+(quality_pairs or []),dependencies)


def rank_pairs(rows, columns, cfg, selection, candidates, dependencies):
    """Use only core metrics to select; enrich only the chosen numeric pairs."""
    target, question = cfg.get("target"), (cfg.get("question") or "").casefold()
    vectors = {c["name"]: [row[i] for row in rows] for i,c in enumerate(columns)}
    for pair in candidates:
        names = (pair["left"], pair["right"])
        pair["focus"] = int(target in names if target else False) + int(any(
            re.search(r"(?<!\w)" + re.escape(name.casefold()) + r"(?!\w)", question) for name in names))
        if "association" in pair:
            pair["strength"] = pair["association"]["strength"]
        elif pair["method"] == "pearson":
            pair["strength"] = abs(pair["statistics"]["pearson_r"])
        elif pair["method"] == "grouped_numeric":
            means = [g["mean"] for g in pair["statistics"]["groups"] if g["mean"] is not None]
            nums = [x for v in vectors[pair["statistics"]["numeric_column"]] if (x:=number(v)) is not None]
            span = max(nums)-min(nums) if nums else 0
            pair["strength"] = rounded((max(means)-min(means))/span) if means and span and math.isfinite(span) else 0
    candidates.sort(key=lambda x: (-x["focus"], -x["strength"], -x["statistics"]["n"], x["left"], x["right"], x["method"]))
    selection["ranking_rule"] = "Declared target/literal question-column focus, then descriptive strength (absolute r, correlation ratio eta, Cramer V, or missing-rate spread), complete-case n, then lexical pair/method ties; grouping reservation disclosed separately; unlike scores are priority heuristics, not inferential comparisons."
    selection["selected"] = []
    selection["ranked"] = []
    chosen = []
    slots=set(range(min(len(candidates),cfg['pair_budget'])))
    byname={c['name']:c for c in columns}
    declared=cfg.get('group_by')
    if declared and byname[declared]['effective_type'] not in {'categorical','boolean'}:raise ValueError('group_by must be an effective category/boolean')
    grouping=[i for i,p in enumerate(candidates) if 'association' in p and byname[p['left']]['effective_type'] in {'categorical','boolean'} and (not declared or p['left']==declared)]
    reserved=None
    if target and byname[target]['effective_type'] in {'numeric','latitude','longitude'} and grouping and slots and (len(slots)>=2 or declared):
        reserved=grouping[0]
        if reserved not in slots:slots.remove(max(slots));slots.add(reserved)
    selection['grouping_policy']='Within-group summaries accompany budgeted category-bearing pairs; '+('one slot reserved for '+candidates[reserved]['left'] if reserved is not None else 'no extra grouping slot available/required')+'.'
    for rank, pair in enumerate(candidates, 1):
        selected = rank-1 in slots
        selection["ranked"].append({"rank": rank, "left": pair["left"], "right": pair["right"], "method": pair["method"],
                                    "focus": pair["focus"], "strength": pair["strength"], "n": pair["statistics"]["n"], "selected": selected, **({k:pair["association"][k] for k in ("measure","value")} if "association" in pair else {})})
        if not selected:
            selection["excluded"].append({"column": pair["left"], "other": pair["right"], "method": pair["method"], "reason": "pair budget exhausted"})
            continue
        if pair["method"] == "pearson":
            ix, iy = [next(i for i,c in enumerate(columns) if c["name"]==name) for name in (pair["left"],pair["right"])]
            cases = [(x,y) for row in rows if (x:=number(row[ix])) is not None and (y:=number(row[iy])) is not None]
            xs,ys = [x for x,_ in cases],[y for _,y in cases]
            try:
                from scipy.stats import pearsonr
            except ImportError:
                dependencies["scipy"] = "unavailable; p-values omitted"
            else:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", RuntimeWarning)
                    p = rounded(float(pearsonr(xs,ys).pvalue))
                pair["statistics"].update(p_value=p, p_value_status="available" if p is not None else "undefined")
                dependencies["scipy"] = "available"
        chosen.append(pair)
        selection["selected"].append([pair["left"],pair["right"]])
    return selection, chosen, dependencies


def compare(before: ProfilingResult, after: ProfilingResult) -> ProfilingResult:
    a, b = before.document, after.document
    if a["kind"] != "profile" or b["kind"] != "profile":
        raise ValueError("compare requires two profile artifacts")
    contexts = {"before": {"source": a["source"], "context": a["context"], "purpose": a["purpose"], "schema": a["schema"], "working_record": a["working_record"]},
                "after": {"source": b["source"], "context": b["context"], "purpose": b["purpose"], "schema": b["schema"], "working_record": b["working_record"]}}
    differences = {key: {"before": contexts["before"][key], "after": contexts["after"][key]}
                   for key in contexts["before"] if contexts["before"][key] != contexts["after"][key]}
    ac, bc = {c["name"]: c for c in a["columns"]}, {c["name"]: c for c in b["columns"]}
    return ProfilingResult({"schema_version": SCHEMA_VERSION, "kind": "comparison", "contexts": contexts,
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
