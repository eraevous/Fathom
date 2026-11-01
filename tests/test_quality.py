"""Exact quality evidence plus clean decoys; builder acceptance is not owner acceptance."""

from pathlib import Path
import csv
import io
from html import unescape

import pytest

from fathom.connectors import CSVConnector
from fathom.profiler import profile
from fathom.renderers import render_html, render_markdown

F = Path(__file__).parent / "fixtures" / "quality"


def table(names, rows):
    f = io.StringIO(); w = csv.writer(f); w.writerow(names); w.writerows(rows)
    return f.getvalue()


def rules(doc, rule):
    return [f for f in doc["findings"] if f.get("rule") == rule and f["kind"] == "observation"]


@pytest.mark.parametrize("values,clean,rule", [
    ([20, 21, 22, 23, 24, 999], [20, 21, 22, 23, 24, 25], "sentinel"),
    ([0, 1, 2, 3, 4, -1], [-5, -4, -3, -2, -1, 0], "sentinel"),
    (["real", "dummy", "live"], ["real", "testimony", "live"], "dummy"),
    (["NA", "live", "ready"], ["NATO", "live", "ready"], "placeholder"),
    (["yes"] * 20 + ["no"], ["yes", "no"] * 11, "dominant"),
    (["x"] * 5, ["x", "y"] * 3, "constant"),
    ([1] * 9 + [1000], list(range(10)), "skew"),
    (["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-08"],
     ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"], "temporal_gap"),
])
def test_diagnostic_violation_and_decoy(make_profile, values, clean, rule):
    dirty = make_profile(table(["x"], [[v] for v in values])).document
    decoy = make_profile(table(["x"], [[v] for v in clean])).document
    matches = rules(dirty, rule)
    assert matches and not rules(decoy, rule)
    for f in matches:
        assert f["evidence"] and f["uncertainty"] and f["generator"] == "rule:quality-v1"
        assert f["message"] in unescape(render_html(profile_result(dirty)))
        assert any(a["kind"] == "action" and {"finding": f["id"]} in a["evidence"] for a in dirty["findings"])
    if rule in {"sentinel", "dummy", "placeholder"}:
        assert any(f["kind"] == "hypothesis" and f.get("rule") == rule for f in dirty["findings"])


def profile_result(doc):
    from fathom.models import ProfilingResult
    return ProfilingResult(doc)


def test_structural_group_violations_and_decoys(make_profile):
    dirty = make_profile(table(["a", "copy", "scale", "g", "recode"],
        [[i, i, 2*i+7, "A" if i%2 else "B", "north" if i%2 else "south"] for i in range(8)])).document
    assert rules(dirty, "duplicate_columns")
    assert rules(dirty, "lockstep_columns")
    assert dirty["dataset_summary"]["duplicate_columns"] == 1
    clean = profile(CSVConnector(F / "clean.csv").load()).document
    assert not rules(clean, "duplicate_columns") and not rules(clean, "lockstep_columns")


def test_missing_patterns_and_group_rates(make_profile):
    rows = [[None if i < 4 else i, None if i < 4 else i+10, "A" if i < 5 else "B"] for i in range(10)]
    d = make_profile(table(["a", "b", "group"], rows)).document
    assert rules(d, "co_missing")
    assert rules(d, "conditional_missingness")
    pair = next(p for p in d["bivariate"] if p["method"] == "missingness_by_group" and p["left"] == "a")
    assert pair["statistics"]["spread"] == .8
    assert pair["statistics"]["groups"] == [{"value": "A", "n": 5, "missing": 4, "rate": .8}, {"value": "B", "n": 5, "missing": 0, "rate": 0}]
    clean_rows = [[None if i in (0,5) else i, i, "A" if i < 5 else "B"] for i in range(10)]
    clean = make_profile(table(["a", "b", "group"], clean_rows)).document
    assert not rules(clean, "co_missing") and not rules(clean, "conditional_missingness")


def test_complete_summary_exact_and_links(make_profile):
    d = make_profile('a,b,c\n1,1,X\n2,2,Y\n3,3,Z\n4,4,""\n5,5,W\n').document
    s = d["dataset_summary"]
    assert s["complete_rows"] == {"count": 4, "share": .8}
    assert s["complete_columns"] == {"count": 2, "share": pytest.approx(2/3)}
    assert s["missing_cells"] == {"count": 1, "share": pytest.approx(1/15)}
    assert s["inferred_types"] == {"numeric": 2, "string": 1}
    assert s["duplicate_columns"] == 1
    ids = {f["id"] for f in d["findings"]}
    assert all(ref in ids for refs in s["finding_links"].values() for ref in refs)


def test_empty_all_missing_and_unique_id_decoys(make_profile):
    empty = make_profile("a,b\n").document["dataset_summary"]
    assert empty["complete_rows"] == {"count": 0, "share": None}
    assert empty["complete_columns"] == {"count": 2, "share": 1}
    d = make_profile('a,b\n"",""\n"",""\n').document
    assert not rules(d, "constant")
    unique = make_profile(table(["a", "b"], [[f"id{i}", f"other{i}"] for i in range(8)])).document
    assert not rules(unique, "lockstep_columns")


def test_workshop_report_finds_planted_families_and_clean_decoy():
    result = profile(CSVConnector(F / "workshop.csv").load())
    d = result.document
    for rule in ("sentinel", "dummy", "dominant", "constant", "duplicate_columns", "lockstep_columns", "co_missing", "conditional_missingness", "temporal_gap", "skew"):
        assert rules(d, rule), rule
    assert d["overview"]["duplicate_rows"] == 1
    text = render_html(result) + render_markdown(result)
    for phrase in ("999", "dummy", "mean", "median", "north", "2026-01-20", "2026-01-31"):
        assert phrase in text
    assert d["dataset_summary"]["complete_rows"]["count"] == 28
    clean = profile(CSVConnector(F / "clean.csv").load()).document
    assert not [f for f in clean["findings"] if f["kind"] == "action"]


def test_relevance_stronger_later_and_column_order(make_profile):
    rows = [[i%3, i*2+(i%2), i] for i in range(12)]
    d = make_profile(table(["weak", "strong", "target"], rows), {"target": "target", "pair_budget": 1}).document
    assert d["selection"]["selected"] == [["strong", "target"]]
    swapped = make_profile(table(["strong", "weak", "target"], [[r[1],r[0],r[2]] for r in rows]), {"target": "target", "pair_budget": 1}).document
    assert swapped["selection"]["selected"] == d["selection"]["selected"]
    assert "strength" in d["selection"]["ranking_rule"]


def test_shared_budget_zero_and_redundant_candidates(make_profile):
    rows = [[i*2+(i%2), i*2+(i%2), 1 if i<19 else 2, i, None if i<10 else i] for i in range(20)]
    cfg = {"target": "target", "pair_budget": 1}
    d = make_profile(table(["a", "a_copy", "flat", "target", "sparse"], rows), cfg).document
    assert len(d["bivariate"]) == 1
    reasons = " ".join(x["reason"] for x in d["selection"]["excluded"])
    assert "near-duplicate" in reasons and "near-constant" in reasons
    cfg["pair_budget"] = 0
    zero = make_profile(table(["a", "a_copy", "flat", "target", "sparse"], rows), cfg).document
    assert not zero["bivariate"] and not rules(zero, "conditional_missingness")
    assert zero["quality"]["coverage"]["eligible_missingness_candidates"] > 0


def test_small_exact_copy_cannot_consume_budget(make_profile):
    d=make_profile('a,target\n1,1\n2,2\n',{'target':'target'}).document
    assert not d['bivariate']
    assert 'near-duplicate' in next(x['reason'] for x in d['selection']['excluded'] if x['column']=='a')


def test_human_type_override_controls_numeric_diagnostics(make_profile):
    csv=table(['code'],[[x] for x in [20,21,22,23,24,999]])
    inferred=make_profile(csv).document
    declared=make_profile(csv,{'columns':{'code':{'type':'categorical'}}}).document
    assert rules(inferred,'sentinel') and not rules(declared,'sentinel')
    assert declared['columns'][0]['inference']['type']=='numeric'


def test_wide_screening_limits_are_explicit(make_profile):
    names=[f'c{i:02}' for i in range(70)]
    rows=[[f'v{i}_{j}' for j in range(70)] for i in range(6)]
    d=make_profile(table(names,rows)).document
    cov=d['quality']['coverage']
    assert cov['near_duplicate_comparisons']==2000
    assert cov['omitted_near_duplicate_candidates']>0
    assert cov['omitted_grouping_columns']==50
    assert len(cov['grouping_columns_excluded'])==50


def test_later_builder_holdout_report_evidence():
    result=profile(CSVConnector(F/'holdout.csv').load())
    d=result.document
    assert d['overview']=={'rows':31,'columns':16,'duplicate_rows':1,'missing_cells':20}
    assert d['dataset_summary']['complete_rows']=={'count':21,'share':pytest.approx(21/31)}
    near=rules(d,'near_duplicate_columns')
    assert near and near[0]['evidence'][0]['value']['agreement']==pytest.approx(30/31)
    assert rules(d,'conditional_missingness') and rules(d,'temporal_gap')
    text=render_html(result)+render_markdown(result)
    for value in ('999','test_7','near_a','near_b','2026-03-10','2026-03-13'):
        assert value in text


def test_shared_absence_is_not_near_copy_evidence():
    d=profile(CSVConnector(F/'shared-absence.csv').load()).document
    assert rules(d,'co_missing')
    assert not rules(d,'near_duplicate_columns')
    assert not d['quality']['value_exclusions']
    targeted=profile(CSVConnector(F/'shared-absence.csv').load(),{'target':'b'}).document
    assert targeted['selection']['selected']==[['a','b']]
