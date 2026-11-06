"""Reader-facing semantics, not a second set of analytical verdict rules."""
from html.parser import HTMLParser
from pathlib import Path
import copy,json,re,io,zipfile
import pytest
from fathom.connectors import CSVConnector
from fathom.profiler import profile
from fathom.renderers import render_html,render_markdown
from fathom.liftoff import build_liftoff,render_liftoff
from fathom.models import ProfilingResult

class Read(HTMLParser):
    def __init__(self):super().__init__();self.stack=[];self.nodes=[];self.ids=[];self.links=[];self.headings=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('id'):self.ids.append(a['id'])
        if tag=='a' and a.get('href','').startswith('#'):self.links.append(a['href'][1:])
        if re.fullmatch('h[1-6]',tag):self.headings.append(int(tag[1]))
        if tag not in {'meta','input','br','hr','img','link'}:self.stack.append((tag,a))
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i][0]==tag:self.stack=self.stack[:i];break
    def handle_data(self,text):self.nodes.append((text,list(self.stack)))
    def text(self):return ''.join(n for n,_ in self.nodes)

def fixture():
    return profile(CSVConnector(Path('tests/fixtures/liftoff/planted.csv')).load(),{'target':'amount','columns':{'group':{'type':'categorical'}},'pair_budget':4})

def test_key_findings_short_bold_inferred_and_literal_decoys():
    p=fixture();raw=p.to_json();h=render_html(p);r=Read();r.feed(h)
    strong=[t for t,s in r.nodes if any(tag=='strong' for tag,_ in s)]
    assert strong and all(len(t.split())<=8 for t in strong)
    # Aggregate complete spans, including any nested literal markup.
    class Bold(Read):
        def __init__(self):super().__init__();self.active=None;self.spans=[]
        def handle_starttag(self,tag,attrs):
            super().handle_starttag(tag,attrs)
            if tag=='strong':self.active=[]
        def handle_data(self,text):
            super().handle_data(text)
            if self.active is not None:self.active.append(text)
        def handle_endtag(self,tag):
            if tag=='strong':self.spans.append(''.join(self.active));self.active=None
            super().handle_endtag(tag)
    head=h.split('<section id="key-findings">')[1].split('</section>')[0]
    bold=Bold();bold.feed(head);assert bold.spans and all(len(t.split())<=8 for t in bold.spans)
    assert any('marked' in t for t in strong)
    assert all(any(tag=='em' for tag,_ in s) for t,s in r.nodes if '(inferred)' in t)
    assert any('inferred' in t and any(tag=='em' for tag,_ in s) for t,s in r.nodes)
    assert any(t=='amount' and any(tag=='code' for tag,_ in s) for t,s in r.nodes)
    assert p.to_json()==raw
    from fathom.report_style import runs
    assert runs('An ordinary sentence about reliable measurements.')==[('An ordinary sentence about reliable measurements.','plain')]
    assert runs('constant',columns=['constant'],verdict=True)==[('constant','literal')]
    assert '<script>' not in render_html(ProfilingResult({**p.document,'dataset':{'title':{'text':'<script>alert(1)</script>','status':'inferred'},'description':{'text':'<b>unknown</b>','status':'inferred'}}})).split('<body>')[1].split('<nav')[0]

@pytest.mark.parametrize('view',['profile','brief'])
def test_shared_navigation_has_real_destinations_counts_and_progressive_fallback(view):
    p=fixture() if view=='profile' else build_liftoff(CSVConnector(Path('tests/fixtures/liftoff/planted.csv')).load())
    h=render_html(p) if view=='profile' else render_liftoff(p)
    r=Read();r.feed(h)
    assert h.count('class="report-nav"')==1
    assert 'aria-controls="report-sections"' in h and 'aria-expanded="true"' in h
    assert '<button hidden' in h # no-script starts as a static list
    assert 'id="report-sections"' in h and 'data-nav-count' in h
    assert all(ref in r.ids for ref in r.links if ref.startswith('report-') or ref=='key-findings')
    assert len(r.ids)==len(set(r.ids))
    assert max(r.headings)<=3
    assert '@media print' in h and '.report-nav{display:none' in h
    assert 'fetch(' not in h and 'XMLHttpRequest' not in h

def test_finding_verdict_remains_outside_collapsed_provenance_and_order_unchanged():
    p=fixture();h=render_html(p);r=Read();r.feed(h)
    for f in p.document['findings']:
        # Repetition summaries may hide the original; all source messages remain.
        assert f['message'] in ReadText(h)
    for t,s in r.nodes:
        if any(tag=='article' and 'finding' in a.get('class','') for tag,a in s) and 'Generator:' in t:
            assert any(tag=='details' and 'open' not in a for tag,a in s)
    assert h.index('Key findings')<h.index('<h2>Dictionary')<h.index('<h2>Provenance')<h.index('Dataset summary')
    assert render_html(ProfilingResult(json.loads(p.to_json())))==h
    brief=Read();brief.feed(render_liftoff(build_liftoff(CSVConnector(Path('tests/fixtures/liftoff/planted.csv')).load())))
    for t,stack in brief.nodes:
        if re.match(r'(Automatic|Provisional) · rule ',t):
            assert any(tag=='details' and 'open' not in attrs for tag,attrs in stack)

def ReadText(h):
    r=Read();r.feed(h);return r.text()

def test_markdown_and_panel_share_typographic_roles():
    from fathom.panel import build_panel
    from fathom.panel_view import html,markdown
    p=fixture();md=render_markdown(p)
    assert md.startswith('# *planted*')
    assert '*\\(inferred\\)*' in md and '`amount`' in md and '**marked**' in md
    result=build_panel(CSVConnector(Path('tests/fixtures/years/panel.csv')).load(),{'series':['entity','candidate'],'time':'year','value':'value','period':'year','date_format':'YEAR'},Path('.'))
    raw=result.to_json();h=html(result)
    assert '<strong>not estimable</strong>' in h and '<code>rule:panel-v1</code>' in h
    assert '<strong>training only</strong>' not in h
    assert '**not estimable**' in markdown(result)
    assert result.to_json()==raw

def test_same_roles_in_export_runs_and_deterministic_optional_files(tmp_path):
    pytest.importorskip('reportlab');pytest.importorskip('pptx')
    from fathom.exports import pdf_bytes,pptx_bytes
    path=tmp_path/'fixed.csv';path.write_text('fixed,x\n'+'\n'.join('1,'+str(i) for i in range(10))+'\n')
    p=profile(CSVConnector(path).load());before=p.to_json()
    a,_=pdf_bytes(p.document);b,_=pptx_bytes(p.document)
    assert a==pdf_bytes(p.document)[0] and b==pptx_bytes(p.document)[0]
    # Inspect real presentation text run properties, not screenshots alone.
    from pptx import Presentation
    deck=Presentation(io.BytesIO(b));assert deck.slides[0].shapes.title.text_frame.paragraphs[0].font.italic
    runs=[r for s in deck.slides for sh in s.shapes if sh.has_text_frame for para in sh.text_frame.paragraphs for r in para.runs]
    assert any(r.font.bold and 'constant' in r.text for r in runs)
    assert any(r.font.italic and 'inferred' in r.text for r in runs)
    assert any(r.font.name=='Courier New' for r in runs)
    assert any(s._element.xpath('.//a:buChar') for s in deck.slides)
    assert b'BitstreamVeraSans-Bold' in a and b'BitstreamVeraSans-Oblique' in a
    assert p.to_json()==before

def test_declared_and_inferred_identity_and_literal_values_are_distinct():
    from fathom.report_style import html_text,runs
    p=fixture();p.document['dataset']['description']={'text':'A plain declaration.','status':'human'}
    h=render_html(p);assert '<p>A plain declaration.</p>' in h
    p.document['dataset']['description']['status']='inferred'
    h=render_html(p);assert '<em>A plain declaration.</em>' in h
    assert html_text('constant',literal=True)=='<code>constant</code>'
    assert html_text('(inferred)')=='<em>(inferred)</em>'
    assert runs('"constant"',verdict=True)==[('"constant"','literal')]
    assert runs('"constant label"',columns=['label'],verdict=True)==[('"constant label"','literal')]
    assert '<strong>constant</strong>' not in html_text('Dataset constant columns: none flagged.',verdict=True)
    assert '<strong>not constant</strong>' in html_text('x is not constant.',verdict=True)
    assert '<strong>' not in html_text('A constant label is a literal value.',columns=['constant'],verdict=False)
    assert 'gap <strong>14.71</strong> ≥ SD 13.81 → <strong>marked</strong>'==html_text('gap 14.71 ≥ SD 13.81 → marked',verdict=True)
    assert html_text('gap 1 < SD 2 → not marked',verdict=True).endswith('<strong>not marked</strong>')

def test_inference_and_evidence_are_not_confused_and_small_lists_remain_prose():
    from fathom.report_style import style_html
    from fathom.verdicts import headlines_html
    from fathom.renderers import readable_html
    h=style_html('<article class="finding kind-hypothesis"><p>Meaning is unknown.</p><details><summary>Evidence</summary><p>Observed raw count: 4.</p></details></article>')
    assert '<em>Meaning is unknown.</em>' in h and '<p>Observed raw count: 4.</p>' in h
    assert '<ul>' not in readable_html(['a','b']) and '<ul>' in readable_html(['a','b','c'])
    d={'findings':[{'id':'x','kind':'observation','message':'A measured fact.','rule':'dummy'}]}
    assert '<ul>' not in headlines_html(d)
    d['findings']*=3
    for i,f in enumerate(d['findings']):d['findings'][i]={**f,'id':str(i)}
    assert headlines_html(d).count('<li>')==3
