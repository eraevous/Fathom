"""Spec 035 slice 3: linear and tree families (L1, L2, L3, E1, E2, E3). FT-DX35-R1..R5 (Kate, independent).

Every check has a planted fixture and a clean decoy (CHARTER; DG-RF)."""
import json
import random

from fathom.profiler import profile

import fathom.diagnostics as dx
from test_diagnostics_035 import BANNED, results, write

FAMILY_IDS = ("L1", "L2", "L3", "E1", "E2", "E3")


def decoy(tmp_path, n=240, name="f.csv"):
    """Independent numeric features, a three-level colour, no missing cells, two balanced overlapping classes."""
    rnd = random.Random(353)
    rows = [[f"{rnd.gauss(0, 1):.5f}", f"{rnd.gauss(0, 1):.5f}", ["a", "b", "c"][i % 3], "yes" if i % 2 else "no"]
            for i in range(n)]
    return write(tmp_path, ["x", "z", "colour", "label"], rows, name)


def cfg(task="classification", families=("linear", "tree"), **block):
    return {"target": "label", "diagnostics": {"task": task, "families": list(families), **block}}


def test_clean_decoy_fires_no_family_check(tmp_path):
    r = results(profile(decoy(tmp_path), cfg()).document)
    assert {k: r[k]["status"] for k in FAMILY_IDS} == dict.fromkeys(FAMILY_IDS, "no_signal")
    assert r["L1"]["condition_number"] < dx.CONDITION_LIMIT and r["L1"]["design"] == ["x", "z"]
    assert "condition number" in dx.describe(r["L1"])


def test_families_gate_each_section(tmp_path):
    r = results(profile(decoy(tmp_path), cfg(families=["linear"])).document)
    assert {r[k]["status"] for k in ("E1", "E2", "E3")} == {"not_applicable"}
    assert r["L3"]["status"] == "no_signal"
    r = results(profile(decoy(tmp_path), cfg(task="regression", families=["linear"])).document)
    assert r["L3"]["status"] == "not_applicable"  # classification only


def test_l1_dependent_constant_and_ill_conditioned(tmp_path):
    rnd = random.Random(1)
    rows = []
    for i in range(100):
        a, b = rnd.gauss(0, 1), rnd.gauss(0, 1)
        rows.append([f"{a:.6f}", f"{b:.6f}", f"{a + 2 * b:.6f}", "5", "yes" if i % 2 else "no"])
    data = write(tmp_path, ["a", "b", "s", "k", "label"], rows)
    l1 = results(profile(data, cfg(families=["linear"])).document)["L1"]
    assert l1["status"] == "signal" and l1["dependent"] == ["s"] and l1["condition_number"] is None
    assert "rank deficient" in dx.describe(l1) and {h["feature"] for h in l1["features"]} == {"s"} | set(l1["constant"])
    near = [[f"{a}", f"{b}", f"{float(a) + 2 * float(b) + random.Random(i).gauss(0, 0.01):.6f}", "yes" if i % 2 else "no"]
            for i, (a, b, *_) in enumerate(rows)]
    l1 = results(profile(write(tmp_path, ["a", "b", "s", "label"], near, "n.csv"), cfg(families=["linear"])).document)["L1"]
    assert l1["status"] == "signal" and l1["condition_number"] >= dx.CONDITION_LIMIT and not l1["dependent"]
    assert {v["feature"] for v in l1["high_vif"]} == {"a", "b", "s"} and "ill-conditioned" in dx.describe(l1)


def test_l1_caps_the_design_and_needs_two_numeric_features(tmp_path):
    rnd = random.Random(2)
    rows = [[f"{rnd.gauss(0, 1):.5f}" for _ in range(14)] + ["yes" if i % 2 else "no"] for i in range(60)]
    names = [f"f{j:02d}" for j in range(14)]
    l1 = results(profile(write(tmp_path, names + ["label"], rows), cfg(families=["linear"])).document)["L1"]
    assert l1["design"] == names[:12] and l1["not_evaluated"] == names[12:]
    one = write(tmp_path, ["x", "colour", "label"], [[str(i), "a", "no"] for i in range(40)], "o.csv")
    l1 = results(profile(one, cfg(families=["linear"])).document)["L1"]
    assert l1["status"] == "insufficient_data" and l1["numeric_features"] == 1


def test_l2_e1_sparse_levels(tmp_path):
    rows = [[f"{i}", "rare" if i < 4 else ["a", "b"][i % 2], "yes" if i % 2 else "no"] for i in range(120)]
    data = write(tmp_path, ["x", "colour", "label"], rows)
    r = results(profile(data, cfg()).document)
    for k in ("L2", "E1"):
        h = r[k]["features"][0]
        assert r[k]["status"] == "signal" and h["feature"] == "colour" and h["sparse_levels"] == 1
        assert h["example_levels"] == [{"level": "rare", "rows": 4}] and h["share_of_rows"] == round(4 / 120, 4)
    assert dx.describe(r["L2"]).startswith("L2 linear") and dx.describe(r["E1"]).startswith("E1 tree")
    assert "x" in r["L2"]["not_evaluated"]


def test_l3_level_and_threshold_separation(tmp_path):
    rows = [[f"{i if i % 2 else i + 1000}", "only" if i % 2 and i < 20 else ["a", "b"][i % 2 == 0 and i % 4 == 0],
             "yes" if i % 2 else "no"] for i in range(120)]
    l3 = results(profile(write(tmp_path, ["x", "colour", "label"], rows), cfg(families=["linear"])).document)["L3"]
    kinds = {h["feature"]: h for h in l3["features"]}
    assert l3["status"] == "signal" and kinds["x"]["kind"] == "threshold" and kinds["x"]["class"] == "no"
    assert kinds["x"]["side"] == "above" and kinds["colour"]["kind"] == "level"
    assert {"level": "only", "rows": 10, "class": "yes"} in kinds["colour"]["example_levels"]
    assert "no overlap" in dx.describe(l3)


def test_e2_identifier_role_and_distinct_share(tmp_path):
    rows = [[f"T{i:04d}x", f"{(i * 7) % 11}", f"{1000 + i}", "yes" if i % 2 else "no"] for i in range(80)]
    c = cfg(families=["tree"])
    c["columns"] = {"order": {"role": "identifier"}}
    e2 = results(profile(write(tmp_path, ["ticket", "x", "order", "label"], rows), c).document)["E2"]
    rules = {h["feature"]: h["rule"] for h in e2["features"]}
    assert e2["status"] == "signal" and rules["order"] == "identifier role" and "distinct share" in rules.get("ticket", "distinct share")
    assert "ticket" in rules and "x" not in rules


def test_e3_missingness_against_the_target(tmp_path):
    rows = [[f"{i}" if not (i % 2 and i % 3 == 0) else "", f"{i % 7}", "yes" if i % 2 else "no"] for i in range(180)]
    e3 = results(profile(write(tmp_path, ["x", "z", "label"], rows), cfg(families=["tree"])).document)["E3"]
    assert e3["status"] == "signal" and e3["features"][0]["feature"] == "x" and e3["features"][0]["gap"] >= dx.MISSING_GAP
    rnd = random.Random(3)
    reg = [["" if i < 40 else f"{rnd.gauss(0, 1):.4f}", f"{(100 if i < 40 else 0) + rnd.gauss(0, 1):.4f}"] for i in range(200)]
    c = {"target": "label", "diagnostics": {"task": "regression", "families": ["tree"]}}
    e3 = results(profile(write(tmp_path, ["x", "label"], reg, "r.csv"), c).document)["E3"]
    assert e3["status"] == "signal" and e3["features"][0]["rows_missing"] == 40 and "where missing" in dx.describe(e3)


def test_family_checks_label_inferred_types_wording_and_bytes(tmp_path):
    data = decoy(tmp_path)
    c = cfg()
    one, two = profile(data, c).to_json(), profile(data, c).to_json()
    assert one == two
    d = json.loads(one)["diagnostics"]
    assert {"x", "z", "colour"} <= set(d["type_basis"]["inferred_columns"]) and dx.TYPE_NOTE in d["uncertainty"]
    found = [f for f in json.loads(one)["findings"] if f.get("rule", "").startswith("diagnostic")]
    assert not any(BANNED.search(f["message"] + f["uncertainty"]) for f in found)
    assert all(dx.describe(r) for r in d["results"])
