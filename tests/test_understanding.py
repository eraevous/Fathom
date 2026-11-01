"""Purpose-facing checks use a violation and a clean/known-context decoy."""

from pathlib import Path

import pytest

from fathom.config import load_config, validate_config
from fathom.connectors import CSVConnector
from fathom.models import SchemaContract
from fathom.profiler import profile

F = Path(__file__).parent / "fixtures"


def test_review_actions_and_clean_decoy():
    dirty = profile(CSVConnector(F / "review.csv").load(), load_config(F / "review.yaml")).document
    clean = profile(CSVConnector(F / "clean.csv").load()).document
    assert dirty["overview"] == {"rows": 4, "columns": 5, "missing_cells": 1, "duplicate_rows": 1}
    assert [x for x in clean["findings"] if x["kind"] == "action"] == []
    observations = {f["id"]: f for f in dirty["findings"] if f["kind"] == "observation"}
    actions = [x for x in dirty["findings"] if x["kind"] == "action"]
    assert len(actions) == 2
    for action in actions:
        assert action["evidence"][0]["finding"] in observations
        assert action["generator"] == "rule:review-v1"
        assert action["uncertainty"]
        assert action["provenance"]["source_sha256"] == dirty["source"]["sha256"]
    assert dirty["working_record"]["decisions"][0]["rationale"]


def test_numeric_accuracy(make_profile):
    d = make_profile('x\n-2\n0\n2\n4\n""\n', {"columns": {"x": {"type": "numeric"}}}).document
    assert d["columns"][0]["statistics"]["mean"] == 1
    stats = d["columns"][0]["statistics"]
    assert stats == {"valid": 4, "invalid": 0, "min": -2, "max": 4, "mean": 1,
                     "median": 1, "population_std": pytest.approx(5 ** 0.5), "zeros": 1, "negatives": 1}
    assert d["columns"][0]["missing"] == 1


@pytest.mark.parametrize("values,expected", [
    (["1", "2", "3"], "numeric"), (["true", "false"], "boolean"),
    (["2026-01-01", "2026-01-02"], "temporal"), (["A", "A", "B"], "categorical"),
    (["001", "002", "003"], "string"), (["red", "green", "blue"], "string"),
    (["NaN", "inf", "-inf"], "string"),
])
def test_inferred_routing(make_profile, values, expected):
    c = make_profile("x\n" + "\n".join(values) + "\n").document["columns"][0]
    assert c["inference"]["type"] == expected
    assert c["effective_type"] == expected
    assert c["inference"]["confidence"]
    assert c["inference"]["reasons"] and c["inference"]["alternatives"]


def test_override_retains_inference_and_human_meaning(make_profile):
    d = make_profile("code\n1\n2\n1\n", {"columns": {"code": {"type": "categorical", "meaning": "Human code"}}}).document
    c = d["columns"][0]
    assert c["inference"]["type"] == "numeric"
    assert c["effective_type"] == "categorical"
    assert c["override"]["generator"] == "human"
    assert c["meaning"] == {"value": "Human code", "generator": "human"}
    assert "mean" not in c["statistics"]


def test_unknowns_and_declared_decoy(make_profile):
    unknown = make_profile("x\n1\n2\n").document
    assert unknown["purpose"]["mode"] == "documentation_qa"
    questions = " ".join(x["message"] for x in unknown["findings"] if x["kind"] == "question")
    for term in ("row unit", "generating process", "missingness mechanism", "meaning"):
        assert term in questions
    known = make_profile("x\n1\n2\n", {"row_unit": "one synthetic reading", "generating_process": "authored",
        "missingness_mechanism": "none in this fixture", "columns": {"x": {"meaning": "synthetic measurement"}}}).document
    assert not [f for f in known["findings"] if f["kind"] == "question"]
    assert known["working_record"]["generator"] == "human"


@pytest.mark.parametrize("typ,bad,good", [("numeric", "NaN", "3"), ("temporal", "yesterday", "2026-01-01"), ("boolean", "maybe", "true")])
def test_invalid_override_violation_and_decoy(make_profile, typ, bad, good):
    cfg = {"columns": {"x": {"type": typ}}}
    dirty = make_profile(f"x\n{bad}\n{good}\n", cfg).document
    clean = make_profile(f"x\n{good}\n", cfg).document
    assert dirty["columns"][0]["statistics"]["invalid"] == 1
    assert any(f["id"].endswith("invalid-review") for f in dirty["findings"])
    assert not any(f["id"].endswith("invalid-review") for f in clean["findings"])


def test_null_policy_and_header_only(make_profile):
    d = make_profile('x\nNA\nnull\n0\n" "\n').document
    assert d["columns"][0]["missing"] == 1
    assert d["columns"][0]["distinct"] == 3
    empty = make_profile("x,y\n").document
    assert empty["overview"]["rows"] == 0
    assert empty["columns"][0]["statistics"] == {}


@pytest.mark.parametrize("csv", ["", "x,x\n1,2\n", "x, \n1,2\n", "x,y\n1\n", 'x\n"unterminated'])
def test_bad_csv(csv, tmp_path):
    import csv as csv_module
    p = tmp_path / "bad.csv"; p.write_text(csv)
    with pytest.raises((ValueError, csv_module.Error)):
        CSVConnector(p).load()


@pytest.mark.parametrize("cfg", [
    {"typo": 1}, {"pair_budget": True}, {"pair_budget": 21}, {"columns": {"absent": {}}},
    {"context": {"snapshot_date": "today"}}, {"columns": {"x": {"type": "magic"}}},
    {"decisions": [{"decision": "Proceed"}]}, {"context": {"transformations": ["filter"]}},
    {"schema": {"mode": "long"}}, {"schema": {"key": ["x", "x"]}},
])
def test_invalid_configuration(cfg):
    with pytest.raises(ValueError):
        validate_config(cfg, ["x"])


def test_wide_schema_and_source(tmp_path):
    p = tmp_path / "source.csv"; p.write_text("id,x\n001,1\n")
    g = CSVConnector(p, SchemaContract(key=("id",))).load()
    assert g.frame.iloc[0, 0] == "001"
    assert g.schema.mode == "wide"
    assert len(g.source["sha256"]) == 64


def test_temporal_boolean_and_frequency_accuracy(make_profile):
    d = make_profile("date,flag,category\n2026-02-03,true,Z\n2026-01-01,false,A\n2026-02-03,TRUE,Z\n").document
    assert d["columns"][0]["statistics"] == {"valid": 3, "invalid": 0, "min": "2026-01-01", "max": "2026-02-03"}
    assert d["columns"][1]["statistics"] == {"valid": 3, "invalid": 0, "true": 2, "false": 1}
    assert d["columns"][2]["frequencies"] == [{"value": "Z", "count": 2}, {"value": "A", "count": 1}]


def test_large_finite_and_nonfinite_values_remain_json_safe(make_profile):
    p = make_profile("x\n1e308\n-1e308\nInfinity\n", {"columns": {"x": {"type": "numeric"}}})
    assert p.document["columns"][0]["statistics"]["valid"] == 2
    assert p.document["columns"][0]["statistics"]["mean"] == 0
    assert "NaN" not in p.to_json()


def test_duplicate_yaml_keys_rejected_and_clean_decoy(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text("pair_budget: 1\npair_budget: 2\n")
    with pytest.raises(ValueError, match="unique"):
        load_config(p)
    p.write_text("pair_budget: 1\ncontext:\n  snapshot_date: 2026-01-01\n")
    assert load_config(p)["context"]["snapshot_date"] == "2026-01-01"
