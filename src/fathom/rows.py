"""Row-level and temporal structure: measured counts with positions; meanings stay questions."""

from collections import Counter, defaultdict
from datetime import date
import statistics

from .parsing import parse_date, parse_datetime

LIMIT = 10  # example row positions per finding (1-based data rows, header excluded)
RULES = {
    "blank_rows": "every cell missing (connector blank) in the row",
    "numeric_blank_rows": ">=2 inferred/declared numeric columns; row not wholly blank but missing in every numeric column",
    "duplicate_rows": "row identical in every cell to an earlier row; positions are the later occurrences",
    "repeated_key": ">=10 distinct nonmissing values; modal group size k in 2..20; groups of size k cover >=90% of nonmissing rows; "
                    "at most 3 keys, columns with an identical partition reported as the same grouping; within-key constant = one value "
                    "(missing counts as a value) in every group of size >=2 and >=2 values between groups",
    "temporal_period": ">=20 dated values; >=99% (and not all) fall in one calendar month, else one calendar year; values outside it reported. "
                       "Day resolution: a straggler inside the dominant month/year is not reported",
    "temporal_fence": ">=20 dated values; calendar day ordinal below Q1-3xIQR or above Q3+3xIQR (inclusive quartiles), IQR>0. "
                      "Day resolution: time of day is ignored, so same-day stragglers are not reported",
    "duplicate_timestamps": "temporal column whose values carry a time of day, >=20 values and >=90% distinct; rows repeating an earlier value",
    "interval": "declared intervals only; both cells strict ISO date or date-time (date-only read as midnight); duration=end-start in seconds",
    "interval_question": ">=2 temporal columns and no declared interval",
}


def positions(indices):
    return [i + 1 for i in indices[:LIMIT]]


def shown(indices, total=None):
    """Row positions in prose: 1-based data rows, header excluded."""
    total = len(indices) if total is None else total
    text = ", ".join(str(i) for i in positions(indices))
    return ("1-based row " if total == 1 else "1-based rows ") + text + (f", first {LIMIT} of {total}" if total > LIMIT else "")


def row_structure(rows, columns, cfg, emit):
    n = len(rows)
    out = {"rules": RULES, "position_basis": "1-based data-row positions (header excluded)", "example_limit": LIMIT}

    def observe(fid, rule, names, message, value, question):
        emit(fid, "observation", message, [{"path": "row_structure." + rule, "value": value}],
             "Measured on this snapshot under a disclosed rule; not proof of an error or a domain cause.",
             "rule:rows-v1", rule=rule, columns=names)
        if question is None: return
        emit(fid + "-question", "question", question, [{"finding": fid}],
             "The table cannot say what this pattern means; ask the data owner.", "rule:rows-v1", rule=rule, columns=names)

    blank = [i for i, r in enumerate(rows) if r and all(v is None for v in r)]
    out["blank_rows"] = {"count": len(blank), "share": len(blank) / n if n else None, "positions": positions(blank)}
    if blank:
        observe("rows-blank", "blank_rows", [], f"{len(blank):,} of {n:,} rows have no value in any column ({shown(blank)}).",
                out["blank_rows"], "What does a wholly blank row stand for here: a separator, an unrecorded entity, or an export artefact?")

    numeric = [j for j, c in enumerate(columns) if c["effective_type"] == "numeric"]
    blank_set = set(blank)
    hollow = [i for i, r in enumerate(rows) if len(numeric) >= 2 and i not in blank_set and all(r[j] is None for j in numeric)]
    names = [columns[j]["name"] for j in numeric]
    out["numeric_blank_rows"] = {"count": len(hollow), "share": len(hollow) / n if n else None, "numeric_columns": names, "positions": positions(hollow)}
    if hollow:
        listed = ", ".join(names[:10]) + (f" and {len(names)-10} more" if len(names) > 10 else "")
        observe("rows-numeric-blank", "numeric_blank_rows", names,
                f"{len(hollow):,} of {n:,} rows have other cells filled but no value in any of the {len(names)} numeric columns ({listed}; {shown(hollow)}).",
                out["numeric_blank_rows"], "Do these rows stand for entities with nothing measured, omitted observations, or a different row unit?")

    seen, dup = set(), []
    for i, r in enumerate(rows):
        key = tuple(r)
        if key in seen: dup.append(i)
        else: seen.add(key)
    out["duplicate_rows"] = {"count": len(dup), "positions": positions(dup)}

    out["repeated_keys"] = repeated_keys(rows, columns, n, observe)
    out["temporal"] = temporal(rows, columns, cfg, observe)
    out["intervals"] = [interval(rows, columns, item, observe) for item in cfg.get("intervals", [])]
    temporal_names = [c["name"] for c in columns if c["effective_type"] == "temporal"]
    out["interval_question"] = None
    if len(temporal_names) >= 2 and not cfg.get("intervals"):
        out["interval_question"] = {"temporal_columns": temporal_names}
        emit("rows-interval-undeclared", "question",
             f"{len(temporal_names)} date/time columns ({', '.join(temporal_names)}); does any pair form a start/end interval? "
             "Declare it under `intervals` to check ordering and durations.",
             [{"path": "row_structure.interval_question", "value": out["interval_question"]}],
             "No interval is inferred from column names; pairing is a domain declaration.", "rule:rows-v1",
             rule="interval_question", columns=temporal_names)
    return out


def repeated_keys(rows, columns, n, observe):
    reported, partitions = [], []
    for index, col in enumerate(columns):
        if len(reported) >= 3: break
        name = col["name"]
        groups = defaultdict(list)
        for i, r in enumerate(rows):
            if r[index] is not None: groups[r[index]].append(i)
        keyed = sum(len(g) for g in groups.values())
        if len(groups) < 10 or not keyed: continue
        sizes = Counter(len(g) for g in groups.values())
        k, count = sorted(sizes.items(), key=lambda x: (-x[1], x[0]))[0]
        covered = k * count
        if not 2 <= k <= 20 or covered / keyed < .9: continue
        partition = frozenset(frozenset(g) for g in groups.values())
        if partition in partitions: continue
        member = [g for g in groups.values() if len(g) >= 2]
        constant, same = [], []
        for j, other in enumerate(columns):
            if j == index: continue
            between = len({rows[i][j] for g in groups.values() for i in g})
            if between >= 2 and all(len({rows[i][j] for i in g}) == 1 for g in member):
                (same if between == len(groups) else constant).append(other["name"])
        partitions.append(partition)
        exceptions = sorted(i for g in groups.values() if len(g) != k for i in g)
        value = {"column": name, "k": k, "distinct_keys": len(groups), "keys_with_k_rows": count, "rows_in_k_groups": covered,
                 "nonmissing_rows": keyed, "missing_key_rows": n - keyed, "share": covered / keyed,
                 "size_distribution": [{"size": s, "keys": c} for s, c in sorted(sizes.items())],
                 "exception_positions": positions(exceptions), "constant_within_key": constant[:10],
                 "constant_within_key_count": len(constant), "same_grouping": same[:10]}
        reported.append(value)
        listed = ", ".join(constant[:10]) + (f" and {len(constant)-10} more" if len(constant) > 10 else "")
        message = (f"Most nonmissing rows belong to groups of exactly {k} by {name}: {covered:,} of {keyed:,} ({covered/keyed:.1%}), "
                   f"from {count:,} of {len(groups):,} {name} values"
                   + (f"; within each {name} value, {listed} never change" if constant else "")
                   + (f"; {', '.join(same[:10])} splits rows into exactly the same groups" if same else "")
                   + ("" if constant or same else "; no other column is constant within each value") + ".")
        observe(f"rows-key-{index}", "repeated_key", [name] + constant[:10], message, value,
                f"Is {name} an entity key with {k} rows each (alternatives, repeated measures, periods)? Would analysis need to account for this grouping?")
    return reported


def temporal(rows, columns, cfg, observe):
    results = []
    for index, col in enumerate(columns):
        if col["effective_type"] != "temporal": continue
        name, fmt = col["name"], cfg["columns"].get(col["name"], {}).get("date_format")
        dated = [(i, date.fromisoformat(p["date"])) for i, r in enumerate(rows)
                 if r[index] is not None and (p := parse_date(r[index], fmt)) is not None]
        entry = {"column": name, "dated_values": len(dated), "period": None, "fence": None, "duplicate_timestamps": None}
        if len(dated) >= 20:
            for grain, label in (("month", lambda d: d.strftime("%Y-%m")), ("year", lambda d: str(d.year))):
                periods = Counter(label(d) for _, d in dated)
                top, count = sorted(periods.items(), key=lambda x: (-x[1], x[0]))[0]
                if count < len(dated) and count / len(dated) >= .99:
                    outside = [i for i, d in dated if label(d) != top]
                    values = sorted({rows[i][index] for i in outside})
                    entry["period"] = {"grain": grain, "period": top, "inside": count, "outside": len(outside), "share_inside": count / len(dated),
                                       "positions": positions(outside), "values": values[:LIMIT]}
                    observe(f"rows-period-{index}", "temporal_period", [name],
                            f"{count:,} of {len(dated):,} {name} values ({count/len(dated):.2%}) fall in {grain} {top}; {len(outside):,} outside it at day resolution "
                            f"({shown(outside)}: {', '.join(values[:3])}{'…' if len(values) > 3 else ''}). Stragglers inside {top} are not detected by this rule.",
                            entry["period"], f"Do the {name} values outside {top} belong to this extract?")
                    break
            ordinals = [d.toordinal() for _, d in dated]
            q1, _, q3 = statistics.quantiles(ordinals, n=4, method="inclusive")
            iqr = q3 - q1
            if iqr > 0:
                low, high = q1 - 3 * iqr, q3 + 3 * iqr
                far = [i for (i, d) in dated if not low <= d.toordinal() <= high]
                if far:
                    entry["fence"] = {"low": date.fromordinal(max(1, int(-(-low // 1)))).isoformat(), "high": date.fromordinal(min(date.max.toordinal(), int(high // 1))).isoformat(),
                                      "iqr_days": iqr, "count": len(far), "positions": positions(far)}
                    observe(f"rows-fence-{index}", "temporal_fence", [name],
                            f"{len(far)} {name} values lie outside {entry['fence']['low']}..{entry['fence']['high']} (quartiles ± 3×IQR at day resolution, IQR {iqr:g} days; {shown(far)}).",
                            entry["fence"], f"Are the far {name} values genuine, mis-keyed, or placeholders?")
        stamped = [(i, p[0]) for i, r in enumerate(rows) if r[index] is not None and (p := parse_datetime(r[index])) is not None and p[1]]
        values = [r[index] for r in rows if r[index] is not None]
        if len(stamped) >= 20 and len(stamped) == len(values) and len({v for _, v in stamped}) / len(stamped) >= .9:
            seen, repeats = set(), []
            for i, v in stamped:
                if v in seen: repeats.append(i)
                else: seen.add(v)
            shared = Counter(v for _, v in stamped)
            entry["duplicate_timestamps"] = {"rows_repeating": len(repeats), "repeated_values": sum(c > 1 for c in shared.values()),
                                             "distinct": len(shared), "values": len(stamped), "positions": positions(repeats)}
            if repeats:
                observe(f"rows-dup-time-{index}", "duplicate_timestamps", [name],
                        f"{len(repeats):,} rows repeat an earlier {name} timestamp exactly ({entry['duplicate_timestamps']['repeated_values']} timestamps shared); {shown(repeats)}.",
                        entry["duplicate_timestamps"], f"Are rows sharing a {name} timestamp separate events, or duplicated records?")
        results.append(entry)
    return results


def interval(rows, columns, item, observe):
    names = [c["name"] for c in columns]
    a, b = names.index(item["start"]), names.index(item["end"])
    durations, negative, zero, unparsed, date_only = [], [], [], 0, 0
    for i, r in enumerate(rows):
        if r[a] is None or r[b] is None: continue
        s, e = parse_datetime(r[a]), parse_datetime(r[b])
        if s is None or e is None:
            unparsed += 1; continue
        date_only += not (s[1] and e[1])
        seconds = (e[0] - s[0]).total_seconds()
        durations.append(seconds)
        if seconds < 0: negative.append(i)
        elif seconds == 0: zero.append(i)
    m = len(durations)
    total = m + unparsed
    dist = None
    if m:
        cuts = statistics.quantiles(durations, n=100, method="inclusive") if m >= 2 else [durations[0]] * 99
        dist = {"min": min(durations), "p1": cuts[0], "p25": cuts[24], "median": statistics.median(durations), "p75": cuts[74], "p99": cuts[98], "max": max(durations)}
    value = {"start": item["start"], "end": item["end"], "complete_pairs": total, "pairs": m, "unparsed_pairs": unparsed, "date_only_pairs": date_only,
             "end_before_start": len(negative), "end_equals_start": len(zero), "negative_share": len(negative) / m if m else None,
             "zero_share": len(zero) / m if m else None, "duration_seconds": dist,
             "negative_positions": positions(negative), "zero_positions": positions(zero),
             "basis": "full date-time parsed for this check (time of day included); the date profile elsewhere uses the calendar date only"}
    pair = f"{item['start']} → {item['end']}"
    unparsed_note = (f" {unparsed:,} of {total:,} pairs are not strict ISO date/date-time "
                     "(e.g. MM/DD/YYYY, a Z or offset suffix, fractional seconds) and were not checked.") if unparsed else ""
    if not m:
        message = (f"Declared interval {pair}: none of {total:,} complete pairs could be parsed, so ordering and durations were not measured."
                   + unparsed_note if total else f"Declared interval {pair}: no row has both cells filled, so nothing was measured.")
        question = f"What date/time format do {item['start']} and {item['end']} use? Only strict ISO dates or date-times are parsed for interval checks."
    else:
        parts = [f"{len(negative)} end before start" + (f" ({shown(negative)})" if negative else ""),
                 f"{len(zero)} end equal to start" + (f" ({shown(zero)})" if zero else "")]
        message = (f"Declared interval {pair}: {m:,} of {total:,} complete pairs parsed; {'; '.join(parts)}; "
                   f"median duration {dist['median']:g} s (min {dist['min']:g}, max {dist['max']:g}). Full date-times parsed for this check.{unparsed_note}")
        question = None
        if negative or zero:
            question = f"What do zero or negative {pair} durations represent: instant records, clock errors, or cancelled events?"
        if unparsed:
            question = (question + " " if question else "") + f"What format do the {unparsed:,} unparsed {pair} pairs use?"
    observe(f"rows-interval-{a}-{b}", "interval", [item["start"], item["end"]], message, value, question)
    return value
