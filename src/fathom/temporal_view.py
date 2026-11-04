"""Temporal structure section: tables and ACF/PACF stem plots derived from the `time_series` artifact key."""

from html import escape

from .presentation import formatted, html_table, markdown_table

INTRO = ("Declared series only. Periods are regularised by aggregation; the four sparsity dimensions are measured per "
         "granularity. Statements are patterns under the stated rules, not causes; questions go to the data owner.")


def name(entry, s):
    what = f"{entry['value']} by {entry['time']}" if entry["value"] else f"events (row counts) by {entry['time']}"
    return what + (f" — {entry['by']} = {s['group']}" if s["group"] is not None else "")


def process_table(s):
    p = s["observation_process"]
    rows = [["Raw rows", formatted(p["raw_rows"])], ["Rows with a parsed time", formatted(p["rows_with_parsed_time"])],
            ["Missing / unparsed time", f"{p['missing_time']:,} / {p['unparsed_time']:,}"],
            ["Distinct timestamps", formatted(p["distinct_timestamps"])], ["Rows sharing a timestamp", formatted(p["duplicate_timestamp_rows"])],
            ["Time of day carried", p["time_of_day"]], ["First / last", f"{p['first']} / {p['last']}"]]
    if s["mode"] == "values":
        rows += [["Rows without a parsed value", formatted(p["rows_without_value"])], ["Rows with an explicit 0", formatted(p["explicit_zero_rows"])]]
    ia = p["native_interarrival_seconds"]
    if ia: rows.append(["Native inter-arrival (s): median / max", f"{formatted(ia['median'])} / {formatted(ia['max'])}"])
    for g in s["granularities"]:
        gap = (f"{g['missing_periods']:,} missing observations" if s["mode"] == "values" else f"{g['absent_event_periods']:,} with no event")
        tail = f"; {g['frequency']['zero_periods']:,} explicit zero" if s["mode"] == "values" else " (counted as 0)"
        rows.append([f"{g['granularity'].capitalize()} periods", f"{g['periods_in_span']:,} in span; {gap}{tail}"])
    for k in s["skipped_granularities"]: rows.append([f"{k['granularity'].capitalize()} skipped", k["reason"]])
    return {"caption": "Observation process", "headers": ["Measure", "Value"], "rows": rows, "numeric": []}


def corr_text(c):
    if c["status"] != "computed": return c["status"] + ": " + c["note"]
    dom = ", ".join(f"{d['lag']} ({d['acf']:.2f})" for d in c["dominant_lags"]) or "none"
    return f"n {c['n']}; signal {c['signal']} (max abs r {c['max_abs_acf']:.2f} vs family band {c['family_band']:.2f}); dominant lags {dom}"


def sparsity_table(s):
    grains = s["granularities"]
    def cell(g, f):
        try: v = f(g)
        except (TypeError, KeyError): v = None
        return v if isinstance(v, str) else formatted(v)
    spec = [
        ("Frequency", "zero share", lambda g: formatted(g["frequency"]["zero_share"], True) if g["frequency"]["zero_share"] is not None else None),
        ("Frequency", "mean inter-event interval (ADI), periods", lambda g: g["frequency"]["adi"]),
        ("Frequency", "intervals spanning a missing period (excluded)", lambda g: g["frequency"]["intervals_spanning_missing"]),
        ("Amplitude", "non-zero median [p25–p75]", lambda g: f"{formatted(g['amplitude']['nonzero']['median'])} [{formatted(g['amplitude']['nonzero']['p25'])}–{formatted(g['amplitude']['nonzero']['p75'])}]"),
        ("Amplitude", "CV² of non-zero values", lambda g: g["amplitude"]["cv2"]),
        ("Wavelength", "values ACF", lambda g: corr_text(g["wavelength"]["values"])),
        ("Wavelength", "occurrence ACF", lambda g: corr_text(g["wavelength"]["occurrence"])),
        ("Wavelength", "calendar lags", lambda g: "; ".join(f"{x['lag']}: " + (f"{x['acf']:.2f}, {x['status']}" if x["acf"] is not None else x["status"]) for x in g["wavelength"]["calendar_lags"])),
        ("Wavelength", "periodogram peak (periods)", lambda g: formatted(g["wavelength"]["spectral"]["peak_period"]) if g["wavelength"]["spectral"]["status"] == "computed" else "not computed: " + g["wavelength"]["spectral"]["reason"]),
        ("Duration", "zero runs: median / longest", lambda g: f"{formatted((g['duration']['zero_runs'] or {}).get('median'))} / {g['duration']['longest_zero_run']}"),
        ("Duration", "non-zero runs (bursts): median / longest", lambda g: f"{formatted((g['duration']['nonzero_runs'] or {}).get('median'))} / {g['duration']['longest_nonzero_run']}"),
    ]
    return {"caption": "Sparsity dimensions × granularities", "headers": ["Dimension", "Measure"] + [g["granularity"] for g in grains],
            "rows": [[d, m] + [cell(g, f) for g in grains] for d, m, f in spec], "numeric": []}


def signal_table(s):
    rows = [[x["signal"], ", ".join(x["present"]) or "—", ", ".join(x["absent"]) or "—", ", ".join(x["undefined"]) or "—", ", ".join(x["insufficient evidence"]) or "—", x["rule"]] for x in s["signals"]]
    return {"caption": "Signals: present / absent / undefined / insufficient evidence (with the rule)", "headers": ["Signal", "Present", "Absent", "Undefined", "Insufficient evidence", "Rule"], "rows": rows, "numeric": []}


def lag_table(g):
    c = g["wavelength"]["values"]; o = g["wavelength"]["occurrence"]
    olags = {l["lag"]: l for l in o.get("lags", [])}
    rows = [[str(l["lag"]), formatted(l["acf"]), formatted(l["pacf"]), "yes" if l["acf_outside_band"] else "", "" if l["supported"] else "poorly supported",
             formatted(olags[l["lag"]]["acf"]) if l["lag"] in olags else "—"] for l in c["lags"]]
    return {"caption": f"{g['granularity'].capitalize()} ACF/PACF (95% band ±{c['band']:.3f}; family band ±{c['family_band']:.3f})",
            "headers": ["Lag", "ACF", "PACF", "Outside 95% band", "Support", "Occurrence ACF"], "rows": rows, "numeric": [1, 2, 5]}


def stem(g, which):
    c = g["wavelength"]["values"]
    lags = [(l["lag"], l[which], l["supported"]) for l in c["lags"] if l[which] is not None]
    w, h, left, right, top, bottom = 560, 240, 55, 540, 15, 205
    def py(v): return top + (bottom - top) * (1 - v) / 2
    L = max(1, len(lags))
    def px(k): return left + (right - left) * (k - .5) / L
    title = f"{g['granularity'].capitalize()} {'ACF' if which == 'acf' else 'PACF'} — stem plot"
    out = [f'<svg role="img" data-kind="stem" aria-label="{escape(title, quote=True)}" viewBox="0 0 {w} {h}"><title>{escape(title)}</title>']
    for v in (-1, -.5, 0, .5, 1):
        out.append(f'<line x1="{left}" y1="{py(v):.1f}" x2="{right}" y2="{py(v):.1f}" stroke="#d5e1df"/>')
        out.append(f'<text x="{left-6}" y="{py(v)+5:.1f}" text-anchor="end" class="tick-label">{v:g}</text>')
    for b, dash in ((c["band"], "5 4"), (c["family_band"], "2 3")):
        for sgn in (1, -1):
            out.append(f'<line x1="{left}" y1="{py(sgn*b):.1f}" x2="{right}" y2="{py(sgn*b):.1f}" stroke="#a0522d" stroke-dasharray="{dash}"/>')
    for k, v, ok in lags:
        colour = "#216e73" if ok else "#9bbfbc"
        out.append(f'<line x1="{px(k):.1f}" y1="{py(0):.1f}" x2="{px(k):.1f}" y2="{py(v):.1f}" stroke="{colour}" stroke-width="2"><title>lag {k}: {v:.3f}</title></line>')
        out.append(f'<circle cx="{px(k):.1f}" cy="{py(v):.1f}" r="2.5" fill="{colour}"/>')
    for k in sorted({1, L} | {round(L * i / 4) for i in range(1, 4)}):
        if 1 <= k <= L: out.append(f'<text x="{px(k):.1f}" y="{bottom+22}" text-anchor="middle" class="tick-label">{k}</text>')
    out.append("</svg>")
    note = ("Dashed: per-lag 95% band ±1.96/√n; dotted: family-wise band; pale stems: lags beyond n/4 (poorly supported). "
            f"n = {c['n']} {g['granularity']} periods.")
    return ('<figure class="chart"><h4>' + escape(title) + "</h4>" + "".join(out) + '<div class="axis-captions"><p><strong>X:</strong> lag ('
            + escape(g["granularity"]) + 's)</p><p><strong>Y:</strong> ' + ("autocorrelation" if which == "acf" else "partial autocorrelation")
            + "</p></div><figcaption>" + escape(note) + "</figcaption></figure>")


def blocks(d):
    ts = d.get("time_series") or {}
    for si, entry in enumerate(ts.get("series", [])):
        head = []
        if entry.get("by"):
            head.append(f"Split by {entry['by']}: {entry['groups_analysed']} of {entry['groups_total']} groups analysed (top {entry['top_n']} by row count); "
                        f"{entry['rows_in_other_groups']:,} rows in other groups and {entry['rows_missing_key']:,} rows with a missing key are not analysed.")
        for s in entry["groups"]:
            charted = [g for g in s["granularities"] if g["granularity"] in s["charted"]]
            yield name(entry, s), head, [process_table(s), sparsity_table(s), signal_table(s)], charted, s
            head = []


def temporal_html(d):
    ts = d.get("time_series") or {}
    if not ts.get("series"): return ""
    out = ['<section id="temporal-structure"><h2>Temporal structure</h2><p>' + escape(INTRO) + "</p>"]
    for title, head, tables, charted, s in blocks(d):
        out += ["<h3>" + escape(title) + "</h3>"] + ["<p>" + escape(h) + "</p>" for h in head] + [html_table(t) for t in tables]
        if charted: out.append("<p>Charts: the two granularities with the most supported lags outside the family band (then larger n).</p>")
        for g in charted: out += [stem(g, "acf"), stem(g, "pacf")]
        for g in s["granularities"]:
            if g["wavelength"]["values"]["status"] == "computed":
                out += ["<details><summary>" + escape(g["granularity"].capitalize()) + " lag table</summary>", html_table(lag_table(g)), "</details>"]
    out += ["<details><summary>Rules</summary><ul>" + "".join(f"<li><strong>{escape(k)}</strong>: {escape(v)}</li>" for k, v in ts["rules"].items()) + "</ul></details></section>"]
    return "".join(out)


def temporal_markdown(d):
    ts = d.get("time_series") or {}
    if not ts.get("series"): return []
    lines = ["## Temporal structure", "", INTRO, ""]
    for title, head, tables, charted, s in blocks(d):
        lines += ["### " + title, ""] + [h + "\n" for h in head] + [markdown_table(t) for t in tables]
        for g in charted: lines += [stem(g, "acf"), "", stem(g, "pacf"), ""]
        for g in s["granularities"]:
            if g["wavelength"]["values"]["status"] == "computed":
                lines += ["<details><summary>" + g["granularity"].capitalize() + " lag table</summary>", "", markdown_table(lag_table(g)), "</details>", ""]
    lines += ["<details><summary>Rules</summary>", ""] + [f"- **{k}**: {v}" for k, v in ts["rules"].items()] + ["", "</details>", ""]
    return lines
