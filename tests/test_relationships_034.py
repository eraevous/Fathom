"""Spec 034 slice 1 (A1): declared association matrix. FT-REL34-R1/R2/R3/R5 (Kate, independent)."""
import csv
import json
import random
import re
from pathlib import Path

import pytest

from fathom.config import validate_config
from fathom.connectors import CSVConnector
from fathom.profiler import profile


def write(tmp_path, header, rows):
    path = tmp_path / "t.csv"
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    return CSVConnector(path).load()


def wide(tmp_path, ncols=200, nrows=60):
    rnd = random.Random(7)
    header = [f"c{i:03d}" for i in range(ncols)]
    rows = [[f"{rnd.gauss(0, 1):.4f}" for _ in header] for _ in range(nrows)]
    return write(tmp_path, header, rows), header


def test_r1_undeclared_wide_table_is_unchanged_and_a_set_computes_66_pairs(tmp_path):
    data, header = wide(tmp_path)
    plain = profile(data).to_json()
    assert "relationships" not in json.loads(plain)
    assert not any(f.get("rule") == "declared_relationship_set" for f in json.loads(plain)["findings"])
    cfg = {"relationships": {"sets": [{"name": "first", "columns": header[:12]}]}}
    one, two = profile(data, cfg).to_json(), profile(data, cfg).to_json()
    assert one == two
    item = json.loads(one)["relationships"]["sets"][0]
    assert item["pairs_planned"] == item["pairs_computed"] == len(item["pairs"]) == 66
    names = {n for p in item["pairs"] for n in (p["left"], p["right"])}
    assert names == set(header[:12])


def test_r1_bounds_are_enforced_before_any_data_is_read():
    cols = [f"c{i}" for i in range(20)]
    with pytest.raises(ValueError, match="2 to 12"):
        validate_config({"relationships": {"sets": [{"name": "s", "columns": cols[:13]}]}}, cols)
    with pytest.raises(ValueError, match="1 to 3"):
        validate_config({"relationships": {"sets": [{"name": str(i), "columns": cols[:2]} for i in range(4)]}}, cols)
    with pytest.raises(ValueError, match="unknown column"):
        validate_config({"relationships": {"sets": [{"name": "s", "columns": ["c0", "nope"]}]}}, cols)
    with pytest.raises(ValueError, match="keys: sets"):
        validate_config({"relationships": {"top_k": 10}}, cols)


def test_r2_types_and_named_skips(tmp_path):
    rows = []
    for i in range(40):
        rows.append([str(i % 3 + 1), f"{i * 1.5:.1f}", f"{(i % 3) * 10 + i * 0.1:.1f}", "same", "", str(i), ["a", "b"][i % 2]])
    header = ["coded", "x", "y", "constant", "empty", "many", "label"]
    data = write(tmp_path, header, rows)
    cfg = {"columns": {"coded": {"type": "categorical"}, "many": {"type": "categorical"}},
           "relationships": {"sets": [{"name": "s", "columns": header}]}}
    item = profile(data, cfg).document["relationships"]["sets"][0]
    skipped = {s["column"]: s["reason"] for s in item["skipped"]}
    assert skipped["constant"] == "constant column"
    assert skipped["empty"] == "all values missing"
    assert skipped["many"] == "more than 20 levels"
    pairs = {(p["left"], p["right"]): p for p in item["pairs"]}
    assert set(pairs[("coded", "x")]["measures"]) == {"eta"}
    assert set(pairs[("x", "y")]["measures"]) == {"pearson_r", "spearman_rho"}
    assert set(pairs[("coded", "label")]["measures"]) == {"cramers_v_corrected"}
    assert item["pairs_computed"] == 6 and item["pairs_planned"] == 21


def test_r3_counts_reconcile_with_planted_missingness(tmp_path):
    rnd = random.Random(3)
    rows = [[("" if i % 5 == 0 else f"{rnd.random():.3f}"), ("" if i % 7 == 0 else f"{rnd.random():.3f}"), f"{i}"] for i in range(70)]
    data = write(tmp_path, ["a", "b", "c"], rows)
    doc = profile(data, {"relationships": {"sets": [{"name": "s", "columns": ["a", "b", "c"]}]}}).document
    rel = doc["relationships"]
    for p in rel["sets"][0]["pairs"]:
        assert p["n"] + p["excluded_rows"] == rel["rows"] == 70
    ab = next(p for p in rel["sets"][0]["pairs"] if (p["left"], p["right"]) == ("a", "b"))
    assert ab["n"] == 70 - len({i for i in range(70) if i % 5 == 0 or i % 7 == 0})
    assert rel["sampling"] and rel["threshold"]


BANNED = re.compile(r"\b(significant|significance|causes?|drives?|important)\b", re.I)


def test_r5_no_banned_wording_in_module_or_findings(tmp_path):
    source = Path("src/fathom/relationships.py").read_text()
    strings = re.findall(r'"([^"\n]*)"', source)
    assert not [s for s in strings if BANNED.search(s)]
    data, header = wide(tmp_path, 6, 30)
    doc = profile(data, {"relationships": {"sets": [{"name": "s", "columns": header}]}}).document
    found = [f for f in doc["findings"] if f.get("rule") == "declared_relationship_set"]
    assert found and all(f["kind"] == "observation" for f in found)
    assert not any(BANNED.search(f["message"] + f["uncertainty"]) for f in found)


def test_type_basis_is_labelled_per_pair_and_in_the_finding(tmp_path):
    rows = [[str(i % 3 + 1), f"{i * 1.5:.1f}", f"{i % 4}.5"] for i in range(30)]
    data = write(tmp_path, ["coded", "x", "y"], rows)
    cfg = {"columns": {"coded": {"type": "categorical"}, "x": {"type": "numeric"}},
           "relationships": {"sets": [{"name": "s", "columns": ["coded", "x", "y"]}]}}
    doc = profile(data, cfg).document
    pairs = {(p["left"], p["right"]): p["semantics"] for p in doc["relationships"]["sets"][0]["pairs"]}
    assert pairs == {("coded", "x"): "human-declared", ("coded", "y"): "inferred", ("x", "y"): "inferred"}
    f = next(f for f in doc["findings"] if f.get("rule") == "declared_relationship_set")
    assert "2 of 3 pairs use at least one inferred column type" in f["message"]


def test_eta_is_described_as_the_square_root_of_the_variance_share(tmp_path):
    data, header = wide(tmp_path, 3, 20)
    text = profile(data, {"relationships": {"sets": [{"name": "s", "columns": header}]}}).document["relationships"]["measures"]["category×numeric"]
    assert "square root" in text and "eta squared" in text
