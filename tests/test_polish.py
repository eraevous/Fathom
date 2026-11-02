import io
import re

import pytest

from fathom.renderers import render_html
from fathom.presentation import column_tables


def test_compact_closed_headers_and_scaled_grid(make_profile):
    html=render_html(make_profile('amount\n1\n2\n3\n'))
    assert '<details class="column-entry">' in html
    assert '<details class="column-entry" open' not in html
    assert 'column-grid' in html and 'grid-template-columns' in html
    assert '.chart svg{width:100%' in html


def test_log_positive_subset_and_zero_negative_counts(make_profile):
    d=make_profile('gross\n-1\n0\n0\n1\n2\n3\n4\n5\n6\n1000000\n').document
    ch=next(x for x in d['columns'][0]['univariate']['charts'] if x.get('scale')=='log10')
    assert ch['coverage_counts']=={'positive':7,'zeros':2,'negatives':1,'invalid':0}
    assert sum(x['count'] for x in ch['data'])==7
    html=render_html(__import__('fathom.models',fromlist=['ProfilingResult']).ProfilingResult(d))
    assert 'Zeros excluded: 2' in html and 'Negatives excluded: 1' in html
    for values in ('0\n0\n0','-1\n-2\n0','0\n1\n2\n3'):
        d=make_profile('gross\n'+values+'\n').document
        assert not any(x.get('scale')=='log10' for x in d['columns'][0]['univariate']['charts'])


def test_order_rounding_and_examples(make_profile):
    p=make_profile('gross\n146083.0\n85343400.142\n100\n')
    t=column_tables(p.document['columns'][0])[0];labels=[r[0] for r in t['rows']]
    assert labels[:3]==['Rows','Valid','Missing']
    assert [x for x in labels if x in ('Min','Q1','Median','Q3','Mean','Max')]==['Min','Q1','Median','Q3','Mean','Max']
    html=render_html(p)
    assert '85,343,400' in html and '146,083' in html
    assert 'Examples: 146,083' in html
    assert 'column-statistics' in html


def test_identifier_near_unique_suppression_and_category_decoy(make_profile):
    for name,values in [('Title',['a','b','c','d','e']),('label',[str(i) for i in range(20)])]:
        cfg={'columns':{name:{'type':'string'}}}
        c=make_profile(name+'\n'+'\n'.join(values)+'\n',cfg).document['columns'][0]
        assert c['univariate']['top_n_suppression']
        assert not any(ch['kind']=='bar' and 'coverage' in ch for ch in c['univariate']['charts'])
    c=make_profile('group\na\na\na\nb\nb\nc\n').document['columns'][0]
    assert any(ch['kind']=='bar' for ch in c['univariate']['charts'])
    c=make_profile('gross\n1\n2\n3\n4\n5\n').document['columns'][0]
    assert 'top_n_suppression' not in c['univariate']


def test_months_ticks_box_and_axis_captions(make_profile):
    from fathom.charts import svg_chart, count_ticks
    assert count_ticks(3)==[0,1,2,3]
    assert count_ticks(1082)==[0,270,541,812,1082]
    p=make_profile('date\n2020-01-01\n2020-02-01\n2020-02-02\n')
    charts=p.document['columns'][0]['univariate']['charts']
    month=next(x for x in charts if x.get('calendar')=='month')
    assert month['data'][0]['label']=='January'
    ch={'kind':'box','title':'Close quartiles','x_label':'Long horizontal title '*8,'y_label':'Rows (count)',
        'box':{'min':0,'q1':85343400.1,'median':85343400.14,'q3':85343400.15,'max':85343401}}
    html=svg_chart(ch)
    assert 'rotate(' not in html and 'box-summary' in html and 'axis-captions' in html
    assert html.count('class="tick-label"')>=3


def test_summary_full_deck_budget_scope_and_bytes(make_profile):
    pptx=pytest.importorskip('pptx');from fathom.exports import export_bundle
    data='a,b,c,d,e\n'+'\n'.join(','.join(str(i+j) for j in range(5)) for i in range(30))+'\n'
    p=make_profile(data)
    one,s=export_bundle(p,['pptx']);two,_=export_bundle(p,['pptx'])
    assert one==two
    summary=pptx.Presentation(io.BytesIO(one['report.pptx']))
    full,status=export_bundle(p,['pptx'],deck='full')
    deck=pptx.Presentation(io.BytesIO(full['report.pptx']))
    assert 5<=len(summary.slides)<=12 and len(deck.slides)>len(summary.slides)
    assert any('7.25' in shape.text for slide in deck.slides for shape in slide.shapes if shape.has_text_frame)
    assert s['formats']['pptx']['mode']=='summary' and status['formats']['pptx']['mode']=='full'
    assert any('Summary deck' in shape.text for slide in summary.slides for shape in slide.shapes if shape.has_text_frame)


def test_cli_full_deck_flag(make_profile,tmp_path):
    from fathom.cli import main
    path=tmp_path/'profile.json';path.write_text(make_profile('x\n1\n2\n3\n').to_json())
    assert main(['export',str(path),'--out',str(tmp_path/'out'),'--formats','pptx','--deck','full'])==0
