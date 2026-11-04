"""Transparent, bounded quality diagnostics inside the profiler's data flow."""

from collections import Counter, defaultdict
from datetime import date
import math
import re
import statistics


def stored(n):
    from .univariate import stored as rule
    return rule(n)


def finite(value):
    from .parsing import finite_number
    return finite_number(value)


def calendar_date(value):
    try:
        d = date.fromisoformat(value)
        return d.isoformat() if d.isoformat() == value else None
    except (TypeError, ValueError):
        return None


def share(count, total):
    return count / total if total else None


def copy_evidence(left, right):
    """Shared absence alone is not evidence of duplicated observed values."""
    joint=[(a,b) for a,b in zip(left,right) if a is not None and b is not None]
    agreement=share(sum(a==b for a,b in zip(left,right)),len(left))
    joint_agreement=share(sum(a==b for a,b in joint),len(joint))
    near=bool(joint and joint_agreement>=.95 and agreement is not None and
              (agreement==1 or (len(left)>=5 and len(joint)>=5 and agreement>=.95)))
    return {"agreement":agreement,"jointly_present":len(joint),"joint_agreement":joint_agreement,"near":near}


MISSINGNESS_TEST = {"family_alpha": .01, "correction": "Bonferroni", "min_cramers_v": .15, "min_group_size": 10,
                    "max_groups": 20, "expected_count_rule": "Cochran: no expected cell below 1 and at most 20% of cells below 5"}


def chi_square_sf(x, df):
    """Upper tail of the chi-square distribution: regularized gamma Q(df/2, x/2), standard library only."""
    if x <= 0:
        return 1.0
    a, z = df / 2, x / 2
    log_front = -z + a * math.log(z) - math.lgamma(a)
    if z < a + 1:
        term = total = 1 / a; k = a
        for _ in range(10000):
            k += 1; term *= z / k; total += term
            if abs(term) < abs(total) * 1e-16:
                break
        return max(0.0, 1 - total * math.exp(log_front))
    tiny = 1e-300; b = z + 1 - a; c = 1 / tiny; d = 1 / b; h = d
    for i in range(1, 10000):
        an = -i * (i - a); b += 2
        d = an * d + b; d = tiny if abs(d) < tiny else d
        c = b + an / c; c = tiny if abs(c) < tiny else c
        d = 1 / d; delta = d * c; h *= delta
        if abs(delta - 1) < 1e-16:
            break
    return h * math.exp(log_front)


def missingness_table_test(groups):
    """Chi-square test of a missing/present x group table, or the reason it was not run."""
    rule = MISSINGNESS_TEST
    if not 2 <= len(groups) <= rule["max_groups"]:
        return {"skipped": "group count outside 2..20"}
    if min(g["n"] for g in groups) < rule["min_group_size"]:
        return {"skipped": "group below minimum size"}
    n = sum(g["n"] for g in groups); missing = sum(g["missing"] for g in groups)
    if missing in (0, n):
        return {"skipped": "no missing/present contrast within grouped rows"}
    cells = [(observed, g["n"] * total / n) for g in groups
             for observed, total in ((g["missing"], missing), (g["n"] - g["missing"], n - missing))]
    if min(e for _, e in cells) < 1 or sum(e < 5 for _, e in cells) > .2 * len(cells):
        return {"skipped": "expected counts too small"}
    chi = sum((o - e) ** 2 / e for o, e in cells)
    return {"n": n, "chi_square": chi, "df": len(groups) - 1, "p_value": chi_square_sf(chi, len(groups) - 1),
            "cramers_v": math.sqrt(chi / n)}


def scan_missingness(tables):
    """Bonferroni over the tests actually run; report only p below alpha/m and V at or above the floor."""
    rule = MISSINGNESS_TEST; evaluated, skipped = [], Counter()
    for table in tables:
        result = missingness_table_test(table["groups"])
        if "skipped" in result:
            skipped[result["skipped"]] += 1
        else:
            evaluated.append({**table, **result})
    m = len(evaluated); threshold = rule["family_alpha"] / m if m else None
    reported = sorted((e for e in evaluated if e["p_value"] < threshold and e["cramers_v"] >= rule["min_cramers_v"]),
                      key=lambda e: (e["p_value"], -e["cramers_v"], e["column"], e["group_column"]))
    results = [{"column": e["column"], "group_column": e["group_column"], "grouping": e["grouping"], "n": e["n"],
                "groups": [{**g, "rate": stored(g["missing"] / g["n"])} for g in e["groups"]],
                "chi_square": stored(e["chi_square"]), "df": e["df"], "p_value": stored(e["p_value"]),
                "bonferroni_p": stored(min(1.0, e["p_value"] * m)), "cramers_v": stored(e["cramers_v"])} for e in reported[:20]]
    block = {"method": "Pearson chi-square test of independence between a column's missing indicator and a screened grouping column",
             **rule, "tests": m, "per_test_alpha": stored(threshold), "skipped": dict(sorted(skipped.items())),
             "unadjusted_below_0_05": sum(e["p_value"] < .05 for e in evaluated), "reported": len(reported),
             "results": results, "omitted_results": max(0, len(reported) - 20),
             "role": "Observation only: never selects pairs, charts or actions; thresholds are disclosed, not a missingness mechanism."}
    return block, evaluated


def quality_profile(rows, columns, cfg, emit):
    """Return additive summary, screening evidence and quality pair candidates."""
    n, p = len(rows), len(columns)
    vectors = {c["name"]: [r[i] for r in rows] for i, c in enumerate(columns)}
    by_name = {c["name"]: c for c in columns}
    constants, dominant, blocked, groups, missing_candidates = [], [], {}, {}, []
    rules = {
        "sentinel": "n>=5; share<=0.2; -1 at minimum otherwise nonnegative, or 999/9999/99999 at maximum >=5x other median absolute magnitude (floor 1)",
        "dummy": "whole lexical test/dummy/sample label with optional numeric suffix",
        "placeholder": "literal na/null/none/unknown/n/a/n-a/tbd/?; possible codes, not null conversion",
        "dominant": "n>=5 nonmissing and top share>=0.95; constant n>=2 and distinct=1",
        "constant": "n>=2 nonmissing and exactly one distinct observed value; all-missing is not constant",
        "redundancy": "exact vectors; affine normalized numeric fingerprints to 1e-8; repeated-category partition recoding; near-copy row AND jointly-present agreement>=0.95 with n>=5 and >=5 jointly-present cells",
        "co_missing": "identical nonempty missing-row masks",
        "conditional_missingness": "2..20 groups, each n>=3, missing-rate spread>=0.30; first 20 grouping columns, target first then lexical",
        "missingness_varies_with": "Pearson chi-square, missing indicator x group; 2..20 groups, each n>=10, Cochran expected counts; Bonferroni over tests run, family alpha 0.01; Cramer V>=0.15; observation only, never an action",
        "temporal_gap": ">=4 dates; modal positive day interval occurs>=2 and >=half intervals; gap>1.5x cadence",
        "skew": "n>=8; absolute standardized third moment>=2 and mean/median displacement>=half IQR (relative fallback for zero IQR)",
    }

    def observation(fid, rule, names, message, value):
        emit(fid, "observation", message, [{"path": "quality." + rule, "value": value}],
             "Measured on this snapshot under a heuristic; not proof of an error or a domain cause.",
             "rule:quality-v1", rule=rule, columns=names)

    def diagnostic(fid, rule, names, message, value, action, hypothesis=None):
        observation(fid, rule, names, message, {**value, "rule": rules.get(rule, rule)})
        if hypothesis:
            emit(fid + "-hypothesis", "hypothesis", hypothesis, [{"finding": fid}],
                 "Possible explanation only; confirm with the data owner.", "rule:quality-v1", rule=rule, columns=names)
        emit(fid + "-review", "action", action, [{"finding": fid}],
             "Conditional review, not automatic cleaning or a confirmed defect.", "rule:quality-v1", rule=rule, columns=names)

    for index, col in enumerate(columns):
        name, typ = col["name"], col["effective_type"]
        raw = vectors[name]; values = [v for v in raw if v is not None]
        counts = Counter(values); prefix = f"q-{index}"
        if counts:
            top, count = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[0]
            if len(counts) == 1 and len(values) >= 2:
                constants.append(name); blocked[name] = "constant column"
                diagnostic(prefix + "-constant", "constant", [name], f"{name} has one observed value across {len(values)} nonmissing cells.",
                           {"value": top, "count": count, "share": 1}, f"Confirm whether {name} is intentionally constant before using it to distinguish rows.")
            elif len(values) >= 5 and count / len(values) >= .95:
                dominant.append(name); blocked[name] = "near-constant column (dominant share >=95%)"
                diagnostic(prefix + "-dominant", "dominant", [name], f"{name} equals {top!r} in {count}/{len(values)} nonmissing cells ({count/len(values):.1%}).",
                           {"value": top, "count": count, "share": count/len(values)}, f"Review the rare alternatives in {name} before treating the column as informative.")
        for rule, matched in (
            ("dummy", [v for v in values if re.fullmatch(r"(?:test|dummy|sample)(?:[ _-]?\d+)?", v.strip().casefold())]),
            ("placeholder", [v for v in values if v.strip().casefold() in {"na", "null", "none", "unknown", "n/a", "n-a", "tbd", "?"}]),
        ):
            if matched:
                diagnostic(prefix + "-" + rule, rule, [name], f"{name} contains {len(matched)}/{len(values)} nonmissing cells with {rule}-like labels ({len(matched)/len(values):.1%}).",
                           {"count": len(matched), "share": len(matched)/len(values), "values": sorted(set(matched))[:10]},
                           f"Ask whether the {rule}-like labels in {name} should be retained, recoded or excluded.",
                           f"The flagged labels in {name} may mark test records or unknown values rather than genuine domain categories.")
        nums = [x for v in values if (x := finite(v)) is not None] if typ == "numeric" else []
        if len(nums) >= 5:
            for candidate in (-1, 999, 9999, 99999):
                count = nums.count(candidate); others = [x for x in nums if x != candidate]
                if not count or not others or count / len(nums) > .2:
                    continue
                extreme = (candidate == -1 and min(nums) == -1 and min(others) >= 0) or (
                    candidate != -1 and max(nums) == candidate and candidate >= 5 * max(1, statistics.median(abs(x) for x in others)))
                if extreme:
                    diagnostic(prefix + f"-sentinel-{candidate}", "sentinel", [name], f"{name} equals {candidate} in {count}/{len(nums)} finite cells ({count/len(nums):.1%}) at the column extreme.",
                               {"value": candidate, "count": count, "share": count/len(nums), "finite_count": len(nums)},
                               f"Confirm the meaning of {candidate} in {name} before using it in summaries or recoding it.",
                               f"The extreme value {candidate} in {name} may be a sentinel or placeholder rather than a measured quantity.")
        if len(nums) >= 8 and max(nums) != min(nums):
            scale = max(abs(x) for x in nums) or 1
            unit = [x / scale for x in nums]; mu, med, sd = statistics.mean(unit), statistics.median(unit), statistics.pstdev(unit)
            quartiles = statistics.quantiles(unit, n=4, method="inclusive")
            iqr = quartiles[2] - quartiles[0]
            skew = statistics.mean(((x-mu)/sd)**3 for x in unit) if sd else 0
            displacement = abs(mu-med)
            if abs(skew) >= 2 and displacement >= .5 * (iqr or max(abs(med), 1e-12)):
                diagnostic(prefix + "-skew", "skew", [name], f"{name} is strongly skewed: mean {statistics.mean(nums):.6g} differs from median {statistics.median(nums):.6g}, so the mean may not describe a typical row.",
                           {"finite_count": len(nums), "standardized_third_moment": stored(skew), "mean": statistics.mean(nums), "median": statistics.median(nums)},
                           f"Inspect the tail of {name} and report median alongside mean before choosing a typical-value summary.")
        if typ == "temporal":
            dates = sorted({date.fromisoformat(v) for v in values if calendar_date(v) is not None})
            if len(dates) >= 4:
                deltas = [(b-a).days for a,b in zip(dates, dates[1:])]
                cadence, count = sorted(Counter(deltas).items(), key=lambda x: (-x[1], x[0]))[0]
                if count >= 2 and count/len(deltas) >= .5:
                    gaps = [{"after": a.isoformat(), "before": b.isoformat(), "days": (b-a).days,
                             "unrecorded_cadence_positions": max(0, (b-a).days//cadence-1)}
                            for a,b in zip(dates, dates[1:]) if (b-a).days > 1.5*cadence]
                    if gaps:
                        diagnostic(prefix + "-temporal", "temporal_gap", [name], f"{name} has {len(gaps)} coverage gap(s) relative to an inferred {cadence}-day cadence.",
                                   {"cadence_days": cadence, "cadence_support": count, "intervals": len(deltas), "gaps": gaps[:20], "omitted_gaps": max(0,len(gaps)-20)},
                                   f"Confirm the collection schedule for {name} before treating unrecorded dates as missing observations.",
                                   f"The gaps in {name} may reflect a collection schedule, an outage or deliberate filtering.")

    # Fingerprint groups describe structural patterns, not Cartesian association matrices.
    exact, affine, partition, masks = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)
    for col in columns:
        name = col["name"]; raw = vectors[name]
        if n:
            exact[tuple(raw)].append(name)
        mask = tuple(i for i,v in enumerate(raw) if v is None)
        if mask:
            masks[mask].append(name)
        nums = [finite(v) for v in raw] if col["effective_type"] == "numeric" else []
        valid = [v for v in nums if v is not None]
        if len(valid) >= 5 and len(set(valid)) >= 3:
            scale = max(abs(x) for x in valid) or 1
            unit = [x/scale for x in valid]; base = unit[0]
            step = next((x-base for x in unit if x != base), None)
            if step and all(math.isfinite((x-base)/step) for x in unit):
                signature = tuple(None if x is None else round((x/scale-base)/step, 8) for x in nums)
                affine[signature].append(name)
        present = [v for v in raw if v is not None]; counts = Counter(present)
        if len(present) >= 5 and 2 <= len(counts) <= 20 and min(counts.values()) >= 2:
            encoding = {}
            sig = []
            for v in raw:
                if v is None:
                    sig.append(None)
                else:
                    if v not in encoding: encoding[v] = len(encoding)
                    sig.append(encoding[v])
            partition[tuple(sig)].append(name)
    duplicate_groups = [sorted(g) for g in exact.values() if len(g)>1]
    lockstep_groups = []
    for family in (affine, partition):
        for group in family.values():
            group = sorted(group)
            if len(group)>1 and len({tuple(vectors[x]) for x in group})>1 and group not in lockstep_groups:
                lockstep_groups.append(group)
    duplicate_groups.sort(); lockstep_groups.sort()
    for group in duplicate_groups:
        for name in group[1:]:
            blocked.setdefault(name, f"near-duplicate of {group[0]} (exact duplicate vector)")
    for rule, found in (("duplicate_columns", duplicate_groups), ("lockstep_columns", lockstep_groups)):
        for i, group in enumerate(found):
            diagnostic(f"q-{rule}-{i}", rule, group, f"Columns {', '.join(group)} follow an {'exactly duplicated' if rule=='duplicate_columns' else 'observed lockstep'} pattern.",
                       {"columns": group, "rows": n, "kind": "lexical equality" if rule=="duplicate_columns" else "affine numeric or repeated-category partition fingerprint", "tolerance": 1e-8 if rule=="lockstep_columns" else 0},
                       f"Check whether {', '.join(group)} carry independent information before using them together.")
    names = sorted(vectors)
    comparisons, omitted = 0, 0
    for i, name in enumerate(names):
        for other in names[:i]:
            if n < 5 or name in blocked or other in blocked:
                continue
            if comparisons >= 2000:
                omitted += 1; continue
            comparisons += 1
            evidence = copy_evidence(vectors[name],vectors[other])
            agreement = evidence["agreement"]
            if evidence["near"]:
                blocked[name] = f"near-duplicate of {other} (row agreement {agreement:.1%})"
                if agreement < 1:
                    diagnostic(f"q-near-{i}-{names.index(other)}", "near_duplicate_columns", [other,name], f"{name} agrees with {other} on {agreement:.1%} of rows.",
                               {**evidence, "rows": n}, f"Review the few differences between {name} and {other} before keeping both.")
                break
    for i, (mask, group) in enumerate(sorted(masks.items())):
        if len(group)>1:
            diagnostic(f"q-co-missing-{i}", "co_missing", sorted(group), f"Columns {', '.join(sorted(group))} are missing together on the same {len(mask)}/{n} rows ({len(mask)/n:.1%}).",
                       {"columns": sorted(group), "missing_rows": len(mask), "share": len(mask)/n, "data_row_positions_1_based": [x+1 for x in mask[:10]]},
                       "Ask whether a shared collection or processing step explains the co-missing columns.",
                       "Shared missing rows may reflect a common collection or processing step, but the cause is unknown.")

    target = cfg.get("target")
    grouping_names = sorted(names, key=lambda x: (x!=target, x))[:20]
    test_tables = []
    for missing_name in names:
        raw = vectors[missing_name]
        if not 0 < sum(x is None for x in raw) < n:
            continue
        for group_name in grouping_names:
            if group_name == missing_name or group_name in blocked:
                continue
            gcol, graw = by_name[group_name], vectors[group_name]
            if gcol["effective_type"] == "numeric":
                nums = [x for v in graw if (x:=finite(v)) is not None]
                if not nums: continue
                median = statistics.median(nums)
                labels = [None if (x:=finite(v)) is None else (f"<= median ({median:.6g})" if x<=median else f"> median ({median:.6g})") for v in graw]
                basis = {"grouping": "numeric median split (descriptive)", "median": median}
            elif gcol["effective_type"] in {"categorical", "boolean", "string"}:
                labels = [v.lower() if v is not None and gcol["effective_type"]=="boolean" else v for v in graw]
                basis = {"grouping": "observed labels"}
            else:
                continue
            sizes, missing = Counter(), Counter()
            for v, label in zip(raw, labels):
                if label is not None:
                    sizes[label] += 1; missing[label] += v is None
            if not 2<=len(sizes)<=20:
                continue
            gs = [{"value": k, "n": sizes[k], "missing": missing[k], "rate": missing[k]/sizes[k]} for k in sorted(sizes)]
            test_tables.append({"column": missing_name, "group_column": group_name, "grouping": basis["grouping"],
                                "groups": [{k: g[k] for k in ("value", "n", "missing")} for g in gs]})
            if min(sizes.values())<3:
                continue
            spread = max(g["rate"] for g in gs)-min(g["rate"] for g in gs)
            if spread >= .3:
                missing_candidates.append({"left": missing_name, "right": group_name, "method": "missingness_by_group",
                    "statistics": {"n": sum(sizes.values()), "groups": gs, "spread": stored(spread), **basis},
                    "strength": stored(spread), "generator": "rule:quality-v1", "semantics": "inferred" if not gcol["override"] else "human-declared",
                    "uncertainty": "Observed missing-rate contrast, not a missingness mechanism or causation; grouping can be inferred."})

    missingness_tests, _ = scan_missingness(test_tables)
    for i, result in enumerate(missingness_tests["results"]):
        rates = [g["rate"] for g in result["groups"]]
        emit(f"q-missing-test-{i}", "observation",
             f"Missingness in {result['column']} varies with {result['group_column']}: missing share {min(rates):.1%} to {max(rates):.1%} across "
             f"{len(rates)} groups (n={result['n']}; Cramér's V {result['cramers_v']:.2f}; chi-square p={result['p_value']:.2g}, below the "
             f"Bonferroni threshold {missingness_tests['per_test_alpha']:.2g} for {missingness_tests['tests']} tests).",
             [{"path": f"quality.missingness_tests.results.{i}", "value": result}],
             "Association between missingness and groups in this snapshot under disclosed thresholds; not a missingness mechanism, "
             "cause or defect, and it selects no action.", "rule:missingness-test-v1",
             rule="missingness_varies_with", columns=[result["column"], result["group_column"]])

    summary = {"rows": n, "columns": p, "complete_rows": {"count": sum(all(x is not None for x in r) for r in rows), "share": share(sum(all(x is not None for x in r) for r in rows),n)},
        "complete_columns": {"count": sum(c["missing"]==0 for c in columns), "share": share(sum(c["missing"]==0 for c in columns),p)},
        "missing_cells": {"count": sum(c["missing"] for c in columns), "share": share(sum(c["missing"] for c in columns),n*p)},
        "duplicate_rows": n-len({tuple(r) for r in rows}), "duplicate_columns": sum(len(g)-1 for g in duplicate_groups),
        "lockstep_columns": len({name for g in lockstep_groups for name in g[1:]}), "duplicate_groups": duplicate_groups, "lockstep_groups": lockstep_groups,
        "inferred_types": dict(sorted(Counter(c["inference"]["type"] for c in columns).items())),
        "constant_columns": constants, "near_constant_columns": dominant}
    summary["finding_links"] = {}
    for key in list(summary):
        if key=="finding_links": continue
        fid = "summary-" + key.replace("_","-")
        value = summary[key]
        if key in {"complete_rows", "complete_columns", "missing_cells"}:
            rate = value["share"]
            description = f"{value['count']} ({rate:.1%})" if rate is not None else f"{value['count']} (share unavailable)"
        elif isinstance(value, dict):
            description = ', '.join(f'{k}: {v}' for k,v in value.items()) or "none"
        elif isinstance(value, list):
            description = '; '.join(', '.join(g) if isinstance(g,list) else g for g in value) or "none flagged"
        else:
            description = str(value)
        observation(fid, "dataset_summary", [], f"Dataset {key.replace('_',' ')}: {description}.", {key:value})
        summary["finding_links"][key] = [fid]
    coverage = {"near_duplicate_comparisons": comparisons, "near_duplicate_limit": 2000, "omitted_near_duplicate_candidates": omitted,
                "grouping_columns_screened": grouping_names, "grouping_column_limit": 20, "omitted_grouping_columns": max(0,p-20),
                "grouping_columns_excluded": [{"column": name, "reason": "grouping-column screening limit"} for name in names if name not in grouping_names],
                "eligible_missingness_candidates": len(missing_candidates), "reported_missingness_candidates": 0}
    return summary, {"rules": rules, "coverage": coverage, "value_exclusions": blocked, "missingness_tests": missingness_tests}, missing_candidates
