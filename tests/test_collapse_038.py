"""Spec 038: collapsible Findings and kind groups; the rerun's updated report opens in a new tab."""
import re

from fathom.renderers import KINDS, render_html, render_markdown
from html_helpers import assert_navigation_only_script
from test_serve import running


def test_findings_and_every_kind_group_collapse_and_start_open(make_profile):
    p = make_profile("a,b,c\n1,x,true\n2,y,false\n3,z,true\n,,\n")
    html = render_html(p)
    section = html[html.index('<section id="findings">'):html.index('</section>', html.index('<section id="findings">'))]
    assert re.search(r'<details class="collapsible findings-section" open><summary><h2>Findings</h2><span class="group-count">\(\d+\)</span></summary>', section)
    for kind, title in KINDS:
        n = sum(f['kind'] == kind for f in p.document['findings'])
        assert f'<details class="collapsible kind-group" data-kind="{kind}" open><summary><h3 class="kind-heading kind-{kind}">' in section
        assert f'</h3><span class="group-count">({n:,})</span></summary>' in section
    assert section.count('<details class="collapsible') == len(KINDS) + 1
    # Nothing starts hidden, the controls need script, and the page keeps its one allowed script.
    assert not re.search(r'<details class="collapsible[^"]*"(?: data-kind="\w+")?>', html)  # none start closed
    assert '<div class="findings-tools" hidden>' in section
    assert_navigation_only_script(html)
    assert "data-findings" in html and "hashchange" in html


def test_wrapper_is_layout_only(make_profile):
    """The kind wrapper must not restyle what it contains (the inferred-italic rule skips evidence details only)."""
    p = make_profile("a,b,c\n1,x,true\n2,y,false\n3,z,true\n")
    html = render_html(p)
    assert '<em>3 columns have inferred type readings; human overrides are retained separately.</em>' in html
    assert '<em>(' not in html  # counts are plain


def test_markdown_unchanged_shape(make_profile):
    md = render_markdown(make_profile("a,b\n1,x\n2,y\n"))
    assert 'collapsible' not in md and '## Findings' in md


def test_rerun_opens_a_named_tab_and_report_is_sandboxed(tmp_path):
    with running(tmp_path) as client:
        status, headers, body = client.request()
        page = body.decode()
        assert status == 200
        assert "window.open('','fathom-updated-report')" in page and 'reportTab' in page
        assert 'tab.location.replace(answer.report)' in page
        # Opened during the click, before the profile is awaited, so pop-up blockers allow it.
        assert page.index("window.open(") < page.index("await send('rerun'")
        assert 'opens in a new tab' in page
        status, headers, body = client.request('GET', '/report')
        assert status == 200 and headers['Content-Security-Policy'].endswith('; sandbox allow-scripts')
        status, headers, _ = client.request()
        assert 'sandbox' not in headers['Content-Security-Policy']
