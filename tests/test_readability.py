from copy import deepcopy
from html import unescape
from pathlib import Path

import pytest

from fathom.connectors import CSVConnector
from fathom.models import ProfilingResult
from fathom.profiler import profile
from fathom.renderers import render_html, render_markdown

F = Path(__file__).parent / "fixtures" / "quality"


def test_person_first_order_and_no_primary_json_dump():
    p = profile(CSVConnector(F/"workshop.csv").load())
    for view in (render_html(p), render_markdown(p)):
        titles = ("Dataset summary", "Usefulness", "What the data cannot tell", "Findings", "Relations", "Dictionary", "Provenance")
        order = [view.index(("<h3>" if s in titles[1:3] else "<h2>")+s+"</h" if view.startswith("<!doctype") else ("### " if s in titles[1:3] else "## ")+s) for s in titles]
        assert order == sorted(order)
        assert '"source_sha256"' not in view and '"effective_type"' not in view
    html = render_html(p)
    assert '<pre>' not in html
    assert '<script' not in html and 'src="http' not in html
    assert '<svg' in html


def test_native_global_toggle_and_all_original_items(make_profile):
    p = make_profile("a,b,c\n1,x,true\n2,y,false\n3,z,true\n")
    html = render_html(p)
    assert 'id="full-view"' in html and 'type="checkbox"' in html
    assert 'id="full-view" checked' not in html
    assert 'for="full-view"' in html and 'Show full per-item detail' in html
    assert '#full-view:checked' in html
    assert 'class="summary-view"' in html and 'class="full-view"' in html
    assert '3 columns have inferred type readings' in html
    assert 'Domain meaning is unknown for 3 columns' in html
    for finding in p.document["findings"]:
        assert f'id="{finding["id"]}"' in html
        assert finding["message"] in unescape(html)
    assert '<details' in html and 'Evidence and uncertainty' in html


def test_summary_links_and_artifact_only_roundtrip(tmp_path):
    p = profile(CSVConnector(F/"workshop.csv").load())
    saved = tmp_path/"artifact.json";saved.write_text(p.to_json())
    r = ProfilingResult.load(saved)
    assert render_html(r) == render_html(p)
    assert render_markdown(r) == render_markdown(p)
    html = render_html(r)
    for refs in r.document["dataset_summary"]["finding_links"].values():
        for ref in refs:
            assert f'href="#{ref}"' in html and f'id="{ref}"' in html


def test_legacy_artifact_unknown_complete_rows():
    old = ProfilingResult.load(F/"legacy-profile.json")
    assert "dataset_summary" not in old.document
    for view in (render_html(old),render_markdown(old)):
        assert 'Unavailable in this saved artifact' in view
        assert 'Dictionary' in view and 'What the data cannot tell' in view


@pytest.mark.parametrize("mutation", [
    lambda d: d["dataset_summary"].update(rows=-1),
    lambda d: d["dataset_summary"]["complete_rows"].update(share=2),
    lambda d: d["dataset_summary"]["finding_links"].update(rows=["nonexistent"]),
    lambda d: d["dataset_summary"].pop("inferred_types"),
    lambda d: d.update(quality={}),
    lambda d: d["dataset_summary"].update(duplicate_groups=[1]),
    lambda d: d["dataset_summary"].update(constant_columns=["absent"]),
    lambda d: d["dataset_summary"].update(rows=100),
])
def test_invalid_additions_rejected(make_profile,mutation):
    d=deepcopy(make_profile("x\n1\n2\n").document);mutation(d)
    with pytest.raises(ValueError):ProfilingResult(d)


def test_hostile_text_stays_text_in_both_views(make_profile):
    p=make_profile('"<img src=x onerror=alert(1)>"\n"<script>alert(1)</script>"\n')
    html=render_html(p)
    assert '<img ' not in html and '<script>' not in html
    assert '&lt;img' in html and '&lt;script' in html
    md=render_markdown(p)
    assert '<img ' not in md and '<script>' not in md
