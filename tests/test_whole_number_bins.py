"""Spec 028: whole-number histogram bins.

A column whose finite values are all whole numbers (mana values, counts, string
lengths) gets bins that hold whole runs of values, labelled inclusively, so a hover
title never reads "6 to 7.2" for data that can only be 6 or 7. Any genuine fraction
keeps the original real-valued bins. Violating fixtures sit beside clean decoys.
"""
import re

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
    assert extra == {"whole_number_bins": {"width": 2}}
    assert not any(FRACTIONAL_LABEL.search(d["label"]) for d in data)
    assert data[0]["label"] == "0 to 1" and data[-1]["label"] == "16"
    assert_exact_partition(nums, data)


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
    assert whole_ticks(-0.5, 100.5) == [0, 25, 50, 75, 100]


def test_beyond_exact_float_integers_keeps_real_valued_bins():
    # Above 2**53 every float is integral, so integrality says nothing about the data.
    data, extra = histogram_bins([1e300, 2e300, 5e300])
    assert extra == {} and sum(d["count"] for d in data) == 3
    data, extra = histogram_bins([0, 2**53])
    assert extra["whole_number_bins"]["width"] > 1 and sum(d["count"] for d in data) == 2
