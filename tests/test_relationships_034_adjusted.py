"""Spec 034 slice 2a (A2 conditional, A3 partial). FT-REL34-R3/R4/R5 (Kate, independent)."""
import csv
import json
import random
import re
from pathlib import Path

import pytest

from fathom.config import validate_config
from fathom.connectors import CSVConnector
from fathom.profiler import profile

BANNED = re.compile(r"\b(significant|significance|causes?|drives?|important)\b", re.I)


def write(tmp_path, header, rows, name="t.csv"):
    path = tmp_path / name
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    return CSVConnector(path).load()


def confounded(tmp_path, n=400, seed=11):
    """X and Y both follow Z (four levels, and its numeric code); no direct X-Y link."""
    rnd = random.Random(seed)
    rows = []
    for i in range(n):
        level = i % 4
        z = level * 2.0
        rows.append([f"{z + rnd.gauss(0, 1):.5f}", f"{z + rnd.gauss(0, 1):.5f}", f"{z:.1f}", f"L{level}"])
    return write(tmp_path, ["x", "y", "zcode", "zlevel"], rows)


CFG = {"target": "y", "columns": {"zlevel": {"type": "categorical"}},
       "relationships": {"condition_on": ["zlevel"], "controls": ["zcode"]}}


def test_r4_confounded_marginal_vs_within_level_and_partial(tmp_path):
    doc = profile(confounded(tmp_path), CFG).document
    rel = doc["relationships"]
    cond = next(c for c in rel["conditional"] if c["left"] == "x")
    assert cond["status"] == "computed" and cond["marginal"]["pearson_r"] > 0.7
    assert len(cond["levels"]) == 4 and all(abs(lv["measures"]["pearson_r"]) < 0.2 for lv in cond["levels"])
    part = next(p for p in rel["partial"] if p["left"] == "x")
    assert part["status"] == "computed" and part["marginal_pearson_r"] > 0.7 and abs(part["partial_r"]) < 0.15
    assert cond["declared_as"] == "relationships.condition_on" and part["declared_as"] == "relationships.controls"
    assert "estimand" in cond and "estimand" in part
    assert rel["selection_route"].startswith("target pairs already selected by pair_budget")
    messages = [f["message"] for f in doc["findings"] if f.get("rule") in {"conditional_association", "partial_correlation"}]
    assert any("within levels of zlevel" in m for m in messages)
    assert any("with zcode held linear" in m for m in messages)


def test_r3_counts_reconcile_with_planted_missingness(tmp_path):
    rnd = random.Random(5)
    rows = []
    for i in range(200):
        x, y, z = rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1)
        rows.append(["" if i % 10 == 0 else f"{x:.4f}", f"{y:.4f}", "" if i % 7 == 0 else f"{z:.4f}",
                     "" if i % 13 == 0 else ("a" if i % 2 else "b")])
    data = write(tmp_path, ["x", "y", "z", "g"], rows)
    doc = profile(data, {"target": "y", "relationships": {"condition_on": ["g"], "controls": ["z"]}}).document
    rel = doc["relationships"]
    cond = next(c for c in rel["conditional"] if c["left"] == "x")
    assert cond["n"] + cond["excluded_rows"] == 200
    assert sum(lv["n"] for lv in cond["levels"]) + cond["condition_missing"] == cond["n"]
    part = next(p for p in rel["partial"] if p["left"] == "x")
    assert part["n"] + part["excluded_rows"] == 200
    assert part["n"] == sum(1 for i in range(200) if i % 10 and i % 7)


def test_small_levels_are_reported_not_measured(tmp_path):
    rnd = random.Random(2)
    rows = [[f"{rnd.gauss(0, 1):.4f}", f"{rnd.gauss(0, 1):.4f}", "big" if i < 80 else "small"] for i in range(100)]
    doc = profile(write(tmp_path, ["x", "y", "g"], rows), {"target": "y", "relationships": {"condition_on": ["g"]}}).document
    cond = next(c for c in doc["relationships"]["conditional"] if c["left"] == "x")
    small = next(lv for lv in cond["levels"] if lv["level"] == "small")
    assert small["n"] == 20 and small["measures"] is None and "reported, not measured" in small["reason"]
    assert next(lv for lv in cond["levels"] if lv["level"] == "big")["measures"]


def test_level_bounds_and_collinear_controls_are_named_skips(tmp_path):
    rnd = random.Random(4)
    rows = []
    for i in range(120):
        z = rnd.gauss(0, 1)
        rows.append([f"{rnd.gauss(0, 1):.4f}", f"{rnd.gauss(0, 1):.4f}", f"{z:.4f}", f"{2 * z + 1:.4f}", f"g{i % 12}"])
    data = write(tmp_path, ["x", "y", "z", "z2", "many"], rows)
    doc = profile(data, {"target": "y", "relationships": {"condition_on": ["many"], "controls": ["z", "z2"]}}).document
    rel = doc["relationships"]
    cond = next(c for c in rel["conditional"] if c["left"] == "x")
    assert cond["status"] == "skipped" and "12 levels" in cond["reason"]
    part = next(p for p in rel["partial"] if p["left"] == "x")
    assert part["status"] == "skipped" and "collinear" in part["reason"]


def test_validation_happens_before_data_is_read():
    cols = ["x", "y", "z", "a", "b", "c", "d", "e"]
    with pytest.raises(ValueError, match="needs a declared target"):
        validate_config({"relationships": {"controls": ["z"]}}, cols)
    with pytest.raises(ValueError, match="cannot include the target"):
        validate_config({"target": "y", "relationships": {"condition_on": ["y"]}}, cols)
    with pytest.raises(ValueError, match="1 to 5"):
        validate_config({"target": "y", "relationships": {"controls": ["x", "z", "a", "b", "c", "d"]}}, cols)
    with pytest.raises(ValueError, match="unknown column"):
        validate_config({"target": "y", "relationships": {"condition_on": ["nope"]}}, cols)
    with pytest.raises(ValueError, match="at least one"):
        validate_config({"relationships": {}}, cols)
    cfg = validate_config({"target": "y", "relationships": {"controls": ["z"]}}, cols)
    assert cfg["relationships"] == {"controls": ["z"]}


def test_undeclared_has_no_new_keys_and_runs_are_byte_identical(tmp_path):
    data = confounded(tmp_path)
    plain = profile(data, {"target": "y"}).document
    assert "relationships" not in plain
    sets_only = profile(data, {"target": "y", "relationships": {"sets": [{"name": "s", "columns": ["x", "y"]}]}}).document
    assert not {"conditional", "partial"} & set(sets_only["relationships"])
    one = json.dumps(profile(data, CFG).document, sort_keys=True)
    two = json.dumps(profile(confounded(tmp_path), CFG).document, sort_keys=True)
    assert one == two


def test_r5_no_banned_wording(tmp_path):
    strings = re.findall(r'"([^"\n]*)"', Path("src/fathom/adjusted.py").read_text())
    assert not [s for s in strings if BANNED.search(s)]
    doc = profile(confounded(tmp_path), CFG).document
    found = [f for f in doc["findings"] if f.get("rule") in {"conditional_association", "partial_correlation"}]
    assert found and all(f["kind"] == "observation" for f in found)
    assert not any(BANNED.search(f["message"] + f["uncertainty"]) for f in found)
    assert not any("confound" in f["message"].lower() or "effect of" in f["message"].lower() for f in found)
