from html_helpers import visible_text, assert_navigation_only_script
from copy import deepcopy
import csv
import io
from pathlib import Path

import pytest

from fathom.models import ProfilingResult
from fathom.renderers import render_html, render_markdown


def csv_text(header, rows):
    s=io.StringIO();w=csv.writer(s);w.writerow(header);w.writerows(rows);return s.getvalue()


def test_numeric_ecdf_log_and_clean_decoys(make_profile):
    p=make_profile('amount\n1\n1\n2\n3\n4\n5\n6\n10000\n')
    charts=p.document['columns'][0]['univariate']['charts']
    ecdf=next(c for c in charts if c['kind']=='ecdf')
    assert ecdf['points']==[{'x':x,'cumulative':count/8,'count':count} for x,count in [(1.,2),(2.,3),(3.,4),(4.,5),(5.,6),(6.,7),(10000.,8)]]
    assert any(c.get('scale')=='log10' for c in charts)
    # FT-R18 now permits zero/negative exclusions with explicit coverage.
    for values in ('0\n0\n0','-1\n-2\n0','3\n3\n3','1\n2\n3\n4'):
        charts=make_profile('x\n'+values+'\n').document['columns'][0]['univariate']['charts']
        assert not any(c.get('scale')=='log10' for c in charts)
    assert sum(c['count'] for c in charts[0]['data'])==4


def test_ecdf_display_bound(make_profile):
    d=make_profile('x\n'+'\n'.join(str(i) for i in range(1000))+'\n').document
    ch=next(c for c in d['columns'][0]['univariate']['charts'] if c['kind']=='ecdf')
    assert len(ch['points'])<=200 and ch['omitted_points']>0
    assert ch['points'][0]['x']==0 and ch['points'][-1]['cumulative']==1


def test_category_remainder_and_text_length(make_profile):
    vals=['Other','[Other values — remainder]']+[f'category{i}' for i in range(13)]
    p=make_profile(csv_text(['group'],[[v] for v in vals for _ in range(2)]),{'columns':{'group':{'type':'categorical'}}})
    ch=next(c for c in p.document['columns'][0]['univariate']['charts'] if c.get('coverage'))
    assert len(ch['data'])==11 and ch['data'][-1]['is_other']
    assert len({x['label'] for x in ch['data']})==11
    assert sum(x['count'] for x in ch['data'])==30 and ch['coverage']==10/15
    assert sum(x['share'] for x in ch['data'])==pytest.approx(1)
    p=make_profile(csv_text(['note'],[[''],[' '],['ab'],['abcd']]))
    ch=next(c for c in p.document['columns'][0]['univariate']['charts'] if c.get('measure')=='string_length')
    assert sum(x['count'] for x in ch['data'])==4


@pytest.mark.parametrize('dates,period',[
    (['2020-01-01','2020-01-03'],'day'),
    (['2020-01-01','2021-01-01'],'month'),
    (['1900-01-01','2026-01-01'],'year'),
])
def test_date_chart_period_and_calendar_bars(make_profile,dates,period):
    c=make_profile(csv_text(['date'],[[v] for v in dates])).document['columns'][0]
    ch=next(x for x in c['univariate']['charts'] if x['kind']=='time')
    assert ch['period']==period and len(ch['data'])<=60
    if period=='day':assert [v['count'] for v in ch['data']]==[1,0,1]
    for basis in ('weekday','month'):
        bar=next(x for x in c['univariate']['charts'] if x.get('calendar')==basis)
        assert sum(v['count'] for v in bar['data'])==2


def test_missingness_patterns_and_complete_decoy(make_profile):
    p=make_profile('a,b,c\n, ,1\n,,2\n1,2,3\n')
    masks=p.document['missingness_patterns']
    assert masks['patterns'][0]=={'missing':['a','b'],'count':2,'share':2/3}
    assert sum(x['count'] for x in masks['patterns'])==3
    clean=make_profile('a,b\n1,2\n3,4\n').document['missingness_patterns']
    assert clean['patterns']==[{'missing':[],'count':2,'share':1.0}]
    assert len(p.document['bivariate'])<=p.document['selection']['budget']


def test_time_name_does_not_imply_dates(make_profile):
    p=make_profile('Running Time min,Full_time,Part_time\n90,100,50\n120,200,60\n')
    assert 'dates (' not in p.document['dataset']['description']['text']
    assert all(c['effective_type']=='numeric' for c in p.document['columns'])


def test_column_inline_tables_formatting_and_raw_disclosure(make_profile):
    p=make_profile('amount,category\n10014234,A\n47.23671133,B\n47.23671133,A\n',{'columns':{'amount':{'units':'USD'}}})
    html=render_html(p);md=render_markdown(p)
    assert 'class="column-entry"' in html and 'Raw evidence' in html
    assert '10,014,234' in html and '47.24' in html and 'USD' in html
    assert 'Value</th>' in html and 'Share</th>' in html and 'class="num"' in html
    assert '10,014,234' in md
    assert_navigation_only_script(html)
    hostile=make_profile('label\n"![x](https://example.org/x)"\n')
    assert '| ![x](' not in render_markdown(hostile)


def test_new_artifact_validation(make_profile):
    d=deepcopy(make_profile('x\n1\n2\n3\n').document)
    ecdf=next(c for c in d['columns'][0]['univariate']['charts'] if c['kind']=='ecdf')
    ecdf['points'][0]['cumulative']=2
    with pytest.raises(ValueError):ProfilingResult(d)


def test_saved_artifact_chart_views_and_legacy(make_profile,tmp_path):
    p=make_profile('x\n1\n2\n3\n');path=tmp_path/'saved.json';path.write_text(p.to_json())
    assert render_html(p)==render_html(ProfilingResult.load(path))
    old=ProfilingResult.load(Path(__file__).parent/'fixtures/quality/legacy-profile.json')
    assert 'Dictionary' in render_html(old)


def test_pattern_display_bounds_and_no_data_change(make_profile):
    rows=[[None if i&(1<<k) else '1' for k in range(6)] for i in range(32)]
    p=make_profile(csv_text([f'c{k}' for k in range(6)],rows))
    masks=p.document['missingness_patterns']
    assert len(masks['patterns'])==20 and masks['omitted_patterns']==12
    assert masks['omitted_rows']==12 and p.document['overview']['missing_cells']==80


def test_export_new_chart_kinds_use_numeric_xy_and_pdf(make_profile):
    pptx=pytest.importorskip('pptx');pytest.importorskip('reportlab')
    from fathom.exports import export_bundle
    from pptx.enum.chart import XL_CHART_TYPE
    p=make_profile('x\n1\n2\n1000\n')
    files,_=export_bundle(p,['pdf','pptx'],deck='full')
    deck=pptx.Presentation(io.BytesIO(files['report.pptx']))
    xy=[sh.chart for slide in deck.slides for sh in slide.shapes if sh.has_chart and sh.chart.chart_type==XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS]
    assert len(xy)==1
    assert xy[0].series[0].values[-1]==100
    assert b'Empirical cumulative distribution' in files['report.pdf']
