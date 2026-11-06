"""Human-readable quantities and summary view contracts; no new analytic tests."""
from pathlib import Path
import copy,json,re,io
import pytest
from fathom.connectors import CSVConnector
from fathom.config import load_config,validate_config
from fathom.profiler import profile
from fathom.models import ProfilingResult
from fathom.renderers import render_html,render_markdown
from html_helpers import visible_text
FIX=Path('tests/fixtures/summary')

def result():return profile(CSVConnector(FIX/'mixed.csv').load(),load_config(FIX/'config.yaml'))

def test_numeric_contrast_nested_quantities_preserves_all_gates_and_decoy():
    from fathom.finding_view import finding_tree,html_tree,comparison_count
    p=result();fs=[f for f in p.document['findings'] if f.get('rule')=='target_group_contrast' and f['kind']=='observation'];assert fs
    f=fs[0];before=copy.deepcopy(f);tree=finding_tree(f);h=html_tree(tree)
    assert '<ul ' in h and '<strong>marked</strong>' in render_html(p)
    assert any('group:' in s for s in tree['children']) and any('rest:' in s for s in tree['children'])
    assert all(comparison_count(s)<=1 for s in [tree['text'],*tree['children']])
    for g in f['evidence'][0]['value']['gates']:
        if g['status']=='computed':assert ('marked' if g['marked'] else 'not marked') in visible_text(h)
    assert f==before
    # Existing failed gates in the middle group must remain failed, never recreated from unsigned gaps.
    mid=next(g for s in p.document['target_analysis']['groups'] for g in s['groups'] if g['value']=='middle')
    assert not mid['contrasts']
    fake=copy.deepcopy(f);fake['evidence'][0]['value']=mid
    t=finding_tree(fake);assert 'not marked' in ' '.join([t['text'],*t['children']])

def test_generic_comparison_lines_and_literal_identifiers_are_safe():
    from fathom.finding_view import finding_tree,comparison_count
    f={'id':'paired','kind':'observation','message':'Training mean = 3; evaluation mean = 4; gap 1 ≥ SD 0.5; observed = 8 vs expected = 9.','columns':[],'evidence':[]}
    t=finding_tree(f)
    assert t['children'] and all(comparison_count(s)<=1 for s in [t['text'],*t['children']])
    assert all(str(x) in ' '.join(t['children']) for x in [3,4,1,8,9])
    assert comparison_count('`x=y` and "a≥b" are literal labels.')==0
    named={'id':'named','kind':'observation','columns':['x=y'],'message':'x=y mean = 3; rest mean = 4.','evidence':[]}
    assert any('x=y' in line for line in finding_tree(named)['children'])
    clean={'id':'q','kind':'question','message':'What is the row unit?','evidence':[]}
    assert finding_tree(clean)=={'text':clean['message'],'children':[]}

def test_summaries_use_stored_metrics_links_and_no_new_measurements():
    from fathom.summary_view import summary_tables,transpose
    p=result();before=p.to_json();tables=summary_tables(p.document)
    assert {t['type'] for t in tables}=={c['effective_type'] for c in p.document['columns']}
    n=next(t for t in tables if t['type']=='numeric');assert n['headers'][:4]==['Column','n','Missing %','Distinct']
    row=next(r for r in n['rows'] if r[0]=='amount');assert row[1]==59 and row[2]==pytest.approx(1/60)
    c=next(c for c in p.document['columns'] if c['name']=='amount');assert row[4]==c['statistics']['mean']
    text=next(t for t in tables if t['type']=='string');note=next(r for r in text['rows'] if r[0]=='note')
    assert note[4]==pytest.approx(1/60) # top1, not top10 coverage
    empty=next(r for r in text['rows'] if r[0]=='empty')
    assert empty[1]==0 and empty[2]==1 and empty[4]=='Not stored'
    coord=next(t for t in tables if t['type']=='latitude');assert 'Not stored' in coord['rows'][0]
    time=next(t for t in tables if t['type']=='temporal');assert any('parse' in h.lower() for h in time['headers'])
    for t in tables:assert transpose(transpose(t))==t
    h=render_html(p);assert h.index('Key findings')<h.index('Distribution summaries')<h.index('<h2>Dictionary')
    assert 'href="#dictionary-column-0"' in h and 'id="dictionary-column-0"' in h
    assert 'data-transpose' in h and '<button hidden' in h and '<svg' in h
    assert p.to_json()==before

def test_orientation_is_out_of_band_strict_and_same_in_exports():
    raw={'report':{'summary_orientation':'metrics_as_rows'}}
    clean=validate_config(raw);assert 'report' not in clean and raw['report']['summary_orientation']=='metrics_as_rows'
    for value in [None,True,{},'wrong']:
        with pytest.raises(ValueError):validate_config({'report':{'summary_orientation':value}})
    with pytest.raises(ValueError):validate_config({'report':{'mystery':True}})
    a=result();cfg=load_config(FIX/'config.yaml');cfg['report']={'summary_orientation':'metrics_as_rows'}
    b=profile(CSVConnector(FIX/'mixed.csv').load(),cfg);assert a.to_json()==b.to_json()
    opts={'summary_orientation':'metrics_as_rows'}
    h=render_html(a,report=opts);md=render_markdown(a,report=opts)
    assert 'data-orientation="metrics_as_rows"' in h and '| Metric |' in md
    pytest.importorskip('pptx');pytest.importorskip('reportlab')
    from fathom.exports import export_bundle
    files,status=export_bundle(a,['pdf','pptx'],report=opts)
    from pptx import Presentation
    deck=Presentation(io.BytesIO(files['report.pptx']))
    assert any(sh.has_table and sh.table.cell(0,0).text=='Metric' for s in deck.slides for sh in s.shapes)
    assert len(deck.slides)<=12

def test_palette_exact_tokens_actual_text_and_graphic_roles():
    from fathom.palette import THEMES,KIND_COLOURS,CATEGORICAL,DARK_CATEGORICAL,contrast,status_hue_distance
    assert THEMES['light']['surface'].lower()=='#f2ede3' and THEMES['dark']['ink'].lower()=='#f0f0e9'
    assert THEMES['light']['grid'].lower()=='#c9c2b4'
    for theme,series in [('light',CATEGORICAL),('dark',DARK_CATEGORICAL)]:
        for bg in [THEMES[theme]['panel'],THEMES[theme]['surface']]:
            for c in ['ink','muted','link',*[]]:assert contrast(THEMES[theme][c],bg)>=4.5
            for c in KIND_COLOURS[theme].values():assert contrast(c,bg)>=4.5
            for c in [THEMES[theme][k] for k in ['accent','accent_faint','band']]+series:assert contrast(c,bg)>=3
        assert all(status_hue_distance(c)>=25 for c in series)
    from fathom.target_marks import plot_marks
    p=result()
    for ch in p.document['target_analysis']['charts']:
        for kind,*v in plot_marks(ch)[2]:
            color=v[4] if kind in {'line','rect'} else v[3] if kind=='circle' else None
            if color:assert min(contrast(color,THEMES['light'][bg]) for bg in ['surface','panel'])>=3
    assert 'opacity=".65"' not in render_html(p)


def test_actual_finding_lines_have_at_most_one_comparison():
    from html.parser import HTMLParser
    class Lines(HTMLParser):
        def __init__(self):super().__init__();self.active=False;self.blocks=[];self.code=0;self.lines=[]
        def handle_starttag(self,tag,attrs):
            if tag=='article' and 'finding' in dict(attrs).get('class','').split():self.active=True
            if not self.active:return
            if tag=='code':self.code+=1
            if tag in {'article','div','p','li','ul','summary','dd','dt'}:self.blocks.append([])
        def handle_endtag(self,tag):
            if not self.active:return
            if tag=='code':self.code-=1
            if tag in {'article','div','p','li','ul','summary','dd','dt'} and self.blocks:self.lines.append(''.join(self.blocks.pop()))
            if tag=='article':self.active=False
        def handle_data(self,text):
            if self.active and self.blocks and not self.code:self.blocks[-1].append(text)
    p=result();h=render_html(p);lines=Lines();lines.feed(h)
    operators=re.compile(r'==|!=|>=|<=|=|≥|\bvs\b')
    assert lines.lines
    assert all(len(operators.findall(line))<=1 for line in lines.lines),[line for line in lines.lines if len(operators.findall(line))>1]
    md=render_markdown(p).split('## Findings',1)[1].split('## Temporal',1)[0].split('## Relations',1)[0]
    # Source values may contain literal operators; code spans are not comparisons.
    for line in md.splitlines():
        if line.lstrip().startswith('- ') and not '`' in line:
            assert len(operators.findall(line))<=1,line


def test_empty_legacy_and_hostile_summary_links_remain_truthful():
    from fathom.summary_view import summary_tables,summary_html,summary_markdown
    assert summary_tables({'columns':[]})==[] and summary_html({'columns':[]})==''
    p=result();d=copy.deepcopy(p.document);d['columns'][0]['name']='<img src=x onerror=alert(1)>'
    d['columns'][0].pop('univariate',None)
    for out in [summary_html(d),summary_markdown(d)]:assert '<img ' not in out and '&lt;img' in out
    t=summary_tables(d)[0];assert 'Not stored' in t['rows'][0]


def test_export_native_marks_use_explicit_accessible_palette():
    pytest.importorskip('pptx');pytest.importorskip('reportlab')
    from fathom.exports import export_bundle
    from fathom.palette import THEMES,contrast
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE
    from pptx.dml.color import MSO_COLOR_TYPE
    files,_=export_bundle(result(),['pptx'],deck='full');deck=Presentation(io.BytesIO(files['report.pptx']))
    used=[]
    for slide in deck.slides:
        for shape in slide.shapes:
            if shape.shape_type==MSO_SHAPE_TYPE.AUTO_SHAPE:
                assert shape.fill.fore_color.type==MSO_COLOR_TYPE.RGB
                used.append('#'+str(shape.fill.fore_color.rgb))
            if shape.has_chart:
                for series in shape.chart.series:
                    assert series.format.line.color.type==MSO_COLOR_TYPE.RGB
                    used.append('#'+str(series.format.line.color.rgb))
    assert used and all(contrast(c,THEMES['light']['panel'])>=3 and contrast(c,THEMES['light']['surface'])>=3 for c in used)


def test_multiple_rate_contrasts_and_small_group_caution_keep_source_counts():
    from fathom.target import summarize_groups
    from fathom.finding_view import finding_tree
    group=summarize_groups([['A','yes']]*2+[['B','no']]*20,[{'name':'group','effective_type':'categorical'},{'name':'label','effective_type':'categorical'}],0,1)['groups'][0]
    assert group['small'] and len(group['contrasts'])==2
    source=copy.deepcopy(group)
    f={'id':'rates','kind':'observation','rule':'target_group_contrast','columns':['group','label'],'message':'Stored contrasts','evidence':[{'value':group}]}
    t=finding_tree(f);text=' '.join(t['children'])
    assert '100.0%' in text and '0.0%' in text and '(n = 2)' in text and '(n = 20)' in text
    assert 'too small to read reliably' in text and 'not marked' in text
    assert source==group


def test_saved_render_orientation_and_export_absence_degrade(tmp_path,monkeypatch):
    import subprocess,sys,os
    p=result();artifact=tmp_path/'profile.json';artifact.write_text(p.to_json());cfg=tmp_path/'view.yaml';cfg.write_text('report: {summary_orientation: metrics_as_rows}\n')
    out=tmp_path/'render'
    command=[sys.executable,'tests/offline_runner.py','render',str(artifact),'--config',str(cfg),'--out',str(out)]
    r=subprocess.run(command,env={**os.environ,'PYTHONPATH':'src','FATHOM_DENY_NETWORK':'1'},capture_output=True)
    assert r.returncode==0,r.stderr.decode()
    assert 'data-orientation="metrics_as_rows"' in (out/'report.html').read_text()
    assert artifact.read_text()==p.to_json()
    from fathom.exports import export_bundle
    monkeypatch.setitem(sys.modules,'reportlab',None);monkeypatch.setitem(sys.modules,'pptx',None)
    files,status=export_bundle(p,['pdf','pptx'],report={'summary_orientation':'metrics_as_rows'})
    assert not files and all(v['status']=='unavailable' for v in status['formats'].values())


def test_pdf_gate_connector_uses_available_glyphs():
    pytest.importorskip('reportlab')
    from fathom.exports import pdf_bytes
    document=copy.deepcopy(result().document)
    before=copy.deepcopy(document)
    pdf,_=pdf_bytes(document)
    # ReportLab uses an uncompressed text stream; the generated gate connector
    # must be words rather than a missing-font question mark.
    assert b'leads to' in pdf and document==before
