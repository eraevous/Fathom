"""Spec011 time series: synthetic series with known structure, and silent decoys."""

from datetime import datetime, timedelta
import math
import random
import sys

import pytest

from fathom.config import validate_config
from fathom.renderers import render_html, render_markdown
from fathom.timeseries import pacf

BASE = datetime(2024, 1, 1)  # fixed; no runtime dates


def daily(values, col="amount", skip=()):
    lines = ["when," + col]
    for i, v in enumerate(values):
        if i not in skip:
            lines.append(f"{(BASE + timedelta(days=i)).date().isoformat()},{v}")
    return "\n".join(lines) + "\n"


def declare(value="amount", grains=("day",), **extra):
    return {"time_series": [{"time": "when", "value": value, "granularities": list(grains), **extra}]}


def series(doc, i=0, g=0):
    return doc["time_series"]["series"][i]["groups"][g]


def grain(s, name):
    return next(x for x in s["granularities"] if x["granularity"] == name)


def signal(s, name):
    return next(x for x in s["signals"] if x["signal"].startswith(name))


def ts_findings(doc, kind=None):
    return [f for f in doc["findings"] if f["generator"] == "rule:timeseries-v1" and (kind is None or f["kind"] == kind)]


def test_pure_periodic_series_peaks_at_its_period(make_profile):
    pattern = [10, 14, 18, 14, 10, 6, 2]
    d = make_profile(daily([pattern[i % 7] for i in range(140)]), declare()).document
    g = grain(series(d), "day")
    c = g["wavelength"]["values"]
    assert c["status"] == "computed" and c["n"] == 140 and c["dominant_lags"][0]["lag"] == 7
    assert c["lags"][6]["acf"] > 0.9 and g["wavelength"]["calendar_lags"][0]["status"] == "supported"
    assert signal(series(d), "repeating cycle")["present"] == ["day"]
    assert any("peaks at lag 7" in f["message"] for f in ts_findings(d, "question"))


def test_white_noise_has_no_significant_structure(make_profile):
    rng = random.Random(1)
    d = make_profile(daily([f"{rng.gauss(50, 5):.4f}" for _ in range(300)]), declare()).document
    s = series(d)
    assert grain(s, "day")["wavelength"]["values"]["signal"] == "absent"
    assert signal(s, "autocorrelation in values")["absent"] == ["day"]
    assert signal(s, "repeating cycle")["present"] == []
    assert not any(f["rule"] == "dominant_cycle" for f in ts_findings(d))


def test_white_noise_family_wise_false_positive_rate_is_near_five_percent():
    from fathom.timeseries import correlogram
    hits = 0
    for seed in range(1, 201):
        rng = random.Random(seed)
        hits += correlogram([rng.gauss(50, 5) for _ in range(300)], 28)["signal"] == "present"
    assert hits <= 16  # 8 of 200 observed; Bonferroni targets <= 5%


def test_intermittent_demand_frequency_amplitude_duration(make_profile):
    values = [5 if i % 3 == 0 else 0 for i in range(60)]
    values[30] = 11
    g = grain(series(make_profile(daily(values), declare()).document), "day")
    assert g["frequency"]["zero_periods"] == 40 and g["frequency"]["zero_share"] == round(40 / 60, 10)
    assert g["frequency"]["adi"] == 3 and g["frequency"]["inter_event_interval"]["max"] == 3
    assert g["amplitude"]["nonzero"]["median"] == 5 and g["amplitude"]["nonzero"]["max"] == 11
    assert g["amplitude"]["cv2"] == pytest.approx(1.71 / 5.3 ** 2, abs=1e-9)  # nineteen 5s and one 11: pvar 1.71, mean 5.3
    assert g["duration"]["longest_zero_run"] == 2 and g["duration"]["zero_runs"]["n"] == 20
    assert g["duration"]["longest_nonzero_run"] == 1


def test_constant_series_is_undefined_and_warned(make_profile):
    s = series(make_profile(daily([4] * 40), declare()).document)
    c = grain(s, "day")["wavelength"]["values"]
    assert c["status"] == "undefined" and "constant" in c["note"]
    assert signal(s, "autocorrelation in values")["undefined"] == ["day"]
    assert signal(s, "autocorrelation in values")["insufficient evidence"] == []
    assert "day values" in signal(s, "autocorrelation in values")["notes"]


def test_short_series_is_insufficient(make_profile):
    s = series(make_profile(daily(list(range(1, 11))), declare()).document)
    c = grain(s, "day")["wavelength"]["values"]
    assert c["status"] == "insufficient" and "10 observed periods" in c["note"] and "lags" not in c


def test_missing_periods_are_distinguished_from_explicit_zeros(make_profile):
    values = [3 + (i % 5) for i in range(40)]
    for i in (20, 21, 22): values[i] = 0
    d = make_profile(daily(values, skip=range(10, 15)), declare()).document
    s = series(d); g = grain(s, "day")
    assert (g["periods_in_span"], g["missing_periods"], g["frequency"]["zero_periods"], g["observed_periods"]) == (40, 5, 3, 35)
    assert s["observation_process"]["explicit_zero_rows"] == 3
    assert g["duration"]["longest_zero_run"] == 3  # the missing block ends runs; it is not counted as zeros
    q = [f for f in ts_findings(d, "question") if f["rule"] == "observation_gaps"]
    assert len(q) == 1 and "5 day periods are missing observations" in q[0]["message"]


def hourly_events():
    lines = ["stamp,kind"]
    for h in range(24 * 40):
        for k in range(1 + (h % 24 >= 8) * 3 + (h // 24 % 7 == 5)):
            lines.append(f"{(BASE + timedelta(hours=h, minutes=7 * k)).isoformat(sep=' ')},x")
    return "\n".join(lines) + "\n", {"time_series": [{"time": "stamp", "value": None, "granularities": ["auto"]}]}


def test_event_counts_from_timestamps_with_hour_and_day(make_profile):
    s = make_profile(*hourly_events()).document["time_series"]["series"][0]["groups"][0]
    assert s["mode"] == "events" and [g["granularity"] for g in s["granularities"]] == ["hour", "day", "week", "month"]
    h = grain(s, "hour")
    assert h["periods_in_span"] == 960 and h["no_recorded_event_periods"] == 0
    assert h["wavelength"]["calendar_lags"][0]["acf"] > 0.9 and h["wavelength"]["values"]["dominant_lags"][0]["lag"] == 24
    assert grain(s, "week")["wavelength"]["values"]["status"] == "insufficient"


def test_by_split_limits_to_top_n_groups(make_profile):
    lines = ["when,amount,shop"]
    for gi, size in enumerate([40, 39, 38, 10, 5, 3]):
        for i in range(size):
            lines.append(f"{(BASE + timedelta(days=i)).date().isoformat()},{i % 4},s{gi}")
    lines.append("2024-01-02,1,")
    d = make_profile("\n".join(lines) + "\n", declare(by="shop", top_n=3)).document
    entry = d["time_series"]["series"][0]
    assert [g["group"] for g in entry["groups"]] == ["s0", "s1", "s2"]
    assert (entry["groups_total"], entry["rows_in_other_groups"], entry["rows_missing_key"]) == (6, 18, 1)
    assert "3 of 6 groups analysed" in render_markdown(make_profile("\n".join(lines) + "\n", declare(by="shop", top_n=3)))


def test_pacf_durbin_levinson_on_ar1_acf():
    assert pacf([0.5 ** k for k in range(1, 6)]) == pytest.approx([0.5, 0, 0, 0, 0], abs=1e-12)


def test_spectral_degrades_without_scipy(make_profile, monkeypatch):
    monkeypatch.setitem(sys.modules, "scipy.signal", None)
    pattern = [1, 5, 9, 5]
    d = make_profile(daily([pattern[i % 4] for i in range(60)]), declare()).document
    assert grain(series(d), "day")["wavelength"]["spectral"] == {"status": "not computed", "reason": "stats extra (scipy) not installed"}
    assert d["time_series"]["dependencies"]["scipy"].startswith("unavailable")


def test_report_has_temporal_section_with_stem_plots(make_profile):
    result = make_profile(*hourly_events())
    assert result.document["time_series"]["series"][0]["groups"][0]["charted"] == ["hour", "day"]
    html, md = render_html(result), render_markdown(result)
    assert '<section id="temporal-structure" class="temporal-tables"><h2>Temporal structure</h2>' in html and "## Temporal structure" in md
    assert html.count('data-kind="stem"') == 4  # ACF + PACF for two granularities
    assert "Sparsity dimensions × granularities" in html and "Insufficient evidence" in html


def test_undeclared_series_asks_one_question(make_profile):
    d = make_profile(daily([i % 5 for i in range(40)])).document
    q = [f for f in ts_findings(d) if f["rule"] == "time_series_undeclared"]
    assert len(q) == 1 and q[0]["kind"] == "question" and d["time_series"]["series"] == []
    assert q[0]["message"].startswith("when (40 distinct days): would counts of rows over time (time_series with value: null)")
    assert "totals of amount" in q[0]["message"]


def test_undeclared_pure_timestamps_offer_event_counts(make_profile):
    d = make_profile("stamp\n" + "".join(f"{(BASE + timedelta(hours=h)).isoformat(sep=' ')}\n" for h in range(35))).document
    q = d["time_series"]["question"]
    assert q["temporal_columns"] == [{"column": "stamp", "granularity": "hour", "distinct_periods": 35}] and q["numeric_columns"] == []


def test_undeclared_question_quiet_on_few_periods_and_skips_identifier_like(make_profile):
    few = make_profile(daily([1, 2, 3] * 3)).document  # 9 days < 30
    assert few["time_series"]["question"] is None
    lines = ["when,order_id,amount"] + [f"{(BASE + timedelta(days=i)).date().isoformat()},{1000 + i},{i % 3}" for i in range(40)]
    q = make_profile("\n".join(lines) + "\n").document["time_series"]["question"]
    assert q["numeric_columns"] == ["amount"]  # order_id: integers, all distinct


def test_inter_event_interval_does_not_span_missing_periods(make_profile):
    values = [2 + i % 3 for i in range(40)]
    g = grain(series(make_profile(daily(values, skip=range(10, 25)), declare()).document), "day")  # gaps only, no zeros
    assert g["frequency"]["zero_periods"] == 0 and g["frequency"]["adi"] == 1
    assert g["frequency"]["intervals_spanning_missing"] == 1 and g["frequency"]["inter_event_interval"]["max"] == 1


def test_zero_and_burst_signals_need_thirty_periods(make_profile):
    s = series(make_profile(daily([0, 3, 4] * 8 + [0]), declare()).document)  # 25 periods
    for name in ("zero periods", "bursts"):
        assert signal(s, name)["insufficient evidence"] == ["day"] and signal(s, name)["present"] == []


def test_decoys_stay_silent(make_profile):
    no_time = make_profile("a,b\n1,2\n3,4\n5,6\n").document
    assert not ts_findings(no_time) and no_time["time_series"]["question"] is None
    declared = make_profile(daily(list(range(40))), declare()).document
    assert not [f for f in ts_findings(declared) if f["rule"] == "time_series_undeclared"]
    assert "temporal-structure" not in render_html(make_profile("a,b\n1,2\n3,4\n"))


@pytest.mark.parametrize("bad", [
    {"time_series": [{"time": "nope", "value": None}]},
    {"time_series": [{"time": "when", "value": "amount", "granularities": ["minute"]}]},
    {"time_series": [{"time": "when", "value": "when"}]},
    {"time_series": [{"time": "when", "max_lag": 0}]},
    {"time_series": [{"time": "when", "colour": "x"}]},
])
def test_invalid_declarations_are_refused(bad):
    with pytest.raises(ValueError):
        validate_config(bad, ["when", "amount"])


def test_alternating_days_lag_one_is_not_estimable(make_profile):
    values = [1 + (i // 2) % 3 for i in range(60)]
    d = make_profile(daily(values, skip=range(1, 60, 2)), declare(max_lag=1)).document
    s = series(d); c = grain(s, "day")["wavelength"]["values"]
    assert c["n"] == 30 and c["lags"][0]["pairs"] == 0 and c["lags"][0]["acf"] is None
    assert c["signal"] == "not estimable" and "not the same as near zero" in c["note"]
    sig = signal(s, "autocorrelation in values")
    assert sig["not estimable"] == ["day"] and sig["absent"] == [] and sig["present"] == []


def test_random_missing_still_recovers_known_period(make_profile):
    pattern = [10, 14, 18, 14, 10, 6, 2]
    rng = random.Random(5)
    skip = {i for i in range(280) if rng.random() < 0.2}
    c = grain(series(make_profile(daily([pattern[i % 7] for i in range(280)], skip=skip), declare()).document), "day")["wavelength"]["values"]
    assert not c["complete"] and c["not_estimable_lags"] == []
    lag7 = c["lags"][6]
    assert lag7["pairs"] < 273 and lag7["band"] == round(1.96 / math.sqrt(lag7["pairs"]), 10)
    assert c["dominant_lags"][0]["lag"] == 7 and c["signal"] == "present"


def test_weekly_default_reaches_52_when_span_allows(make_profile):
    values = [5 + (i // 7) % 52 for i in range(7 * 110)]
    g = grain(series(make_profile(daily(values), declare(grains=("week",))).document), "week")
    assert g["wavelength"]["values"]["max_lag"] == 52 and g["wavelength"]["calendar_lags"][0]["acf"] is not None
    short = grain(series(make_profile(daily(values[:7 * 60]), declare(grains=("week",))).document), "week")
    assert short["wavelength"]["calendar_lags"][0]["status"] == "not evaluated at max_lag 26"
