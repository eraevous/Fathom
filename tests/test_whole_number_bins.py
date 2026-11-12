"""Spec 028: whole-number histogram bins.

A column whose finite values are all whole numbers (mana values, counts, string
lengths) gets bins that hold whole runs of values, labelled inclusively, so a hover
title never reads "6 to 7.2" for data that can only be 6 or 7. Any genuine fraction
keeps the original real-valued bins. Violating fixtures sit beside clean decoys.
"""
import re

import pytest

from fathom.charts import svg_chart, whole_ticks
from fathom.univariate import histogram, histogram_bins, numeric_profile

FRACTIONAL_LABEL = re.compile(r"\d\.\d")


def members(data):
    """Expand inclusive whole-number labels into the set of values each bin claims."""
    out = []
    for d in data:
        parts = d["label"].split(" to ")
        first, last = int(parts[0]), int(parts[-1])
        out.append(range(first, last + 1))
    return out


def assert_exact_partition(nums, data):
    claimed = members(data)
    flat = [v for r in claimed for v in r]
    assert len(flat) == len(set(flat)), "bins overlap"
    assert flat == list(range(min(nums), max(nums) + 1)), "bins leave a gap or overrun the range"
    for r, d in zip(claimed, data):
        assert d["count"] == sum(1 for x in nums if x in r)
        assert d["low"] == r[0] - 0.5 and d["high"] == r[-1] + 0.5


def test_violation_integer_column_no_longer_gets_fractional_labels():
    # The reported case: mana values 0..16. Before spec 028 these read "0 to 1.6", "6.4 to 8".
    nums = [0] * 30 + [1] * 40 + [2] * 50 + [3] * 45 + [5] * 20 + [6] * 12 + [7] * 9 + [16]
    data, extra = histogram_bins(nums)
    assert not any(FRACTIONAL_LABEL.search(d["label"]) for d in data + extra["tail"])
    # 17 values > 16 bars, but one row (0.5%) lies outside 0..15: one bar per value plus a tail callout.
    assert [d["label"] for d in data] == [str(v) for v in range(16)]
    assert extra["whole_number_bins"] == {"width": 1, "core": [0, 15], "tail_rows": 1}
    assert extra["tail"] == [{"label": "16", "low": 15.5, "high": 16.5, "count": 1, "side": "high"}]
    assert sum(d["count"] for d in data + extra["tail"]) == len(nums)


def test_sixteen_values_or_fewer_get_one_bar_per_value():
    data, extra = histogram_bins(list(range(16)) * 3)
    assert len(data) == 16 and extra == {"whole_number_bins": {"width": 1}}


def test_dense_wide_range_falls_back_to_at_most_sixteen_whole_bars():
    # Decoy for the tail rule: 0..49 evenly; no 16-value window holds 95% of rows.
    data, extra = histogram_bins(list(range(50)))
    assert extra == {"whole_number_bins": {"width": 4}} and len(data) == 13 and "tail" not in extra
    assert_exact_partition(list(range(50)), data)


def test_tail_just_over_five_percent_is_not_a_callout():
    nums = [1] * 300 + [2] * 50 + list(range(40, 60)) + [200]  # 21 of 371 rows (5.7%) outside 1..16
    _, extra = histogram_bins(nums)
    assert "tail" not in extra and extra["whole_number_bins"]["width"] > 1


def test_low_and_high_tails_and_ranges():
    nums = [-40] + [v for v in range(10, 26) for _ in range(20)] + [60, 61, 70, 90, 95, 99, 400]
    data, extra = histogram_bins(nums)
    assert extra["whole_number_bins"]["core"] == [10, 25]
    low = [d for d in extra["tail"] if d["side"] == "low"]
    high = [d for d in extra["tail"] if d["side"] == "high"]
    assert low == [{"label": "-40", "low": -40.5, "high": -39.5, "count": 1, "side": "low"}]
    # Seven distinct high values > 6: at most 4 non-empty inclusive ranges.
    assert 1 <= len(high) <= 4 and sum(d["count"] for d in high) == 7
    assert sum(d["count"] for d in data + extra["tail"]) == len(nums)


def test_declared_bins_are_a_maximum_without_tail_logic():
    nums = [0] * 30 + [1] * 40 + [16]
    data, extra = histogram_bins(nums, bins=10)
    assert "tail" not in extra and len(data) <= 10 and extra["whole_number_bins"]["width"] == 2


def test_clean_decoy_genuine_fractions_keep_real_valued_bins():
    nums = [1, 2, 2.5, 3, 4, 5]
    data, extra = histogram_bins(nums)
    assert extra == {}
    # sqrt(6) -> 3 equal-width real bins; the fractional edge is kept, not rounded.
    assert [d["label"] for d in data] == ["1 to 2.3333", "2.3333 to 3.6667", "3.6667 to 5"]
    assert sum(d["count"] for d in data) == len(nums)


def test_small_span_gives_one_bar_per_value_and_respects_declared_maximum():
    nums = [1, 1, 2, 3, 3, 3]
    data, extra = histogram_bins(nums, bins=10)
    assert [d["label"] for d in data] == ["1", "2", "3"] and [d["count"] for d in data] == [2, 1, 3]
    assert extra["whole_number_bins"]["width"] == 1
    data, _ = histogram_bins(list(range(100)), bins=4)
    assert len(data) == 4 and [d["label"] for d in data] == ["0 to 24", "25 to 49", "50 to 74", "75 to 99"]


def test_negative_and_boundary_values_land_in_exactly_one_bin():
    nums = [-7, -7, -3, -1, 0, 0, 4, 9, 9, 9]
    data, _ = histogram_bins(nums, bins=3)
    assert_exact_partition(nums, data)
    # Span 17 in at most 3 bins -> width 6; the last bin is truncated at the maximum.
    assert [d["label"] for d in data] == ["-7 to -2", "-1 to 4", "5 to 9"]
    # The minimum sits on the first bin's lower end and the maximum on the last bin's upper end.
    assert [d["count"] for d in data] == [3, 4, 3]


def test_constant_and_float_typed_whole_values():
    data, extra = histogram_bins([5, 5, 5])
    assert data == [{"label": "5", "low": 4.5, "high": 5.5, "count": 3}] and extra["whole_number_bins"]["width"] == 1
    data, extra = histogram_bins([2.0, 3.0, 3.0])
    assert [d["label"] for d in data] == ["2", "3"] and extra


def test_large_whole_numbers_stay_exact():
    nums = [10**12, 10**12 + 1, 10**12 + 7]
    data, _ = histogram_bins(nums, bins=2)
    assert_exact_partition(nums, data)


def test_log_scale_never_uses_whole_number_bins():
    # Powers of ten give whole log10 values; the log view must still use real-valued bins.
    ch = histogram([0.0, 1.0, 2.0, 2.0], "t", "x (log scale)", scale="log10")
    assert "whole_number_bins" not in ch


def test_profile_statistics_and_stored_values_unchanged():
    stats, charts = numeric_profile([str(v) for v in [1, 2, 2, 3, 9]], "mana", None)
    assert stats["integers"] == 5 and stats["percentiles"]["50"] == 2
    hist = next(c for c in charts if c["kind"] == "histogram")
    assert hist["whole_number_bins"] and sum(d["count"] for d in hist["data"]) == 5
    box = next(c for c in charts if c["kind"] == "box")
    assert box["box"]["min"] == 1 and box["box"]["max"] == 9


def test_svg_hover_titles_ticks_and_disclosure():
    stats, charts = numeric_profile([str(v) for v in [0, 1, 1, 2, 3, 6, 7, 7, 12, 16]], "mana", None)
    svg = svg_chart(next(c for c in charts if c["kind"] == "histogram"))
    titles = re.findall(r"<rect[^>]*><title>([^<]*)</title>", svg)
    assert titles and not any(FRACTIONAL_LABEL.search(t) for t in titles)
    ticks = re.findall(r'class="tick-label"[^>]*>([^<]*)<', svg)
    assert ticks and not any(FRACTIONAL_LABEL.search(t) for t in ticks)
    assert "Whole-number values:" in svg
    # Decoy: a fractional column keeps its real-valued titles and gets no whole-number note.
    _, charts = numeric_profile(["0.5", "1.25", "3", "7.75"], "x", None)
    assert "Whole-number values:" not in svg_chart(next(c for c in charts if c["kind"] == "histogram"))


def test_whole_ticks():
    assert whole_ticks(-0.5, 3.5) == [0, 1, 2, 3]
    assert whole_ticks(4.5, 4.5 + 1) == [5]
    assert whole_ticks(-0.5, 100.5) == [0, 20, 40, 60, 80, 100]
    # Even 1/2/5 x 10^k steps, never 0, 4, 8, 11, 15.
    assert whole_ticks(-0.5, 15.5) == [0, 5, 10, 15]
    assert whole_ticks(-40.5, 99.5) == [-40, -20, 0, 20, 40, 60, 80]


def test_beyond_exact_float_integers_keeps_real_valued_bins():
    # Above 2**53 every float is integral, so integrality says nothing about the data.
    data, extra = histogram_bins([1e300, 2e300, 5e300])
    assert extra == {} and sum(d["count"] for d in data) == 3
    # Revised boundary (#45 review): half-integer edges are exact only below 2**52.
    data, extra = histogram_bins([0, 2**52 - 1])
    assert extra["whole_number_bins"]["width"] > 1 and sum(d["count"] for d in data) == 2
    data, extra = histogram_bins([0, 2**53])
    assert extra == {} and sum(d["count"] for d in data) == 2


def test_tail_callout_inset_table_and_note():
    nums = [str(v) for v in [0] * 30 + [1] * 40 + [2] * 50 + [3] * 45 + [5] * 20 + [16]]
    _, charts = numeric_profile(nums, "mana", None)
    hist = next(c for c in charts if c["kind"] == "histogram")
    svg = svg_chart(hist)
    assert 'class="tail-callout"' in svg and "<title>16: 1 (tail)</title>" in svg
    assert "Tail outside 0 to 15" in svg
    assert "16 (tail callout)" in svg  # chart-values table row
    assert "1 row outside that range is shown in the tail callout: 16 (1 row)" in svg
    assert hist["bin_rule"].startswith("whole-number columns: one bar per value up to 16")


def test_inset_moves_below_the_axis_when_both_corners_are_crowded():
    nums = [str(v) for v in [v for v in range(16) for _ in range(40)] + [99]]
    _, charts = numeric_profile(nums, "flat", None)
    svg = svg_chart(next(c for c in charts if c["kind"] == "histogram"))
    assert 'viewBox="0 0 560 270"' not in svg and 'y="282"' in svg


def test_report_level_rule_discloses_both_layouts():
    from fathom.univariate import report_bin_rule
    rule = report_bin_rule()
    assert rule.startswith("sqrt(n) rounded up, capped at 10") and "whole-number columns" in rule
    assert "at most 6 whole-value bins" in report_bin_rule(6)


# ---------------------------------------------------------------- repairs 2026-11-12 (bot findings on #45)

def test_bars_are_drawn_at_their_bin_boundaries():
    """Codex 4544048070 / Copilot 4544920908: a truncated last bin made bars (drawn by index) disagree with labels."""
    import re
    from fathom.charts import svg_chart
    from fathom.univariate import histogram
    chart = histogram(list(range(7)), 't', 'x', bins=3)
    # Bins keep the spec's exact, non-overrunning partition; the narrower last bin is drawn narrower.
    assert [d['label'] for d in chart['data']] == ['0 to 2', '3 to 5', '6']
    assert [d['high'] - d['low'] for d in chart['data']] == [3, 3, 1]
    # In the SVG each bar spans exactly its bin's interval on the axis.
    svg = svg_chart(chart)
    bars = [(float(x), float(w)) for x, w in re.findall(r'<rect x="([\d.]+)" y="[^"]+" width="([\d.]+)" height="[^"]+" fill="[^"]+"><title>', svg)]
    assert len(bars) == 3
    left, right = 65, 515
    lo, hi = chart['data'][0]['low'], chart['data'][-1]['high']
    for (x, w), d in zip(bars, chart['data']):
        assert x == pytest.approx(left + (right - left) * (d['low'] - lo) / (hi - lo))
        assert x + w + 2 == pytest.approx(left + (right - left) * (d['high'] - lo) / (hi - lo))


def test_half_integer_geometry_stays_representable_near_2_52():
    """Copilot 4544920927: at 2**52 a half-integer edge rounds, collapsing the last bin."""
    from fathom.univariate import histogram
    big = histogram([2 ** 52, 2 ** 52 + 1, 2 ** 52 + 2], 't', 'x')
    assert 'whole_number_bins' not in big
    assert all(d['low'] < d['high'] for d in big['data'])
    below = histogram([2 ** 52 - 3, 2 ** 52 - 2, 2 ** 52 - 1], 't', 'x')
    assert 'whole_number_bins' in below
    assert all(d['low'] < d['high'] for d in below['data'])
    assert [d['high'] - d['low'] for d in below['data']] == [1, 1, 1]


def test_tail_inset_fits_inside_the_svg():
    """Copilot 4544920864: a 16-value core near 10**15 produced a 661-unit inset inside a 560-unit SVG."""
    import re
    from fathom.charts import svg_chart
    from fathom.univariate import histogram
    base = 10 ** 15
    nums = [base + v for v in range(16) for _ in range(3)] + [base + 100000]
    chart = histogram(nums, 'Big counts', 'x')
    assert chart.get('tail')
    svg = svg_chart(chart)
    width = float(re.search(r'viewBox="0 0 ([\d.]+) ', svg).group(1))
    inset = re.search(r'<g class="tail-callout"><rect x="([\d.]+)" y="[\d.]+" width="([\d.]+)"', svg)
    x0, w = float(inset.group(1)), float(inset.group(2))
    assert 0 <= x0 and x0 + w <= width, (x0, w, width)
    group = svg[svg.index('<g class="tail-callout">'):svg.index('</g>', svg.index('<g class="tail-callout">'))]
    for text in re.findall(r'<text x="[\d.]+" y="[\d.]+" class="tick-label">([^<]*)</text>', group):
        assert 13 * len(text) <= w, text
    assert str(base) in svg  # the full core range stays available (title tooltip / note)


def test_pdf_histogram_uses_boundary_bar_spans(make_profile, monkeypatch):
    """The PDF renderer places histogram bars with the same boundary geometry as the SVG (#45 review)."""
    pytest.importorskip('reportlab')
    import fathom.charts as charts
    from fathom.exports import export_bundle
    from fathom.univariate import histogram
    calls = []
    real = charts.bar_spans
    monkeypatch.setattr(charts, 'bar_spans', lambda data, x0, width: calls.append((x0, width, [d['label'] for d in data])) or real(data, x0, width))
    p = make_profile('v\n' + '\n'.join(str(i) for i in range(7)) + '\n', {'bins': 3})
    files, _ = export_bundle(p, ['pdf'])
    assert files['report.pdf'].startswith(b'%PDF-')
    assert (55, 390, ['0 to 2', '3 to 5', '6']) in calls
    spans = real(histogram(list(range(7)), 't', 'x', bins=3)['data'], 55, 390)
    assert [round(w / spans[0][1], 6) for _, w in spans] == [1, 1, round(1 / 3, 6)]


# ---------------------------------------------------------------- degenerate-geometry sweep (Codex 4551700095)

SWEEP = [
    ('constant fractional', [2.5] * 10, None),
    ('constant whole', [3] * 10, None),
    ('single value', [7], None),
    ('two distinct', [1, 2], None),
    ('negative only', [-5, -3, -1, -2], None),
    ('mixed sign spanning 0', [-3, -1, 0, 2, 5], None),
    ('tiny range 1e-12', [1 + i * 1e-13 for i in range(10)], None),
    ('whole just below 2^52', [2 ** 52 - 5, 2 ** 52 - 3, 2 ** 52 - 1], None),
    ('at/above 2^52', [2 ** 52, 2 ** 52 + 1, 2 ** 52 + 3], None),
    ('non-divisible span, bins=3', list(range(7)), 3),
    ('non-divisible span, default cap', list(range(23)), None),
    ('huge outlier, tail inset', [v for v in range(16) for _ in range(3)] + [10 ** 6], None),
    ('declared bins=1', [1, 2, 3, 4], 1),
    ('bins > distinct (whole)', [1, 2, 3], 10),
    ('bins > distinct (fractional)', [0.5, 1.5], 10),
]


@pytest.mark.parametrize('name,nums,bins', SWEEP, ids=[s[0] for s in SWEEP])
def test_degenerate_histograms_draw_valid_bars_in_svg_and_pdf(name, nums, bins):
    import math
    from fathom.charts import bar_layout
    chart = histogram(nums, 't', 'x', bins=bins)
    data, tail = chart['data'], chart.get('tail', [])
    assert sum(d['count'] for d in data) + sum(d['count'] for d in tail) == len(nums)
    svg = svg_chart(chart)
    bars = re.findall(r'<rect x="([^"]+)" y="[^"]+" width="([^"]+)" height="[^"]+" fill="[^"]+"><title>([^<]*): (\d+)</title></rect>', svg)
    assert len(bars) == len(data), (name, len(bars), len(data))
    for (x, w, label, count), d in zip(bars, data):
        x, w = float(x), float(w)
        assert math.isfinite(x) and math.isfinite(w) and w > 0.5, (name, x, w)
        assert 65 - 1e-9 <= x and x + w <= 515 + 1e-9, (name, x, w)
        assert label == d['label'].replace('&', '&amp;') and int(count) == d['count']
    # PDF uses the same layout over its 55..445 plot box; a fallback is always disclosed in the figure note.
    spans, note = bar_layout(data, 55, 390)
    assert (note is None) == (name not in {'constant fractional', 'tiny range 1e-12'}), (name, note)
    if note:
        assert note in svg
    assert len(spans) == len(data)
    for x, w in spans:
        assert math.isfinite(x) and math.isfinite(w) and w > 0 and 55 - 1e-9 <= x and x + w <= 445 + 1e-9, (name, x, w)


@pytest.mark.parametrize('name,nums,bins', SWEEP + [('all missing', [], None)], ids=[s[0] for s in SWEEP] + ['all missing'])
def test_degenerate_histograms_export_smoke(make_profile, name, nums, bins):
    pytest.importorskip('reportlab')
    pytest.importorskip('pptx')
    from fathom.exports import export_bundle
    from fathom.renderers import render_html, render_markdown
    rows = nums or [None, None, None]  # all missing: v is blank beside a second column
    text = 'v,w\n' + ''.join(('' if v is None else repr(v) if isinstance(v, float) else str(v)) + f',{i}\n' for i, v in enumerate(rows))
    p = make_profile(text, {'bins': bins} if bins else None)
    render_html(p), render_markdown(p)
    files, _ = export_bundle(p, ['pdf', 'pptx'])
    assert files['report.pdf'].startswith(b'%PDF-') and files['report.pptx'][:2] == b'PK'
