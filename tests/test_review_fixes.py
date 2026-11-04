"""Regressions for all eight Copilot threads, HO-20261103-002."""
import copy
import io
import json

import pytest

from fathom.charts import svg_chart
from fathom.models import ProfilingResult
from fathom.target import relationship_chart
from fathom.target_marks import plot_marks


def box_chart(values,log=True):
    cols=[{'name':'g','effective_type':'categorical'},
          {'name':'amount','effective_type':'numeric','univariate':{'charts':[{'scale':'log10'}] if log else []}}]
    return relationship_chart([['A',str(v)] for v in values],cols,{'left':'g','right':'amount'})


def test_r4451047766_box_counts_and_small_caution():
    for values in ([0]*9+[50],[-1]*9+[50],[0]*10):
        chart=box_chart(values);row=chart['data'][0]
        assert row['n']==sum(v>0 for v in values)
        assert row['excluded_nonpositive']==sum(v<=0 for v in values)
        marks=plot_marks(chart)[2]
        assert any(mark[0]=='text' and 'small' in mark[3] for mark in marks)
    legacy=box_chart([0]*9+[50]);legacy['data'][0].pop('excluded_nonpositive')
    assert any(m[0]=='text' and 'n=? (legacy)' in m[3] for m in plot_marks(legacy)[2])
    for chart in (box_chart(range(1,11)),box_chart([0]*9+[50],log=False)):
        assert chart['data'][0]['n']==10 and chart['data'][0]['excluded_nonpositive']==0
        assert not any(m[0]=='text' and 'small' in m[3] for m in plot_marks(chart)[2])


def test_r4451047591_tiny_positive_geometry_preserves_statistics(make_profile):
    from fathom.univariate import percentile
    p=make_profile('g,amount\n'+'A,1e-12\n'*9+'B,1e-7\n',{'target':'amount','columns':{'g':{'type':'categorical'}}})
    chart=next(c for c in p.document['target_analysis']['charts'] if c['kind']=='group_box')
    assert chart['x_scale']=='log10' and chart['data'][0]['box']['median']==1e-12
    assert percentile([1e-12]*9,50)==1e-12  # Spec 008 (DEC-043): stored statistics keep 6 significant figures.
    ordinary=box_chart([1,2,3,4]);assert ordinary['data'][0]['box']['median']==2.5
    assert 'Chart values' in svg_chart(chart)


def rates_profile(make_profile):
    return make_profile('x,g,target\n1,A,no\n2,A,no\n3,B,yes\n4,B,yes\n',
                        {'target':'target','columns':{'g':{'type':'categorical'},'target':{'type':'categorical'}}})


def test_r4451047741_rate_axes_match_horizontal_shares(make_profile):
    p=rates_profile(make_profile)
    for chart in p.document['target_analysis']['charts']:
        assert chart['kind']=='rates'
        assert chart['x_label']=='Target category share among complete cases'
        assert chart['y_label'].startswith(('x','g'))
        html=svg_chart(chart);assert 'X: Target category share' in html and 'Y: Target category share' not in html
    from fathom.exports import export_bundle
    files,status=export_bundle(p,['pdf','pptx'])
    if status['formats']['pdf']['status']=='written':assert b'X: Target category share among complete cases' in files['report.pdf']
    if status['formats']['pptx']['status']=='written':
        import pptx
        deck=pptx.Presentation(io.BytesIO(files['report.pptx']))
        assert any('X: Target category share among complete cases; Y:' in sh.text for slide in deck.slides for sh in slide.shapes if sh.has_text_frame)
    scatter=make_profile('x,y\n1,2\n2,5\n3,7\n',{'target':'y'}).document['target_analysis']['charts'][0]
    assert scatter['x_label']=='x' and scatter['y_label']=='y'


@pytest.mark.parametrize('value',['DELETE',None,42,False,'x','unknown'])
def test_r4451047657_target_envelope_load_rejection(make_profile,tmp_path,value):
    p=make_profile('x,y\n1,2\n2,5\n3,7\n',{'target':'y'});d=copy.deepcopy(p.document)
    if value=='DELETE':d['target_analysis'].pop('target')
    else:d['target_analysis']['target']=value
    path=tmp_path/'bad.json';path.write_text(json.dumps(d))
    with pytest.raises(ValueError):ProfilingResult.load(path)
    assert ProfilingResult(p.document)
    assert ProfilingResult(make_profile('x\n1\n2\n').document).document['target_analysis']['target'] is None
    legacy=copy.deepcopy(p.document);legacy.pop('target_analysis');assert ProfilingResult(legacy)


@pytest.mark.parametrize('field',['statistics','contrasts','share_denominator','group_missing','value','value_type','missing_share','rates_missing_count','rates_bad_share','bad_statistic','bad_contrast','bad_denominator','bad_group_missing'])
def test_r4451047683_group_load_rejection(make_profile,tmp_path,field):
    p=rates_profile(make_profile);d=copy.deepcopy(p.document);summary=d['target_analysis']['groups'][0];group=summary['groups'][0]
    if field in ('share_denominator','group_missing','value_type'):summary.pop(field)
    elif field in ('statistics','contrasts','value','missing_share'):group.pop(field)
    elif field=='rates_missing_count':group['statistics']['rates'][0].pop('count')
    elif field=='rates_bad_share':group['statistics']['rates'][0]['share']='bad'
    elif field=='bad_statistic':group['statistics']={'mean':'bad'}
    elif field=='bad_contrast':group['contrasts']=[{'measure':'x','group':'bad','rest':None,'basis':42}]
    elif field=='bad_denominator':summary['share_denominator']=True
    else:summary['group_missing']=-1
    path=tmp_path/'bad.json';path.write_text(json.dumps(d))
    with pytest.raises(ValueError):ProfilingResult.load(path)
    assert ProfilingResult(p.document)
    assert ProfilingResult(make_profile('g,y\nA,1\nA,3\nB,8\n',{'target':'y'}).document)


@pytest.mark.parametrize('field,value',[('n',None),('total_rows',None),('n',1.5),('total_rows',True),('plotted','2'),('plotted',-1),('omitted_points',False),('omitted_nonpositive',.5)])
def test_r4451047707_chart_count_load_rejection(make_profile,tmp_path,field,value):
    p=make_profile('x,y\n1,2\n2,5\n3,7\n',{'target':'y'});d=copy.deepcopy(p.document);chart=d['target_analysis']['charts'][0]
    if value is None:chart.pop(field)
    else:chart[field]=value
    path=tmp_path/'bad.json';path.write_text(json.dumps(d))
    with pytest.raises(ValueError):ProfilingResult.load(path)
    assert ProfilingResult(p.document)
    for field in ('plotted','omitted_points','omitted_nonpositive'):p.document['target_analysis']['charts'][0].pop(field,None)
    assert ProfilingResult(p.document) # Historically optional fields remain optional.


def test_r4451047624_accessible_exact_chart_values(make_profile):
    scatter=make_profile('x,y\n1,2\n2,5\n3,7\n',{'target':'y'}).document['target_analysis']['charts'][0]
    box=box_chart([0,1e-12,2e-12]);box['data'][0]['label']='Long <group> label & exact spelling'
    rates=rates_profile(make_profile).document['target_analysis']['charts']
    for ch in [scatter,box,*rates]:
        html=svg_chart(ch)
        assert '<details><summary>Chart values</summary>' in html
        assert '<table' in html and '<th' in html
    html=svg_chart(box);assert 'Long &lt;group&gt; label &amp; exact spelling' in html
    assert '1e-12' in html and '2e-12' in html and 'Excluded nonpositive' in html
    assert 'Target category' in svg_chart(rates[0]) and 'Rate' in svg_chart(rates[0])


def test_r4451047641_powerpoint_minimum_font_layout(make_profile):
    pptx=pytest.importorskip('pptx');from fathom.exports import export_bundle
    # Every group/target level is genuinely present; neither column is identifier-like.
    csv='g,target\n'+''.join(f'group-{g:02},level-{v:02}\n' for g in range(20) for v in range(20))
    p=make_profile(csv,{'target':'target','columns':{'g':{'type':'categorical'},'target':{'type':'categorical'}}})
    files,status=export_bundle(p,['pptx']);deck=pptx.Presentation(io.BytesIO(files['report.pptx']))
    slides=[s for s in deck.slides if s.shapes.title.text.startswith('Target:')]
    assert len(slides)>1
    for slide in slides:
        labels=[sh for sh in slide.shapes if sh.has_text_frame and sh!=slide.shapes.title and sh.top>914400*1.4 and sh.top<914400*6.15 and sh.text.strip()]
        boxes=sorted((sh.left,sh.top,sh.width,sh.height) for sh in labels)
        for i,(x,y,w,h) in enumerate(boxes):
            for xx,yy,ww,hh in boxes[i+1:]:
                if x<xx+ww and xx<x+w:assert y+h<=yy or yy+hh<=y
        assert all(run.font.size is None or run.font.size.pt>=8 for sh in labels for para in sh.text_frame.paragraphs for run in para.runs)
    texts='\n'.join(sh.text for s in slides for sh in s.shapes if sh.has_text_frame)
    assert all(f'group-{g:02}' in texts for g in range(20)) and all(f'level-{v:02}' in texts for v in range(20))
    ordinary=make_profile('x,y\n1,2\n2,5\n3,7\n',{'target':'y'})
    data,_=export_bundle(ordinary,['pptx']);assert len(pptx.Presentation(io.BytesIO(data['report.pptx'])).slides)<=12
