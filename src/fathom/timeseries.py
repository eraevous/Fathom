"""Declared time series: observation process, four sparsity dimensions, ACF/PACF per granularity.

Standard library only. The optional `stats` extra (scipy) adds a periodogram peak; without it the
peak is reported as not computed. Every claim carries its rule; meanings stay questions.
"""

from collections import Counter, defaultdict
from datetime import datetime, timedelta
import math
from statistics import NormalDist, median, quantiles

from .parsing import finite_number, parse_date, parse_datetime
from .univariate import stored

GRAINS = ("hour", "day", "week", "month")
CALENDAR = {"hour": (24, 168), "day": (7,), "week": (52,), "month": (12,)}  # calendar cycles, not domain meaning
DEFAULT_LAG = {"hour": 168, "day": 28, "week": 26, "month": 24}
MIN_N, MAX_PERIODS, TOP_N = 30, 100_000, 5
RULES = {
    "regularise": "periods run from the floor of the first to the floor of the last parsed timestamp; value series sum parsed "
                  "values per period, event series count rows per period; week = ISO week starting Monday",
    "observation": "value series: a period with no row (or only rows without a parsed value) is a missing observation, a period "
                   "whose values sum to 0 is a zero; event series: a period with no row has no recorded event (0 counted), and the "
                   "table cannot say whether the process was observed then",
    "frequency": "zero share = zero periods / observed periods; inter-event interval = periods from one non-zero period to the "
                 "next with no missing period between them (mean is the ADI alias); intervals that span a missing period are counted "
                 "separately and excluded",
    "amplitude": "quantiles (inclusive) of non-zero period values; CV2 = (population sd / mean)^2 of non-zero values",
    "wavelength": "ACF r_k = sum over pairs observed at t and t+k of (x_t-m)(x_t+k-m) / sum over observed (x_t-m)^2; PACF by "
                  "Durbin-Levinson; per-lag 95% band +/-1.96/sqrt(n); dominant lag = supported local ACF peak above the band",
    "duration": "run lengths in periods of consecutive zero and consecutive non-zero periods; a missing period ends a run",
    "reliability": f"n < {MIN_N} observed periods: insufficient (applies to every signal, including zero periods and bursts); "
                   "zero variance: undefined; lag > n/4: poorly supported",
    "cycle": "present when a dominant ACF lag >= 2 (supported local peak above the per-lag band) also exceeds the family-wise band",
    "signal": "present when |r_k| exceeds the family-wise band z(1-0.025/L)/sqrt(n_k) at any supported lag (Bonferroni over the "
              "L supported lags of this one correlogram; not adjusted across granularities, groups or values vs occurrence); "
              "absent = not detected under this rule, not evidence of absence; insufficient evidence under the reliability rule",
    "missingness": "valid pairs are counted per lag; a lag with fewer than max(10, n/4) valid pairs is not estimable (distinct from "
                   "an estimate near 0) and never counts toward present or absent; with missing periods the bands use the per-lag "
                   "valid pair count, n_k = pairs at lag k (complete series: n_k = n); PACF stops at the first non-estimable lag; "
                   "supported = estimable and lag <= n/4",
    "auto": "auto = every granularity at or coarser than the timestamps' resolution (hour needs a time of day) with "
            f"2..{MAX_PERIODS:,} periods in span",
    "by": f"by: the top N groups by row count (default {TOP_N}, ties by value); other groups and rows with a missing key are counted, not analysed; "
          "each group's span runs from its own first to its own last timestamp",
    "spectral": "periodogram peak (scipy.signal.periodogram, mean removed) on gap-free series only; requires the stats extra",
}


def floor(dt, grain):
    if grain == "hour": return dt.replace(minute=0, second=0, microsecond=0)
    day = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    if grain == "day": return day
    if grain == "week": return day - timedelta(days=day.weekday())
    return day.replace(day=1)


def advance(dt, grain):
    if grain == "hour": return dt + timedelta(hours=1)
    if grain == "day": return dt + timedelta(days=1)
    if grain == "week": return dt + timedelta(days=7)
    return dt.replace(year=dt.year + dt.month // 12, month=dt.month % 12 + 1)


def label(dt, grain):
    return {"hour": dt.strftime("%Y-%m-%dT%H"), "day": dt.strftime("%Y-%m-%d"),
            "week": "week of " + dt.strftime("%Y-%m-%d"), "month": dt.strftime("%Y-%m")}[grain]


def span_periods(first, last, grain):
    a, b = floor(first, grain), floor(last, grain)
    if grain == "month": return (b.year - a.year) * 12 + b.month - a.month + 1
    step = {"hour": 3600, "day": 86400, "week": 604800}[grain]
    return int((b - a).total_seconds() // step) + 1


def r10(x):
    return round(x, 10) if x is not None and math.isfinite(x) else None


def summary(values):
    """Scale-bearing quantiles keep the spec 008 stored-number rule (at least 6 significant figures)."""
    if not values: return None
    q = quantiles(values, n=4, method="inclusive") if len(values) >= 2 else [values[0]] * 3
    return {"n": len(values), "min": stored(min(values)), "p25": stored(q[0]), "median": stored(median(values)),
            "p75": stored(q[2]), "max": stored(max(values)), "mean": stored(sum(values) / len(values))}


def runs(states):
    """Run lengths of 'zero' and 'nonzero' states; None (missing) ends a run."""
    out, current, length = {"zero": [], "nonzero": []}, None, 0
    for s in states + [None]:
        if s == current and s is not None: length += 1; continue
        if current is not None: out[current].append(length)
        current, length = s, 1
    return out


def acf(x, max_lag):
    """Pairwise-complete autocorrelation; x holds None for missing periods. Returns ([r_k], [valid pairs at k])."""
    obs = [v for v in x if v is not None]
    n = len(obs)
    m = sum(obs) / n
    c0 = sum((v - m) ** 2 for v in obs)
    if c0 <= 1e-12 * max(1.0, m * m) * n: return None
    out, pairs = [], []
    for k in range(1, max_lag + 1):
        valid = [t for t in range(len(x) - k) if x[t] is not None and x[t + k] is not None]
        pairs.append(len(valid))
        out.append(sum((x[t] - m) * (x[t + k] - m) for t in valid) / c0)
    return out, pairs


def pacf(r):
    """Durbin-Levinson recursion on the ACF r[0]=lag 1; stops if the recursion becomes singular."""
    out, phi = [], []
    for k in range(1, len(r) + 1):
        if k == 1: kk = r[0]; new = [kk]
        else:
            den = 1 - sum(phi[j] * r[j] for j in range(k - 1))
            if den <= 1e-12: break
            kk = (r[k - 1] - sum(phi[j] * r[k - 2 - j] for j in range(k - 1))) / den
            new = [phi[j] - kk * phi[k - 2 - j] for j in range(k - 1)] + [kk]
        if not -1 - 1e-9 <= kk <= 1 + 1e-9: break
        out.append(kk); phi = new
    return out


def correlogram(x, max_lag):
    n = sum(v is not None for v in x)
    complete = n == len(x)
    lag = min(max_lag, max(0, len(x) - 2))
    min_pairs = max(10, n / 4)
    base = {"n": n, "max_lag": lag, "supported_max_lag": min(lag, n // 4), "band": r10(1.96 / math.sqrt(n)) if n else None,
            "min_pairs": r10(min_pairs), "complete": complete}
    if n < MIN_N: return {**base, "status": "insufficient", "note": f"{n} observed periods (< {MIN_N}); ACF/PACF not computed"}
    got = acf(x, lag) if lag else ([], [])
    if got is None: return {**base, "status": "undefined", "note": "zero variance (constant series); ACF/PACF undefined"}
    r, pairs = got
    estimable = [pairs[k - 1] >= min_pairs for k in range(1, lag + 1)]
    first_gap = next((k for k in range(1, lag + 1) if not estimable[k - 1]), lag + 1)
    p = pacf(r[:first_gap - 1])  # Durbin-Levinson needs every earlier lag
    supported = [k for k in range(1, lag + 1) if k <= n // 4 and estimable[k - 1]]
    L = len(supported)
    z = NormalDist().inv_cdf(1 - 0.025 / L) if L else None
    def n_eff(k): return n if complete else pairs[k - 1]
    band = {k: 1.96 / math.sqrt(n_eff(k)) for k in range(1, lag + 1) if pairs[k - 1]}
    family = {k: z / math.sqrt(n_eff(k)) for k in supported}
    ok = set(supported)
    lags = [{"lag": k, "pairs": pairs[k - 1], "estimable": estimable[k - 1],
             "acf": r10(r[k - 1]) if estimable[k - 1] else None, "pacf": r10(p[k - 1]) if k <= len(p) else None,
             "band": r10(band.get(k)), "family_band": r10(family.get(k)), "acf_outside_band": estimable[k - 1] and abs(r[k - 1]) > band[k], "supported": k in ok} for k in range(1, lag + 1)]
    def up(k): return k in ok and r[k - 1] > band[k]
    peaks = [k for k in supported if up(k) and (k == 1 or not estimable[k - 2] or r[k - 1] >= r[k - 2]) and (k == lag or not estimable[k] or r[k - 1] >= r[k])]
    dominant = sorted(peaks, key=lambda k: (-r[k - 1], k))[:3]
    biggest = max((abs(r[k - 1]) for k in supported), default=0)
    hit = any(abs(r[k - 1]) > family[k] for k in supported)
    signal = "present" if hit else "absent" if L else "not estimable"
    out = {**base, "status": "computed", "lags": lags, "not_estimable_lags": [k for k in range(1, lag + 1) if not estimable[k - 1]],
           "band": r10(max((band[k] for k in supported), default=base["band"])),
           "family_band": r10(max(family.values())) if family else None,
           "significant_acf_lags": [k for k in supported if abs(r[k - 1]) > band[k]],
           "significant_pacf_lags": [k for k in supported if k <= len(p) and abs(p[k - 1]) > band[k]],
           "dominant_lags": [{"lag": k, "acf": r10(r[k - 1]), "family_band": r10(family[k])} for k in dominant],
           "max_abs_acf": r10(biggest), "signal": signal, "pacf_computed_to": len(p)}
    if signal == "not estimable":
        out["note"] = f"no lag within n/4 has >= {min_pairs:g} valid pairs; autocorrelation not estimable (not the same as near zero)"
    return out


def spectral(x, deps):
    if any(v is None for v in x) or len(x) < MIN_N: return {"status": "not computed", "reason": "missing periods or n < 30"}
    try:
        from scipy.signal import periodogram
    except ImportError:
        deps["scipy"] = "unavailable; spectral peak not computed"
        return {"status": "not computed", "reason": "stats extra (scipy) not installed"}
    deps["scipy"] = "available"
    freqs, power = periodogram(x, detrend="constant")
    pairs = [(float(p), float(f)) for f, p in zip(freqs, power) if f > 0]
    if not pairs or max(p for p, _ in pairs) <= 0: return {"status": "not computed", "reason": "no power at non-zero frequency"}
    p, f = max(pairs, key=lambda t: (t[0], -t[1]))
    return {"status": "computed", "peak_period": r10(1 / f), "peak_share_of_power": r10(p / sum(q for q, _ in pairs))}


def analyse_grain(points, grain, mode, max_lag, deps):
    first, last = min(points), max(points)
    periods = {}
    t = floor(first, grain)
    end = floor(last, grain)
    while t <= end:
        periods[t] = None; t = advance(t, grain)
    rows, values = Counter(), defaultdict(float)
    with_value = Counter()
    for dt, v in points.items():
        for value in v:
            key = floor(dt, grain); rows[key] += 1
            if value is not None: values[key] += value; with_value[key] += 1
    x, states = [], []
    for key in periods:
        if mode == "events": val = float(rows[key])
        else: val = values[key] if with_value[key] else None
        x.append(val)
        states.append(None if val is None else "zero" if val == 0 else "nonzero")
    observed = [v for v in x if v is not None]
    nonzero = [v for v in observed if v != 0]
    zero_n = len(observed) - len(nonzero)
    idx = [i for i, v in enumerate(x) if v not in (None, 0)]
    gaps, spanning = [], 0
    for a, b in zip(idx, idx[1:]):
        if any(x[t] is None for t in range(a + 1, b)): spanning += 1
        else: gaps.append(b - a)
    rl = runs(states)
    amp = summary(nonzero)
    cv2 = None
    if len(nonzero) >= 2 and amp["mean"]:
        mean = sum(nonzero) / len(nonzero)
        cv2 = r10((sum((v - mean) ** 2 for v in nonzero) / len(nonzero)) / mean ** 2)
    indicator = [None if v is None else float(v != 0) for v in x]
    lag = max_lag or (52 if grain == "week" and len(x) >= 104 else DEFAULT_LAG[grain])  # 52-week lag when the span allows
    values_corr, occurrence_corr = correlogram(x, lag), correlogram(indicator, lag)
    calendar = []
    for s in CALENDAR[grain]:
        entry = {"lag": s, "acf": None, "status": f"not evaluated at max_lag {values_corr['max_lag']}"}
        if values_corr["status"] == "computed" and s <= values_corr["max_lag"] and not values_corr["lags"][s - 1]["estimable"]:
            entry = {"lag": s, "acf": None, "status": "not estimable (too few valid pairs)"}
        elif values_corr["status"] == "computed" and s <= values_corr["max_lag"]:
            entry = {"lag": s, "acf": values_corr["lags"][s - 1]["acf"], "outside_band": values_corr["lags"][s - 1]["acf_outside_band"],
                     "status": "supported" if s <= values_corr["supported_max_lag"] else "poorly supported (lag > n/4)"}
        calendar.append(entry)
    return {
        "granularity": grain, "periods_in_span": len(x), "first_period": label(floor(first, grain), grain),
        "last_period": label(end, grain), "observed_periods": len(observed),
        "periods_with_rows": sum(1 for k in periods if rows[k]),
        "missing_periods": len(x) - len(observed) if mode == "values" else 0,
        "no_recorded_event_periods": sum(1 for k in periods if not rows[k]) if mode == "events" else 0,
        "rows_present_no_value_periods": sum(1 for k in periods if rows[k] and not with_value[k]) if mode == "values" else 0,
        "frequency": {"zero_periods": zero_n, "nonzero_periods": len(nonzero),
                      "zero_share": r10(zero_n / len(observed)) if observed else None,
                      "inter_event_interval": summary(gaps), "intervals_spanning_missing": spanning, "adi": r10(sum(gaps) / len(gaps)) if gaps else None},
        "amplitude": {"nonzero": amp, "cv2": cv2},
        "wavelength": {"values": values_corr, "occurrence": occurrence_corr, "calendar_lags": calendar,
                       "spectral": spectral(x, deps)},
        "duration": {"zero_runs": summary(rl["zero"]), "nonzero_runs": summary(rl["nonzero"]),
                     "longest_zero_run": max(rl["zero"], default=0), "longest_nonzero_run": max(rl["nonzero"], default=0)},
        "series": [{"period": label(k, grain), "value": stored(v)} for k, v in zip(periods, x)][:2000],
        "series_truncated": max(0, len(x) - 2000),
    }


def signals(grains):
    """Per signal, the granularities where it is present, absent, or lacks evidence; each with its rule."""
    out = []
    def add(name, rule, verdicts):
        groups = {"present": [], "absent": [], "undefined": [], "not estimable": [], "insufficient evidence": []}
        for g, v in verdicts: groups[v].append(g)
        out.append({"signal": name, "rule": rule, **groups, "notes": notes})
    notes = {}
    for g in grains:
        for kind in ("values", "occurrence"):
            c = g["wavelength"][kind]
            if "note" in c: notes[f"{g['granularity']} {kind}"] = c["note"]
    def corr_verdict(c):
        if c["status"] == "undefined": return "undefined"
        if c["status"] == "computed" and c["signal"] == "not estimable": return "not estimable"
        return "insufficient evidence" if c["status"] != "computed" or c["signal"] == "insufficient" else c["signal"]
    def enough(g): return g["observed_periods"] >= MIN_N
    add("autocorrelation in values", RULES["signal"], [(g["granularity"], corr_verdict(g["wavelength"]["values"])) for g in grains])
    add("autocorrelation in occurrence (non-zero indicator)", RULES["signal"],
        [(g["granularity"], corr_verdict(g["wavelength"]["occurrence"])) for g in grains])
    def cycle(g):
        c = g["wavelength"]["values"]
        if corr_verdict(c) != "present": return corr_verdict(c)
        return "present" if any(d["lag"] >= 2 and d["acf"] > d["family_band"] for d in c["dominant_lags"]) else "absent"
    add("repeating cycle (dominant ACF peak at lag >= 2 above the family-wise band)", RULES["cycle"], [(g["granularity"], cycle(g)) for g in grains])
    add("zero periods", "observed periods whose value is 0 (event series: no recorded event)",
        [(g["granularity"], "insufficient evidence" if not enough(g) else "present" if g["frequency"]["zero_periods"] else "absent") for g in grains])
    add("bursts (non-zero runs of >= 2 periods separated by zeros)", RULES["duration"],
        [(g["granularity"], "insufficient evidence" if not enough(g) else
          "present" if g["frequency"]["zero_periods"] and g["duration"]["longest_nonzero_run"] >= 2 else "absent") for g in grains])
    return out


def informative(grains):
    """Two granularities for charts: computed correlograms ranked by supported lags outside the family band, then n."""
    def score(g):
        c = g["wavelength"]["values"]
        if c["status"] != "computed": return None
        hits = sum(1 for l in c["lags"] if l["supported"] and abs(l["acf"]) > l["family_band"])
        return (-hits, -c["n"], GRAINS.index(g["granularity"]))
    ranked = sorted((s, g["granularity"]) for g in grains if (s := score(g)) is not None)
    return [g for _, g in ranked[:2]]


def parse_time(value, fmt):
    p = parse_datetime(value)
    if p is not None: return p
    d = parse_date(value, fmt)
    return (datetime.fromisoformat(d["date"]), False) if d else None


def analyse(rows, names, cfg, item, deps, group=None, subset=None):
    ti = names.index(item["time"]); vi = names.index(item["value"]) if item.get("value") else None
    fmt = cfg["columns"].get(item["time"], {}).get("date_format")
    mode = "values" if vi is not None else "events"
    points, unparsed, missing_time, no_value, with_time_of_day = defaultdict(list), 0, 0, 0, 0
    for i in (subset if subset is not None else range(len(rows))):
        r = rows[i]
        if r[ti] is None: missing_time += 1; continue
        p = parse_time(r[ti], fmt)
        if p is None: unparsed += 1; continue
        with_time_of_day += p[1]
        value = None
        if vi is not None:
            value = finite_number(r[vi]) if r[vi] is not None else None
            no_value += value is None
        points[p[0]].append(value if vi is not None else 1.0)
    total = len(subset) if subset is not None else len(rows)
    parsed = sum(len(v) for v in points.values())
    stamps = sorted(points)
    inter = [(b - a).total_seconds() for a, b in zip(stamps, stamps[1:])]
    process = {"raw_rows": total, "rows_with_parsed_time": parsed, "missing_time": missing_time, "unparsed_time": unparsed,
               "rows_without_value": no_value if mode == "values" else None,
               "explicit_zero_rows": sum(1 for v in points.values() for x in v if x == 0) if mode == "values" else None,
               "distinct_timestamps": len(stamps), "duplicate_timestamp_rows": parsed - len(stamps),
               "time_of_day": "all" if parsed and with_time_of_day == parsed else "none" if not with_time_of_day else "some",
               "first": stamps[0].isoformat(sep=" ") if stamps else None, "last": stamps[-1].isoformat(sep=" ") if stamps else None,
               "native_interarrival_seconds": summary(inter)}
    out = {"time": item["time"], "value": item.get("value"), "mode": mode, "group": group, "observation_process": process,
           "granularities": [], "skipped_granularities": []}
    if not stamps:
        out["signals"] = []; out["charted"] = []
        return out
    requested = item["granularities"]
    wanted = [g for g in GRAINS if g in requested or "auto" in requested]
    for g in wanted:
        n = span_periods(stamps[0], stamps[-1], g)
        if g == "hour" and process["time_of_day"] != "all":
            out["skipped_granularities"].append({"granularity": g, "reason": "timestamps lack a time of day"}); continue
        if n > MAX_PERIODS or ("auto" in requested and g not in requested and n < 2):
            out["skipped_granularities"].append({"granularity": g, "reason": f"{n:,} periods in span (allowed 2..{MAX_PERIODS:,})"}); continue
        out["granularities"].append(analyse_grain(points, g, mode, item.get("max_lag"), deps))
    out["signals"] = signals(out["granularities"])
    out["charted"] = informative(out["granularities"])
    return out


def time_series(rows, columns, cfg, emit):
    names = [c["name"] for c in columns]
    deps = {}
    result = {"rules": RULES, "declared": cfg.get("time_series", []), "series": [], "question": None, "dependencies": deps}
    for si, item in enumerate(cfg.get("time_series", [])):
        if item.get("by"):
            bi = names.index(item["by"])
            groups = defaultdict(list)
            missing_key = 0
            for i, r in enumerate(rows):
                if r[bi] is None: missing_key += 1
                else: groups[r[bi]].append(i)
            ranked = sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))
            top = item.get("top_n", TOP_N)
            entry = {"time": item["time"], "value": item.get("value"), "by": item["by"], "groups_total": len(groups), "groups_analysed": min(top, len(groups)),
                     "rows_in_other_groups": sum(len(v) for _, v in ranked[top:]), "rows_missing_key": missing_key, "top_n": top,
                     "groups": [analyse(rows, names, cfg, item, deps, group=k, subset=v) for k, v in ranked[:top]]}
        else:
            entry = {"time": item["time"], "value": item.get("value"), "by": None, "groups": [analyse(rows, names, cfg, item, deps)]}
        result["series"].append(entry)
        describe(si, entry, emit)
    if not cfg.get("time_series"):
        result["question"] = undeclared(rows, columns, cfg)
    if result["question"]:
        q = result["question"]
        temporal, numeric = [t["column"] for t in q["temporal_columns"]], q["numeric_columns"]
        emit("ts-undeclared", "question",
             f"{', '.join(f'{t['column']} ({t['distinct_periods']:,} distinct {t['granularity']}s)' for t in q['temporal_columns'])}: "
             "would counts of rows over time (time_series with value: null) be useful"
             + (f", or totals of {', '.join(numeric[:5])}{' …' if len(numeric) > 5 else ''} over time" if numeric else "")
             + "? Declare it under `time_series` to measure temporal structure.",
             [{"path": "time_series.question", "value": q}],
             "No series is inferred from column names or types; what a series measures is a domain declaration.", "rule:timeseries-v1",
             rule="time_series_undeclared", columns=temporal + numeric[:10])
    return result


def undeclared(rows, columns, cfg):
    """Ask only when a temporal column spans >= MIN_N distinct periods at its finest valid granularity."""
    found = []
    for j, c in enumerate(columns):
        if c["effective_type"] != "temporal": continue
        fmt = cfg["columns"].get(c["name"], {}).get("date_format")
        parsed = [p for r in rows if r[j] is not None and (p := parse_time(r[j], fmt)) is not None]
        if not parsed: continue
        grain = "hour" if all(t for _, t in parsed) else "day"
        distinct = len({floor(dt, grain) for dt, _ in parsed})
        if distinct >= MIN_N: found.append({"column": c["name"], "granularity": grain, "distinct_periods": distinct})
    if not found: return None
    numeric = []
    for j, c in enumerate(columns):
        if c["effective_type"] != "numeric" or cfg["columns"].get(c["name"], {}).get("role") == "identifier": continue
        values = [n for r in rows if r[j] is not None and (n := finite_number(r[j])) is not None]
        if values and all(v == int(v) for v in values) and len(set(values)) / len(values) >= .95: continue  # identifier-like
        numeric.append(c["name"])
    return {"temporal_columns": found, "numeric_columns": numeric[:10],
            "rule": f"temporal column with >= {MIN_N} distinct periods at its finest valid granularity (hour if every value carries a "
                    "time of day, else day); numeric columns listed unless role identifier or integer-valued with distinct ratio >= 0.95"}


def series_name(entry, s):
    what = f"{entry['value']} by {entry['time']}" if entry["value"] else f"events by {entry['time']}"
    return what + (f" [{entry['by']} = {s['group']}]" if s["group"] is not None else "")


def describe(si, entry, emit):
    for gi, s in enumerate(entry["groups"]):
        name = series_name(entry, s)
        p = s["observation_process"]
        parts = [f"{p['rows_with_parsed_time']:,} of {p['raw_rows']:,} rows with a parsed {entry['time']}",
                 f"{p['distinct_timestamps']:,} distinct timestamps ({p['duplicate_timestamp_rows']:,} rows repeat an earlier one)"]
        for sig in s["signals"]:
            bits = [f"{k} at {', '.join(sig[k])}" for k in ("present", "absent", "undefined", "not estimable", "insufficient evidence") if sig[k]]
            parts.append(sig["signal"].split(" (")[0] + ": " + "; ".join(bits))
        fid = f"ts-{si}-{gi}"
        emit(fid, "observation", f"Temporal structure of {name}: " + "; ".join(parts) + ".",
             [{"path": f"time_series.series.{si}.groups.{gi}", "value": {"observation_process": p, "signals": s["signals"]}}],
             "Measured under disclosed rules on regularised periods; signals are statistical patterns, not causes.",
             "rule:timeseries-v1", rule="temporal_structure", columns=[c for c in (entry["time"], entry["value"], entry["by"]) if c])
        gaps = [(g["granularity"], g["missing_periods"] or g["no_recorded_event_periods"]) for g in s["granularities"] if g["missing_periods"] or g["no_recorded_event_periods"]]
        if gaps:
            g, k = gaps[0]
            kind = "missing observations" if s["mode"] == "values" else "periods with no recorded event"
            emit(fid + "-gaps", "question",
                 f"{name}: {k:,} {g} periods are {kind}. Was the process unobserved then, or did nothing occur? The table cannot tell.",
                 [{"finding": fid}], "Absence of rows is not evidence of absence of activity.", "rule:timeseries-v1",
                 rule="observation_gaps", columns=[entry["time"]])
        cycles = [(g["granularity"], d) for g in s["granularities"] if g["wavelength"]["values"]["status"] == "computed"
                  for d in g["wavelength"]["values"]["dominant_lags"] if d["lag"] >= 2 and d["acf"] > d["family_band"]]
        if cycles:
            g, d = cycles[0]
            emit(fid + "-cycle", "question",
                 f"{name}: the {g} ACF peaks at lag {d['lag']} (r = {d['acf']:.3f}). Does a known schedule in how this is produced repeat every {d['lag']} {g}s?",
                 [{"finding": fid}], "A correlogram peak is a pattern, not a mechanism.", "rule:timeseries-v1",
                 rule="dominant_cycle", columns=[entry["time"]])
