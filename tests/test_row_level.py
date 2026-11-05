"""Spec010 row-level and temporal structure: violating fixtures and clean decoys."""

import pytest

from fathom.config import validate_config
from fathom.parsing import parse_datetime


def rows_findings(doc, kind="observation"):
    return [f for f in doc["findings"] if f["generator"] == "rule:rows-v1" and f["kind"] == kind]


def by_rule(doc, rule):
    return [f for f in rows_findings(doc) if f["rule"] == rule]


def test_blank_and_numeric_blank_rows_with_positions(make_profile):
    body = "name,a,b\nx,1,2\n,,\ny,,\nz,3,\n,,\nw,4,5\n"
    d = make_profile(body).document
    assert d["row_structure"]["blank_rows"] == {"count": 2, "share": 2 / 6, "positions": [2, 5]}
    assert d["row_structure"]["numeric_blank_rows"]["positions"] == [3]  # z has a=3: decoy
    assert "2 of 6 rows have no value in any column (1-based rows 2, 5)" in by_rule(d, "blank_rows")[0]["message"]
    assert [f["rule"] for f in rows_findings(d, "question")] == ["blank_rows", "numeric_blank_rows"]


def test_partly_blank_rows_are_quiet(make_profile):
    d = make_profile("name,a,b\nx,1,\ny,,2\nz,3,4\n").document
    assert d["row_structure"]["blank_rows"]["count"] == 0 and d["row_structure"]["numeric_blank_rows"]["count"] == 0
    assert not rows_findings(d)


def test_duplicate_rows_gain_positions(make_profile):
    d = make_profile("a,b\n1,x\n2,y\n1,x\n1,x\n").document
    dup = next(f for f in d["findings"] if f["id"] == "duplicates")
    assert dup["message"].endswith("Repeating rows (1-based): 3, 4.")
    assert d["row_structure"]["duplicate_rows"] == {"count": 2, "positions": [3, 4]}


def keyed(sizes):
    lines = ["person,alias,group,period,score"]
    for p, size in enumerate(sizes):
        for t in range(size):
            lines.append(f"P{p:02d},A{p:02d},{'g' + str(p % 3)},{t},{(p * 7 + t * 3) % 11}")
    return "\n".join(lines) + "\n"


def test_regular_multiplicity_reports_key_and_within_key_constants(make_profile):
    d = make_profile(keyed([3] * 12)).document
    keys = d["row_structure"]["repeated_keys"]
    assert len(keys) == 1  # alias has the identical partition: same grouping, not a second key
    key = keys[0]
    assert (key["column"], key["k"], key["keys_with_k_rows"], key["share"]) == ("person", 3, 12, 1.0)
    assert key["constant_within_key"] == ["group"] and key["same_grouping"] == ["alias"]
    message = by_rule(d, "repeated_key")[0]["message"]
    assert message.startswith("Most nonmissing rows belong to groups of exactly 3 by person: 36 of 36 (100.0%), from 12 of 12 person values")
    assert "within each person value, group never change; alias splits rows into exactly the same groups" in message
    assert by_rule(d, "repeated_key")[0]["kind"] == "observation"


def test_irregular_repetition_is_quiet(make_profile):
    d = make_profile(keyed([1, 2, 3, 4, 5, 6] * 2)).document
    assert d["row_structure"]["repeated_keys"] == [] and not by_rule(d, "repeated_key")


def test_mostly_regular_key_reports_exceptions(make_profile):
    d = make_profile(keyed([4] * 19 + [2])).document
    key = d["row_structure"]["repeated_keys"][0]
    assert (key["k"], key["keys_with_k_rows"], key["rows_in_k_groups"], key["nonmissing_rows"]) == (4, 19, 76, 78)
    assert key["exception_positions"] == [77, 78]


def dates(values, header="day"):
    return header + "\n" + "\n".join(values) + "\n"


def test_period_straggler_and_far_fence(make_profile):
    days = [f"2021-05-{d:02d}" for d in range(1, 31)] * 4
    d = make_profile(dates(days + ["2021-04-30"])).document
    period = d["row_structure"]["temporal"][0]["period"]
    assert (period["grain"], period["period"], period["outside"], period["positions"]) == ("month", "2021-05", 1, [121])
    assert d["row_structure"]["temporal"][0]["fence"] is None  # one day early is not far
    far = make_profile(dates(days + ["1999-01-01"])).document
    assert far["row_structure"]["temporal"][0]["fence"]["count"] == 1
    assert "quartiles ± 3×IQR" in by_rule(far, "temporal_fence")[0]["message"]


def test_clean_date_column_is_quiet(make_profile):
    d = make_profile(dates([f"2021-{m:02d}-{d:02d}" for m in range(1, 13) for d in (1, 15)])).document
    entry = d["row_structure"]["temporal"][0]
    assert entry["period"] is None and entry["fence"] is None and entry["duplicate_timestamps"] is None
    assert not rows_findings(d)


def test_duplicate_event_timestamps(make_profile):
    stamps = [f"2021-05-{d:02d} 10:{m:02d}:00" for d in range(1, 11) for m in range(0, 30, 10)]
    d = make_profile(dates(stamps + [stamps[4], stamps[7]], "at")).document
    dup = d["row_structure"]["temporal"][0]["duplicate_timestamps"]
    assert (dup["rows_repeating"], dup["repeated_values"], dup["positions"]) == (2, 2, [31, 32])
    # Date-only values are not event times: no duplicate-timestamp check.
    plain = make_profile(dates([f"2021-05-{d:02d}" for d in range(1, 31)] + ["2021-05-03"])).document
    assert plain["row_structure"]["temporal"][0]["duplicate_timestamps"] is None


TRIPS = ("start,end,fare\n2021-05-01 10:00:00,2021-05-01 10:05:00,5\n2021-05-01 11:00:00,2021-05-01 11:00:00,3\n"
         "2021-05-02 09:00:00,2021-05-02 08:59:30,4\n2021-05-02 12:00:00,2021-05-02 13:00:00,9\n")


def test_declared_interval_counts_and_durations(make_profile):
    d = make_profile(TRIPS, {"intervals": [{"start": "start", "end": "end"}]}).document
    item = d["row_structure"]["intervals"][0]
    assert (item["pairs"], item["end_before_start"], item["end_equals_start"]) == (4, 1, 1)
    assert item["negative_positions"] == [3] and item["zero_positions"] == [2]
    assert item["duration_seconds"]["min"] == -30 and item["duration_seconds"]["max"] == 3600
    assert "Full date-times parsed" in by_rule(d, "interval")[0]["message"]
    assert not [f for f in d["findings"] if f["id"] == "rows-interval-undeclared"]


def test_undeclared_interval_only_asks(make_profile):
    d = make_profile(TRIPS).document
    assert d["row_structure"]["intervals"] == [] and not by_rule(d, "interval")
    question = next(f for f in d["findings"] if f["id"] == "rows-interval-undeclared")
    assert question["kind"] == "question" and "Declare it under `intervals`" in question["message"]


def test_interval_config_is_strict():
    for bad in ([{"start": "a"}], [{"start": "a", "end": "a"}], [{"start": "a", "end": "zz"}], {"start": "a"}):
        with pytest.raises(ValueError):
            validate_config({"intervals": bad}, ["a", "b"])
    assert parse_datetime("2021-05-01") [1] is False and parse_datetime("2021-02-30 10:00") is None


def test_row_checks_never_act_and_are_deterministic(make_profile):
    first = make_profile(keyed([3] * 12)).to_json()
    second = make_profile(keyed([3] * 12)).to_json()
    assert first == second
    assert not rows_findings(make_profile(keyed([3] * 12)).document, "action")


INTERVAL = {"intervals": [{"start": "start", "end": "end"}]}


def test_fully_parsed_interval_has_no_unparsed_note(make_profile):
    d = make_profile(TRIPS, INTERVAL).document
    message = by_rule(d, "interval")[0]["message"]
    assert "4 of 4 complete pairs parsed" in message and "not strict ISO" not in message
    assert d["row_structure"]["intervals"][0]["unparsed_pairs"] == 0


@pytest.mark.parametrize("start,end", [
    ("03/01/2019 10:00", "03/01/2019 10:05"),          # US format
    ("2019-03-01T10:00:00Z", "2019-03-01T10:05:00Z"),  # Z suffix
    ("2019-03-01 10:00:00.5", "2019-03-01 10:05:00.5"),  # fractional seconds
])
def test_unparsed_interval_shapes_are_not_reported_as_clean(make_profile, start, end):
    body = "start,end\n" + f"{start},{end}\n" * 3
    d = make_profile(body, INTERVAL).document
    item = d["row_structure"]["intervals"][0]
    assert (item["pairs"], item["unparsed_pairs"], item["complete_pairs"]) == (0, 3, 3)
    message = by_rule(d, "interval")[0]["message"]
    assert "none of 3 complete pairs could be parsed" in message and "0 end before start" not in message
    assert [f for f in rows_findings(d, "question") if f["rule"] == "interval"]


def test_partly_parsed_interval_states_unparsed_count_and_asks(make_profile):
    body = TRIPS + "03/03/2021 10:00,03/03/2021 10:05,2\n"
    d = make_profile(body, INTERVAL).document
    message = by_rule(d, "interval")[0]["message"]
    assert "4 of 5 complete pairs parsed" in message and "1 of 5 pairs are not strict ISO" in message
    question = next(f for f in rows_findings(d, "question") if f["rule"] == "interval")
    assert "1 unparsed" in question["message"]
