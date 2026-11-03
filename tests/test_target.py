import copy
import io
import json

import pytest

from fathom.config import validate_config
from fathom.models import ProfilingResult
from fathom.renderers import render_html, render_markdown


def test_hand_computed_measures_and_clean_decoys():
    from fathom.target import association
    assert association('numeric','numeric',[(1,2),(2,4),(3,6)])['value']==1
    assert association('numeric','numeric',[(1,-2),(2,-4),(3,-6)])['value']==-1
    assert association('categorical','numeric',[('A',0),('A',0),('B',10),('B',10)])['value']==1
    assert association('categorical','numeric',[('A',0),('A',10),('B',0),('B',10)])['value']==0
    assert association('categorical','categorical',[('A','x')]*4+[('B','y')]*4)['value']==1
    assert association('categorical','categorical',[(a,b) for a in 'AB' for b in 'xy']*2)['value']==0
    assert association('numeric','numeric',[(1,2),(1,4)]) is None


def test_rank_exclusions_and_no_numeric_uniqueness_block(make_profile):
    rows=['signal,target,leak,copy,record_id,flat,group']
    rows += [f'{i*2+i%2},{i},{20-i},{i},id{i},1,{"A" if i<10 else "B"}' for i in range(20)]
    d=make_profile('\n'.join(rows)+'\n',{'target':'target','pair_budget':2,'columns':{'leak':{'exclude_from_target':True}}}).document
    t=d['target_analysis'];reasons={e['column']:e['reason'] for e in t['excluded']}
    assert 'config' in reasons['leak'] and 'near-duplicate' in reasons['copy']
    assert 'identifier' in reasons['record_id'] and 'constant' in reasons['flat']
    assert t['ranked'][0]['column']=='signal' and len(d['bivariate'])==2
    assert any(p['left']=='group' for p in d['bivariate'])
    assert t['ranked'][0]['measure']=='Pearson r'


def test_small_group_counts_missing_and_contrasts(make_profile):
    csv='g,target\n'+'A,10\n'*10+'B,100\n'*2+'B,\n'
    p=make_profile(csv,{'target':'target','columns':{'g':{'type':'categorical'}}})
    summary=p.document['target_analysis']['groups'][0]
    b=next(g for g in summary['groups'] if g['value']=='B')
    assert b['n']==3 and b['valid']==2 and b['missing']==1
    assert b['share']==pytest.approx(3/13) and b['small']
    assert b['statistics']['mean']==100 and b['statistics']['median']==100
    assert b['contrasts'] and any(f.get('rule')=='target_group_contrast' for f in p.document['findings'])
    text=render_html(p)+render_markdown(p)
    assert 'too small' in text and 'descriptive' in text.lower()


def test_categorical_target_rates_numeric_bins_and_group_sizes(make_profile):
    p=make_profile('x,target,group\n1,no,A\n2,no,A\n3,no,B\n4,yes,A\n5,yes,B\n6,yes,B\n',{'target':'target','columns':{'target':{'type':'categorical'},'group':{'type':'categorical'}}})
    t=p.document['target_analysis']
    assert {r['measure'] for r in t['ranked']}=={'Correlation ratio eta',"Cramer's V"}
    assert any(c['kind']=='rates' for c in t['charts'])
    rates=next(c for c in t['charts'] if c['kind']=='rates')
    assert all(sum(r['rates'].values())==pytest.approx(1) for r in rates['data'] if r['n'])
    assert any(s['group_column']=='target' for s in t['groups'])


def test_skip_budget_and_legacy_config_errors(make_profile):
    assert make_profile('x,y\n1,2\n2,4\n').document['target_analysis']['status']=='skipped'
    d=make_profile('x,y\n1,2\n2,4\n',{'target':'y','pair_budget':0}).document
    assert d['target_analysis']['ranked'] and not d['target_analysis']['charts'] and not d['bivariate']
    for cfg in ({'group_by':'unknown'},{'columns':{'x':{'exclude_from_target':'yes'}}}):
        with pytest.raises(ValueError):validate_config(cfg,['x','y'])
    legacy=copy.deepcopy(d);legacy.pop('target_analysis')
    assert 'legacy' in render_html(ProfilingResult(legacy)).lower()


def test_new_target_artifact_validation(make_profile):
    p=make_profile('x,y\n1,2\n2,5\n3,7\n',{'target':'y'})
    d=copy.deepcopy(p.document);d['target_analysis']['ranked'][0]['n']=-1
    with pytest.raises(ValueError):ProfilingResult(d)


def test_log_ecdf_original_ticks_slim_box_and_sticky_statistics(make_profile):
    from fathom.charts import svg_chart
    d=make_profile('gross\n0\n1\n2\n3\n4\n5\n6\n7\n1000000\n')
    charts=d.document['columns'][0]['univariate']['charts']
    ecdf=next(c for c in charts if c['kind']=='ecdf' and c.get('scale')=='log10')
    assert ecdf['coverage_counts']=={'positive':8,'zeros':1,'negatives':0,'invalid':0}
    assert ecdf['points'][-1]['cumulative']==1
    html=svg_chart(ecdf)
    assert '1M' in html and 'positive' in html.lower()
    box=svg_chart(next(c for c in charts if c['kind']=='box'))
    assert 'Y:' not in box and 'viewBox="0 0 560 110"' in box
    assert 'position:sticky' in render_html(d)


def test_budgeted_plots_all_types_and_exports(make_profile):
    p=make_profile('x,g,target\n1,A,10\n2,A,14\n3,A,15\n4,B,24\n5,B,25\n6,B,30\n',{'target':'target'})
    charts=p.document['target_analysis']['charts']
    assert {c['kind'] for c in charts}=={'scatter','group_box'}
    assert all(c['title'] in render_html(p) for c in charts)
    from fathom.exports import export_bundle
    files,status=export_bundle(p,['pdf','pptx'])
    again,_=export_bundle(p,['pdf','pptx']);assert files==again
    if status['formats']['pptx']['status']=='written':
        import pptx
        deck=pptx.Presentation(io.BytesIO(files['report.pptx']))
        assert len(deck.slides)<=12
        assert any('Target' in s.shapes.title.text for s in deck.slides)


def test_declared_group_budget_order_and_clean_contrasts(make_profile):
    text='x,g,target\n'+'\n'.join(f'{i*2+i%2},{i%2},{i}' for i in range(12))+'\n'
    cfg={'target':'target','pair_budget':1,'group_by':'g','columns':{'g':{'type':'categorical'}}}
    d=make_profile(text,cfg).document
    assert d['selection']['selected']==[['g','target']]
    assert d['target_analysis']['ranked'][0]['column']=='x'
    assert 'reserved' in d['target_analysis']['grouping_policy']
    clean=make_profile('g,target\nA,0\nA,10\nB,0\nB,10\n',{'target':'target'}).document
    assert not [f for f in clean['findings'] if f.get('rule')=='target_group_contrast']
    with pytest.raises(ValueError):make_profile(text,{'target':'target','group_by':'x'})


def test_scatter_sampling_log_coverage_and_native_log_ecdf(make_profile):
    from fathom.exports import export_bundle
    from pathlib import Path
    p=make_profile('x,gross\n'+'\n'.join(f'{i},{0 if i==0 else 10**(i/20)}' for i in range(250))+'\n',{'target':'gross'})
    ch=p.document['target_analysis']['charts'][0]
    assert ch['kind']=='scatter' and ch['y_scale']=='log10'
    assert ch['omitted_nonpositive']==1 and ch['plotted']==200 and ch['omitted_points']==49
    files,status=export_bundle(p,['pptx'],deck='full')
    if status['formats']['pptx']['status']=='written':
        import zipfile
        with zipfile.ZipFile(io.BytesIO(files['report.pptx'])) as z:
            xml=b''.join(z.read(n) for n in z.namelist() if n.startswith('ppt/charts/') and n.endswith('.xml'))
            assert b'logBase' in xml
    corrupted=copy.deepcopy(p.document);corrupted['target_analysis']['charts'][0]['points'][0]['y']=0
    with pytest.raises(ValueError):ProfilingResult(corrupted)
