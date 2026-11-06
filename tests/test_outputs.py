from html_helpers import visible_text, assert_navigation_only_script
import copy
import json

import pytest

from fathom.models import ProfilingResult
from fathom.profiler import compare
from fathom.renderers import render_html, render_markdown


def test_artifact_roundtrip_and_standalone_views(make_profile, tmp_path):
    p = make_profile('x\n1\n""\n')
    path = tmp_path / "profile.json"; path.write_text(p.to_json())
    loaded = ProfilingResult.load(path)
    assert loaded.to_json() == p.to_json()
    assert render_html(loaded) == render_html(p)
    assert render_markdown(loaded) == render_markdown(p)
    html = render_html(loaded)
    for word in ("Dictionary", "Findings", "Working record", "Source", "inferred", "rule:review-v1"):
        assert word in html
    assert "<svg" in html
    assert_navigation_only_script(html)


def test_html_and_markdown_treat_input_as_text(make_profile):
    p = make_profile('x\n"<script>alert(1)</script>"\n', {"question": "[click](https://evil.invalid) <img src=x onerror=alert(1)>"})
    html = render_html(p)
    assert "<script>" not in html and "<img " not in html
    assert "&lt;script&gt;" in html
    md = render_markdown(p)
    assert "<script>" not in md
    assert all(line.startswith("    ") for line in md.splitlines() if "[click](https" in line)


def test_context_first_exact_deltas_and_identical_decoy(make_profile):
    before = make_profile('x\n1\n1\n""\n', {"context": {"snapshot_date": "2026-01-01", "source": "synthetic"}})
    after = make_profile("x,y\n1,A\n2,B\n", {"context": {"snapshot_date": "2026-01-02", "source": "synthetic revision",
        "transformations": [{"type": "filter", "description": "synthetic revision"}]}})
    c = compare(before, after)
    assert c.document["deltas"]["rows"] == -1
    assert c.document["deltas"]["missing_cells"] == -1
    assert c.document["deltas"]["duplicate_rows"] == -1
    assert c.document["deltas"]["columns_added"] == ["y"]
    for view in (render_html(c), render_markdown(c)):
        assert view.index("Contexts") < view.index("Measured deltas")
        assert "row-level lineage" in view
    same = compare(before, before).document
    assert same["context_differences"] == {}
    assert all(same["deltas"][k] == 0 for k in ("rows", "missing_cells", "duplicate_rows"))


@pytest.mark.parametrize("mutation", [
    lambda d: d.update(schema_version=3), lambda d: d.update(kind="unknown"),  # 2 is valid since spec 008
    lambda d: d.pop("overview"), lambda d: d.update(columns=[{}]),
    lambda d: d["overview"].update(rows=-1), lambda d: d["findings"][0].update(kind="fact"),
    lambda d: d.update(kind=[]), lambda d: d["columns"][0].update(inference={}),
    lambda d: d["columns"][0].update(frequencies=[{"value": "x", "count": -1}]),
    lambda d: d["columns"][0].update(meaning={"value": "invented", "generator": "rule"}),
    lambda d: d["findings"][0].update(evidence=[None]),
    lambda d: d["context"].update(snapshot_date="not-a-date"),
    lambda d: d["selection"].update(budget=True),
])
def test_bad_artifacts_rejected(make_profile, mutation):
    d = copy.deepcopy(make_profile("x\n1\n").document); mutation(d)
    with pytest.raises(ValueError):
        ProfilingResult(d)


def test_nonfinite_json_artifact_rejected(tmp_path):
    p = tmp_path / "invalid.json"; p.write_text('{"schema_version":1,"kind":"profile","bad":NaN}')
    with pytest.raises(ValueError, match="non-finite"):
        ProfilingResult.load(p)


def test_declared_source_context_and_semantics_changes(make_profile):
    before = make_profile("code\n1\n2\n")
    after = make_profile("code\n1\n2\n", {"columns": {"code": {"type": "categorical", "meaning": "supplied code"}}})
    d = compare(before, after).document
    assert d["deltas"]["shared_columns"][0]["semantics_changed"] is True
    assert d["deltas"]["shared_columns"][0]["effective_type"] == {"before": "numeric", "after": "categorical"}
