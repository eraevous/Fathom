"""Spec 035 slice 1: context gate, registry, five statuses, W1, W5, T1, T3. FT-DX35-R1..R5 (Kate, independent)."""
import csv
import json
import random
import re
from pathlib import Path

import pytest

import fathom.diagnostics as dx
from fathom.config import validate_config
from fathom.connectors import CSVConnector
from fathom.profiler import profile

BANNED = re.compile(r"leakage-free|no leakage|\bsafe\b|\bbest\b|recommended model|suitable for|\bready\b|\bpassed\b|\bOK\b"
                    r"|residual|heteroscedastic|influence|fitted", re.I)


def write(tmp_path, header, rows, name="t.csv"):
    path = tmp_path / name
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    return CSVConnector(path).load()


def results(doc):
    return {r["id"]: r for r in doc["diagnostics"]["results"]}


def clean(tmp_path, n=120):
    """Two balanced classes, noisy features, no duplicates: the decoy for W1 and W5."""
    rnd = random.Random(35)
    rows = [[f"{rnd.gauss(0, 1):.5f}", rnd.choice(["a", "b", "c"]), f"{rnd.gauss(0, 1):.5f}", "yes" if i % 2 else "no"]
            for i in range(n)]
    return write(tmp_path, ["x", "colour", "z", "label"], rows)


def test_r1_absent_block_changes_nothing_and_gate_asks_for_roles(tmp_path):
    data = clean(tmp_path)
    plain = profile(data, {"target": "label"}).to_json()
    assert "diagnostics" not in json.loads(plain)
    assert not any(f.get("rule", "").startswith("diagnostic") for f in json.loads(plain)["findings"])
    doc = profile(data, {"diagnostics": {"task": "forecast"}}).document
    asks = {f["id"]: f for f in doc["findings"] if f.get("rule") == "diagnostic_context_gate"}
    assert "diagnostics.time" in asks["diagnostics-needs-time"]["message"]
    assert "`target`" in asks["diagnostics-needs-target"]["message"]
    assert all(r["status"] == "not_applicable" for r in doc["diagnostics"]["results"])
    no_task = profile(data, {"target": "label", "diagnostics": {}}).document
    assert results(no_task)["T1"]["status"] == "not_applicable"
    assert any(f["id"] == "diagnostics-needs-task" for f in no_task["findings"])
    assert no_task["diagnostics"]["context"]["task"] is None  # never inferred from the target's type


def test_r1_config_refuses_undeclared_or_malformed_roles():
    cols = ["a", "b", "y"]
    for bad in ({"task": "clustering"}, {"families": ["boosting"]}, {"task": "count", "nonsense": 1},
                {"task": "classification", "features": ["y"]}, {"task": "classification", "features": ["zz"]},
                {"task": "regression", "exposure": "a"}, {"task": "count", "horizon": {"value": 3, "unit": "month"}},
                {"task": "forecast", "horizon": {"value": 0, "unit": "month"}},
                {"split": {"column": "a", "train": ["t"], "evaluation": ["t"]}}):
        with pytest.raises(ValueError):
            validate_config({"target": "y", "diagnostics": bad}, cols)
    ok = validate_config({"target": "y", "diagnostics": {"task": "forecast", "time": "a",
                                                         "horizon": {"value": 3, "unit": "month"}}}, cols)
    assert ok["diagnostics"]["horizon"] == {"value": 3, "unit": "month"}


def test_r2_registry_rows_carry_every_contract_field():
    fields = {"id", "tasks", "families", "roles", "inputs", "computation", "threshold", "limitations", "finding"}
    assert [r["id"] for r in dx.REGISTRY] == ["W1", "W5", "T1", "T3"]
    for row in dx.REGISTRY:
        assert fields <= set(row) and all(row[f] for f in fields)


def test_r2_five_statuses_are_distinct_and_rendered_differently(tmp_path, monkeypatch):
    data = clean(tmp_path)
    doc = profile(data, {"target": "label", "diagnostics": {"task": "classification"}}).document
    seen = {r["id"]: r["status"] for r in doc["diagnostics"]["results"]}
    assert seen == {"W1": "no_signal", "W5": "no_signal", "T1": "no_signal", "T3": "not_applicable"}
    tiny = write(tmp_path, ["x", "y"], [["1", "2"]], "tiny.csv")
    assert results(profile(tiny, {"target": "y", "diagnostics": {"task": "count"}}).document)["T3"]["status"] == "insufficient_data"
    small = write(tmp_path, ["x", "y"], [[str(i), "a" if i < 40 else "b"] for i in range(50)], "small.csv")
    assert results(profile(small, {"target": "y", "diagnostics": {"task": "classification"}}).document)["T1"]["status"] == "signal"
    monkeypatch.setitem(dx.CHECKS, "W1", lambda ctx: 1 / 0)
    broken = profile(data, {"target": "label", "diagnostics": {"task": "classification"}}).document
    assert results(broken)["W1"] == {"id": "W1", "title": dx.REGISTRY[0]["title"], "status": "failed", "error": "ZeroDivisionError"}
    assert results(broken)["T1"]["status"] == "no_signal"  # the run continues
    line = next(f for f in broken["findings"] if f["id"] == "diagnostics-checks")["message"]
    assert "checked, not found" in line and "not applicable" in line and "computation failed" in line
    lines = [dx.describe(r) for r in results(broken).values()]
    assert len({l.split(": ", 1)[1].split(" ")[0] for l in lines}) >= 3
    assert all(s in dx.STATUSES for s in seen.values())


def test_r4_w1_duplicates_with_different_targets(tmp_path):
    rows = [[str(i), "a", "yes" if i % 2 else "no"] for i in range(60)]
    rows += [["5", "a", "no"], ["7", "a", "no"]]  # rows 6/8 had "yes"
    data = write(tmp_path, ["x", "colour", "label"], rows)
    doc = profile(data, {"target": "label", "diagnostics": {"task": "classification"}}).document
    w1 = results(doc)["W1"]
    assert w1["status"] == "signal" and w1["groups"] == 2 and w1["rows"] == 4
    assert w1["example_rows"] == [6, 8, 61, 62]
    assert any(f["id"] == "diagnostics-W1" and f["kind"] == "observation" for f in doc["findings"])


def test_r4_w5_rules_fire_with_evidence_and_a_timing_question(tmp_path):
    rnd = random.Random(5)
    rows = []
    for i in range(120):
        label = "yes" if i % 2 else "no"
        rows.append([f"{rnd.gauss(0, 1):.5f}", label, "Y" if label == "yes" else "N",
                     "gold" if i < 40 else rnd.choice(["p", "q"]), label])
    for i in range(40):  # gold always maps to one class
        rows[i][4] = "no"
        rows[i][1] = "no"
        rows[i][2] = "N"
    data = write(tmp_path, ["x", "copy", "recode", "tier", "label"], rows)
    doc = profile(data, {"target": "label", "diagnostics": {"task": "classification"}}).document
    hits = {h["feature"]: h for h in results(doc)["W5"]["features"]}
    assert hits["copy"]["rule"] == "equal to the target on every complete row"
    assert hits["recode"]["rule"] == "levels map one-to-one onto classes"
    assert hits["tier"]["rule"] == "a level maps to a single class" and hits["tier"]["levels"][0]["level"] == "gold"
    assert "x" not in hits
    assert {f["id"] for f in doc["findings"] if f["kind"] == "question" and f.get("rule") == "diagnostic_W5"} == {
        "diagnostics-W5-copy-timing", "diagnostics-W5-recode-timing", "diagnostics-W5-tier-timing"}
    assert doc["diagnostics"]["leakage_note"] is None


def test_r4_w5_numeric_target_uses_rank_rule_only(tmp_path):
    rnd = random.Random(9)
    rows = []
    for i in range(80):
        y = i * 1.5 + rnd.random()
        rows.append([f"{y * 2 + 1:.4f}", f"{rnd.gauss(0, 1):.4f}", f"{i % 3}", f"{y:.4f}"])
    data = write(tmp_path, ["scaled", "noise", "code", "y"], rows)
    doc = profile(data, {"target": "y", "diagnostics": {"task": "regression"}}).document
    hits = {h["feature"]: h for h in results(doc)["W5"]["features"]}
    assert set(hits) == {"scaled"} and hits["scaled"]["spearman_rho"] >= 0.98


def test_r4_clean_fixture_fires_nothing_and_shows_the_fixed_sentence(tmp_path):
    doc = profile(clean(tmp_path), {"target": "label", "diagnostics": {"task": "classification"}}).document
    assert doc["diagnostics"]["leakage_note"] == dx.LEAKAGE_SENTENCE
    line = next(f for f in doc["findings"] if f["id"] == "diagnostics-checks")["message"]
    assert dx.LEAKAGE_SENTENCE in line


def test_t3_count_target_and_exposure(tmp_path):
    rows = [[str(i % 5), str(i % 4 if i % 7 else 0), str(1 + i % 3)] for i in range(60)]
    rows += [["1", "2.5", "0"], ["2", "-1", ""]]
    data = write(tmp_path, ["x", "y", "months"], rows)
    doc = profile(data, {"target": "y", "diagnostics": {"task": "count", "exposure": "months"}}).document
    t3 = results(doc)["T3"]
    assert t3["status"] == "signal" and t3["negative"] == 1 and t3["not_whole"] == 1
    assert t3["exposure_missing"] == 1 and t3["exposure_at_or_below_zero"] == 1
    assert t3["variance_to_mean"] is not None and 0 < t3["zero_share"] < 1
    assert "months" not in doc["diagnostics"]["features"]["columns"]


def test_default_features_exclude_target_roles_and_exclusions(tmp_path):
    data = clean(tmp_path)
    cfg = {"target": "label", "columns": {"z": {"exclude_from_target": True}},
           "diagnostics": {"task": "classification", "entity": "colour"}}
    doc = profile(data, cfg).document
    assert doc["diagnostics"]["features"] == {"basis": "default", "columns": ["x"]}


def test_r3_r4_r5_no_banned_wording_and_byte_identical(tmp_path):
    source = Path("src/fathom/diagnostics.py").read_text()
    strings = re.findall(r'"([^"\n]*)"', source)
    assert not [s for s in strings if BANNED.search(s)]
    data = clean(tmp_path)
    cfg = {"target": "label", "diagnostics": {"task": "classification", "families": ["linear", "tree", "distance"]}}
    one, two = profile(data, cfg).to_json(), profile(data, cfg).to_json()
    assert one == two
    found = [f for f in json.loads(one)["findings"] if f.get("rule", "").startswith("diagnostic")]
    assert found and not any(BANNED.search(f["message"] + f["uncertainty"]) for f in found)


def test_non_finite_result_fails_only_that_check(tmp_path):
    data = write(tmp_path, ["x", "y"], [["1", "1e154"], ["2", "-1e154"], ["3", "1e-300"]])
    doc = profile(data, {"target": "y", "diagnostics": {"task": "count"}}).document  # must not raise
    r = results(doc)
    assert r["T3"]["status"] == "failed" and r["T3"]["error"] == "ArithmeticError"
    assert r["W1"]["status"] in ("signal", "no_signal")


def test_no_signal_t3_still_reports_dispersion(tmp_path):
    rows = [[str(i % 5), str(i % 4)] for i in range(60)]
    doc = profile(write(tmp_path, ["x", "y"], rows), {"target": "y", "diagnostics": {"task": "count"}}).document
    t3 = results(doc)["T3"]
    assert t3["status"] == "no_signal"
    status = next(f for f in doc["findings"] if f["id"] == "diagnostics-checks")
    assert f"variance-to-mean {t3['variance_to_mean']}" in status["message"]
    assert any(e["value"].get("mean") == t3["mean"] for e in status["evidence"])


def test_dataset_level_questions_render_without_column_grouping(tmp_path):
    from fathom.renderers import repetition_groups
    data = write(tmp_path, ["a", "b"], [["1", "2"], ["3", "4"]])
    for cfg in ({"diagnostics": {}}, {"diagnostics": {"task": "forecast"}}):
        doc = profile(data, cfg).document
        assert len([f for f in doc["findings"] if f.get("rule") == "diagnostic_context_gate"]) >= 2
        repetition_groups(doc)  # raised ValueError on a non-column id before the fix
        result = profile(data, cfg)
        from fathom.renderers import render_html, render_markdown
        assert render_html(result) and render_markdown(result)


def test_gate_asks_only_for_checks_the_task_allows(tmp_path):
    doc = profile(clean(tmp_path), {"diagnostics": {"task": "regression"}}).document
    ask = next(q for q in doc["diagnostics"]["questions"] if q["role"] == "target")
    assert ask["unlocks"] == ["W1", "W5"]
    assert results(doc)["T1"]["reason"].startswith("task is regression")


def test_leakage_sentence_shows_whenever_no_warning_fired(tmp_path):
    doc = profile(clean(tmp_path), {"diagnostics": {"task": "classification"}}).document  # no target: W1/W5 skipped
    assert doc["diagnostics"]["leakage_note"] == dx.LEAKAGE_SENTENCE


def test_w5_uncomputable_rank_rule_is_not_a_negative_result(tmp_path):
    data = write(tmp_path, ["f", "y"], [["10", "1"], ["20", "2"]])
    w5 = results(profile(data, {"target": "y", "diagnostics": {"task": "regression"}}).document)["W5"]
    assert w5["status"] == "insufficient_data" and w5["not_evaluated"] == ["f"]


def test_t1_keeps_class_labels_and_counts_missing_cells_only(tmp_path):
    rows = [["1", "9007199254740992"]] * 30 + [["2", "9007199254740993"]] * 30 + [["3", ""]]
    doc = profile(write(tmp_path, ["x", "y"], rows), {"target": "y", "diagnostics": {"task": "classification"}}).document
    t1 = results(doc)["T1"]
    assert t1["classes_total"] == 2 and t1["smallest"] == 30 and t1["missing_target"] == 1
    assert {c["class"] for c in t1["classes"]} == {"9007199254740992", "9007199254740993"}
    mixed = [["1", "0"]] * 30 + [["2", "1"]] * 30 + [["3", "unknown"]]
    cfg = {"target": "y", "columns": {"y": {"type": "numeric"}}, "diagnostics": {"task": "classification"}}
    t1 = results(profile(write(tmp_path, ["x", "y"], mixed, "m.csv"), cfg).document)["T1"]
    assert t1["missing_target"] == 0 and t1["classes_total"] == 3


def test_t3_separates_absent_from_unparseable_exposure(tmp_path):
    rows = [[str(i), str(i % 3), "unknown" if i == 0 else "2"] for i in range(40)]
    doc = profile(write(tmp_path, ["x", "y", "m"], rows), {"target": "y", "diagnostics": {"task": "count", "exposure": "m"}}).document
    t3 = results(doc)["T3"]
    assert t3["exposure_missing"] == 0 and t3["exposure_unparsed"] == 1 and t3["status"] == "signal"
    assert "not a number" in next(f for f in doc["findings"] if f["id"] == "diagnostics-T3")["message"]


def test_inferred_types_are_labelled(tmp_path):
    data = clean(tmp_path)
    doc = profile(data, {"target": "label", "diagnostics": {"task": "classification"}}).document
    assert doc["diagnostics"]["type_basis"]["target"] == "inferred" and dx.TYPE_NOTE in doc["diagnostics"]["uncertainty"]
    declared = profile(data, {"target": "label", "columns": {"label": {"type": "categorical"}},
                              "diagnostics": {"task": "classification"}}).document
    assert declared["diagnostics"]["type_basis"]["target"] == "human-declared"
    assert dx.TYPE_NOTE not in declared["diagnostics"]["uncertainty"]


def test_inferred_feature_types_are_labelled_when_the_target_is_declared(tmp_path):
    data = write(tmp_path, ["x", "y"], [[str(10 * i), str(i)] for i in range(1, 40)])
    doc = profile(data, {"target": "y", "columns": {"y": {"type": "numeric"}}, "diagnostics": {"task": "regression"}}).document
    assert results(doc)["W5"]["status"] == "signal"
    assert doc["diagnostics"]["type_basis"] == {"target": "human-declared", "inferred_columns": ["x"]}
    assert dx.TYPE_NOTE in doc["diagnostics"]["uncertainty"]


def test_w5_boolean_target_spellings_are_one_class(tmp_path):
    rows = [["A", "true"]] * 15 + [["A", "TRUE"]] * 15 + [["B", "false"]] * 15 + [["B", "FALSE"]] * 15
    doc = profile(write(tmp_path, ["f", "y"], rows), {"target": "y", "columns": {"y": {"type": "boolean"}},
                                                     "diagnostics": {"task": "classification"}}).document
    hits = {h["feature"]: h for h in results(doc)["W5"]["features"]}
    assert hits["f"]["rule"] == "levels map one-to-one onto classes"
