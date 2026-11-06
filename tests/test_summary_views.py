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
