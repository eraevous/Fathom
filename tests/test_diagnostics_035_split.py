"""Spec 035 slice 2: split and entity (W2, W3, W4, T2, T4, E4). FT-DX35-R1..R5 (Kate, independent).

Every check has a planted fixture and a clean decoy (CHARTER; DG-RF)."""
import json
import random

from fathom.profiler import profile

import fathom.diagnostics as dx
from test_diagnostics_035 import BANNED, results, write

SPLIT = {"column": "fold", "train": ["train"], "evaluation": ["test"]}


def table(tmp_path, n=120, leak=False, name="s.csv"):
    """customer, signup date, x, colour, fold, label. Train rows are dated before every test row unless leak."""
    rnd = random.Random(352)
    rows = []
    for i in range(n):
        test = i >= n * 3 // 4
        day = 1 + (i % 28)
        month = 6 if test else 1 + (i % 5)
        if leak and test and i % 5 == 0:
            month = 2
        rows.append([f"c{i if not (leak and test) else i % 10}", f"2026-{month:02d}-{day:02d}",
                     f"{rnd.uniform(-1, 1) if test else rnd.gauss(0, 1):.5f}", ["a", "b", "c"][i % 3], "test" if test else "train",
                     "yes" if i % 2 else "no"])
    return write(tmp_path, ["customer", "signup", "x", "colour", "fold", "label"], rows, name)


def cfg(**block):
    return {"target": "label", "diagnostics": {"task": "classification", "split": SPLIT, **block}}


def test_clean_split_fires_none_and_keeps_the_fixed_sentence(tmp_path):
    doc = profile(table(tmp_path), cfg(entity="customer", time="signup", families=["tree"])).document
    r = results(doc)
    assert {k: r[k]["status"] for k in ("W2", "W3", "W4", "T2", "E4")} == dict.fromkeys(("W2", "W3", "W4", "T2", "E4"), "no_signal")
    assert r["T4"]["status"] == "not_applicable"  # classification
    assert r["W3"]["rows_per_entity"] == {"min": 1, "median": 1, "max": 1}
    assert doc["diagnostics"]["leakage_note"] == dx.LEAKAGE_SENTENCE
    assert doc["diagnostics"]["features"]["columns"] == ["x", "colour"]  # split, entity and time are roles, not features


def test_w3_w4_entities_and_dates_crossing_the_split(tmp_path):
    doc = profile(table(tmp_path, leak=True), cfg(entity="customer", time="signup")).document
    r = results(doc)
    assert r["W3"]["status"] == "signal" and r["W3"]["entities_on_both_sides"] == 10
    assert r["W3"]["example_entities"] == ["c0", "c1", "c2", "c3", "c4"]
    assert r["W4"]["status"] == "signal" and r["W4"]["evaluation_rows_before_latest_train"] == 6
    assert r["W4"]["overlap_window"][0].startswith("2026-02") and r["W4"]["latest_train"].startswith("2026-05")
    assert doc["diagnostics"]["leakage_note"] is None
    ids = {f["id"] for f in doc["findings"]}
    assert {"diagnostics-W3", "diagnostics-W4"} <= ids
    assert not any(i.startswith("diagnostics-W5-") and i.endswith("-timing") for i in ids)


def test_w2_duplicates_across_the_split(tmp_path):
    rows = [[f"{i}", "a" if i % 2 else "b", "test" if i >= 45 else "train", "yes" if i % 2 else "no"] for i in range(60)]
    rows += [["3", "a", "test", "yes"], ["8", "b", "test", "no"], ["8", "b", "holdout", "no"]]
    data = write(tmp_path, ["x", "colour", "fold", "label"], rows)
    w2 = results(profile(data, cfg()).document)["W2"]
    assert w2["status"] == "signal" and w2["groups"] == 2
    assert w2["train_rows_matched"] == 2 and w2["evaluation_rows_matched"] == 2 and w2["outside_split"] == 1
    assert w2["example_rows"] == [4, 9, 61, 62]


def test_t2_class_missing_from_one_side(tmp_path):
    rows = [[f"{i}", "test" if i >= 60 else "train", "rare" if i < 5 else ("yes" if i % 2 else "no")] for i in range(80)]
    data = write(tmp_path, ["x", "fold", "label"], rows)
    t2 = results(profile(data, cfg()).document)["T2"]
    assert t2["status"] == "signal" and t2["missing_from_evaluation"] == ["rare"] and t2["missing_from_train"] == []
    assert "rare" in t2["train"]["under_minimum"]
    assert t2["evaluation"]["rows_with_target"] == 20


def test_t4_and_e4_evaluation_outside_train_range(tmp_path):
    rows = [[f"{i % 50}", ["a", "b"][i % 2], "train", f"{i % 40}"] for i in range(80)]
    rows += [[f"{60 + i}", "z" if i < 3 else "a", "test", f"{45 + i}" if i < 4 else f"{i}"] for i in range(20)]
    data = write(tmp_path, ["x", "colour", "fold", "y"], rows)
    doc = profile(data, {"target": "y", "diagnostics": {"task": "regression", "split": SPLIT, "families": ["tree"]}}).document
    r = results(doc)
    assert r["T4"]["status"] == "signal" and r["T4"]["above_train_max"] == 4 and r["T4"]["below_train_min"] == 0
    hits = {h["feature"]: h for h in r["E4"]["features"]}
    assert hits["x"]["above_train_max"] == 20 and hits["colour"]["unseen_levels"] == 1 and hits["colour"]["evaluation_rows"] == 3
    assert r["T2"]["status"] == "not_applicable"
    assert "diagnostics-E4" in {f["id"] for f in doc["findings"]}


def test_gate_family_and_missing_roles(tmp_path):
    data = table(tmp_path)
    doc = profile(data, {"target": "label", "diagnostics": {"task": "classification"}}).document
    r = results(doc)
    assert r["E4"]["status"] == "not_applicable" and r["E4"]["reason"].startswith("family not declared")
    asks = {q["role"]: q for q in doc["diagnostics"]["questions"]}
    assert asks["split"]["unlocks"] == ["W2", "W3", "W4", "T2"] and asks["entity"]["unlocks"] == ["W3"]
    doc = profile(data, cfg()).document
    asks = {q["role"]: q["unlocks"] for q in doc["diagnostics"]["questions"]}
    assert asks == {"entity": ["W3"], "time": ["W4"]}
    forecast = profile(data, {"target": "label", "diagnostics": {"task": "forecast", "split": SPLIT}}).document
    assert {q["role"]: q["unlocks"] for q in forecast["diagnostics"]["questions"]}["time"] == ["W4"]


def test_empty_side_and_undated_rows_are_insufficient(tmp_path):
    rows = [[f"{i}", "", "train", "yes" if i % 2 else "no"] for i in range(40)]
    data = write(tmp_path, ["x", "when", "fold", "label"], rows)
    r = results(profile(data, cfg(time="when")).document)
    assert r["W2"]["status"] == "insufficient_data" and r["W2"]["rows_on_smaller_side"] == 0
    rows = [[f"{i}", "03/04/2026" if i % 2 else "", "test" if i >= 30 else "train", "yes" if i % 2 else "no"] for i in range(40)]
    r = results(profile(write(tmp_path, ["x", "when", "fold", "label"], rows, "d.csv"), cfg(time="when")).document)
    assert r["W4"]["status"] == "insufficient_data" and r["W4"]["undated_rows"] == 40  # ambiguous day/month is not read


def test_slice2_wording_and_bytes(tmp_path):
    data = table(tmp_path, leak=True)
    c = cfg(entity="customer", time="signup", families=["tree"])
    one, two = profile(data, c).to_json(), profile(data, c).to_json()
    assert one == two
    found = [f for f in json.loads(one)["findings"] if f.get("rule", "").startswith("diagnostic")]
    assert not any(BANNED.search(f["message"] + f["uncertainty"]) for f in found)
    lines = [dx.describe(r) for r in json.loads(one)["diagnostics"]["results"]]
    assert all(lines)


def test_e4_labels_inferred_feature_types_without_a_target(tmp_path):
    """Codex P1 on #81: E4 chooses range or levels from feature types, so inferred types are labelled."""
    data = table(tmp_path)
    for c in ({"target": "label", "columns": {"label": {"type": "categorical"}},
               "diagnostics": {"task": "classification", "split": SPLIT, "families": ["tree"]}},
              {"diagnostics": {"task": "classification", "split": SPLIT, "families": ["tree"]}}):
        d = profile(data, c).document["diagnostics"]
        assert {"x", "colour"} <= set(d["type_basis"]["inferred_columns"]) and dx.TYPE_NOTE in d["uncertainty"]
    declared = profile(data, {"columns": {"x": {"type": "numeric"}, "colour": {"type": "categorical"}},
                              "diagnostics": {"task": "classification", "split": SPLIT, "families": ["tree"],
                                              "features": ["x", "colour"]}}).document["diagnostics"]
    assert declared["type_basis"]["inferred_columns"] == []


def test_t2_smallest_class_counts_every_class_not_only_the_listed_fifty(tmp_path):
    """Codex P2 on #81: the smallest class comes from the full counts, not the truncated list."""
    rows = []
    for side in ("train", "test"):
        for k in range(51):
            rows += [[f"{len(rows)}", side, f"k{k:02d}"]] * (1 if k == 50 else 40)
    data = write(tmp_path, ["x", "fold", "label"], rows)
    t2 = results(profile(data, cfg()).document)["T2"]
    assert t2["status"] == "no_signal" and len(t2["train"]["classes"]) == 50
    assert t2["train"]["smallest"] == 1 and t2["evaluation"]["smallest"] == 1
    assert "smallest class train 1, evaluation 1 rows" in dx.describe(t2)


def test_e4_lists_identifier_columns_as_not_evaluated(tmp_path):
    """Codex P2 on #81: a sequential numeric ID split by time would always fall outside the train range."""
    rows = [[str(1000 + i), f"{(i * 7) % 13}", "test" if i >= 60 else "train", "yes" if i % 2 else "no"] for i in range(80)]
    data = write(tmp_path, ["order_id", "x", "fold", "label"], rows)
    c = {"target": "label", "columns": {"order_id": {"role": "identifier"}},
         "diagnostics": {"task": "classification", "split": SPLIT, "families": ["tree"]}}
    e4 = results(profile(data, c).document)["E4"]
    assert "order_id" in e4["not_evaluated"] and "order_id" not in {h["feature"] for h in e4["features"]}
    assert e4["status"] == "no_signal"
