import builtins

import pytest


def test_numeric_pair_exact_and_budget(make_profile):
    d = make_profile("x,y,z\n1,2,8\n2,4,6\n3,6,4\n", {"target": "y", "question": "How does y vary with x?", "pair_budget": 1}).document
    assert d["selection"]["selected"] == [["x", "y"]]
    assert {e["column"]: e["reason"] for e in d["selection"]["excluded"]} == {"y": "target column", "z": "pair budget exhausted"}
    pair = d["bivariate"][0]
    assert pair["statistics"]["pearson_r"] == 1
    assert pair["statistics"]["n"] == 3
    assert pair["semantics"] == "inferred"
    assert "causation" in pair["uncertainty"]


def test_group_numeric_pair_both_orientations(make_profile):
    cfg = {"columns": {"g": {"type": "categorical"}}, "target": "x"}
    d = make_profile("g,x\nA,1\nA,3\nB,8\n", cfg).document
    assert d["bivariate"][0]["statistics"]["groups"] == [
        {"value": "A", "n": 2, "mean": 2}, {"value": "B", "n": 1, "mean": 8}]
    cfg["target"] = "g"
    assert make_profile("g,x\nA,1\nA,3\nB,8\n", cfg).document["bivariate"][0]["statistics"]["n"] == 3


def test_boolean_pair_and_override_label(make_profile):
    cfg = {"target": "x", "columns": {"g": {"type": "boolean"}, "x": {"type": "numeric"}}}
    d = make_profile("g,x\ntrue,1\nfalse,4\nTRUE,3\n", cfg).document
    assert d["bivariate"][0]["semantics"] == "human-declared"
    assert d["bivariate"][0]["statistics"]["groups"] == [{"value": "false", "n": 1, "mean": 4}, {"value": "true", "n": 2, "mean": 2}]


@pytest.mark.parametrize("cfg,expected", [({}, "no target declared"), ({"target": "y", "pair_budget": 0}, "pair budget exhausted")])
def test_no_unsolicited_pairs(make_profile, cfg, expected):
    d = make_profile("x,y\n1,2\n2,4\n", cfg).document
    assert not d["bivariate"]
    assert next(e["reason"] for e in d["selection"]["excluded"] if e["column"] == "x") == expected


def test_pair_bad_data_and_clean_decoy(make_profile):
    dirty = make_profile("x,y,label\n1,2,a\n1,4,b\n1,6,c\n", {"target": "y"}).document
    reasons = {e["column"]: e["reason"] for e in dirty["selection"]["excluded"]}
    assert reasons["x"] == "constant numeric input"
    assert reasons["label"] == "unsupported type pair: string × numeric"
    clean = make_profile("x,y\n1,2\n2,4\n3,6\n", {"target": "y"}).document
    assert len(clean["bivariate"]) == 1


def test_pairwise_finite_cases(make_profile):
    d = make_profile('x,y\n1,2\n2,4\nNaN,6\n3,""\n',
        {"target": "y", "columns": {"x": {"type": "numeric"}}}).document
    assert d["bivariate"][0]["statistics"]["n"] == 2
    assert d["bivariate"][0]["statistics"]["pearson_r"] == 1


def test_missing_optional_dependency_degrades(make_profile, monkeypatch):
    original = builtins.__import__
    def no_scipy(name, *args, **kwargs):
        if name.startswith("scipy"):
            raise ImportError("synthetic unavailable dependency")
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", no_scipy)
    d = make_profile("x,y\n1,2\n2,4\n3,6\n", {"target": "y"}).document
    assert d["bivariate"][0]["statistics"]["pearson_r"] == 1
    assert d["bivariate"][0]["statistics"]["p_value"] is None
    assert d["dependencies"]["scipy"] == "unavailable; p-values omitted"
    assert d["bivariate"][0]["statistics"]["p_value_status"] == "unavailable"


def test_optional_dependency_clean_decoy(make_profile):
    stats = pytest.importorskip("scipy.stats")
    if not hasattr(stats, "pearsonr"):
        pytest.skip("optional scipy.stats.pearsonr is unavailable")
    d = make_profile("x,y\n1,2\n2,4\n3,6\n", {"target": "y"}).document
    assert d["bivariate"][0]["statistics"]["p_value"] == pytest.approx(0, abs=1e-7)
    assert d["dependencies"]["scipy"] == "available"


def test_insufficient_and_excessive_group_decoys(make_profile):
    d = make_profile('x,y\n1,2\n"",4\n', {"target": "y"}).document
    assert d["selection"]["excluded"][0]["reason"] == "fewer than two complete finite cases"
    table = "g,x\n" + "".join(f"g{i},{i}\n" for i in range(21))
    cfg = {"target": "x", "columns": {"g": {"type": "categorical"}}}
    d = make_profile(table, cfg).document
    assert "twenty" in d["selection"]["excluded"][0]["reason"]
    clean = make_profile("g,x\nA,1\nB,2\n", cfg).document
    assert len(clean["bivariate"]) == 1
