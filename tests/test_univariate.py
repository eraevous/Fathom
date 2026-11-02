import csv
import io
from pathlib import Path
import random
import re

import pytest

from fathom.profiler import profile
from fathom.connectors import CSVConnector
from fathom.models import ProfilingResult
from fathom.renderers import render_html, render_markdown


def csv_text(names,rows):
    f=io.StringIO();w=csv.writer(f);w.writerow(names);w.writerows(rows);return f.getvalue()


def test_samples_seed_truncation_and_human_identity(make_profile):
    rows=[[str(i),'x'*150] for i in range(50)]
    d=make_profile(csv_text(['id','note'],rows),{'title':'Synthetic readings','description':'Authored example','sample_seed':42}).document
    s=d['samples'];assert s['seed']==42 and s['size']==20
    assert [r['position'] for r in s['first']]==list(range(1,21))
    assert [r['position'] for r in s['last']]==list(range(31,51))
    assert [r['position'] for r in s['random']]==sorted(i+1 for i in random.Random(42).sample(range(50),20))
    assert s['first'][0]['values'][1].endswith('… [truncated]')
    assert d['dataset']['title']['status']=='human'
    assert 'raw input values' in render_html(ProfilingResult(d))


def test_numeric_profile_exact_currency_and_charts(make_profile):
    d=make_profile(csv_text(['gross'],[['$0'],['$100'],['$200'],['$300'],['$400'],['$500']])).document
    c=d['columns'][0];u=c['univariate'];s=u['statistics']
    assert c['effective_type']=='numeric'
    assert s['zeros']=={'count':1,'share':pytest.approx(1/6)}
    assert s['integers']==6 and s['non_integers']==0
    assert s['percentiles']['25']==125 and s['percentiles']['50']==250
    assert {x['kind'] for x in u['charts']}=={'histogram','box','ecdf'}
    assert any(f.get('rule')=='implausible_zero' and f['kind']=='observation' for f in d['findings'])
    clean=make_profile(csv_text(['gross'],[[i] for i in range(100,700,100)])).document
    assert not any(f.get('rule')=='implausible_zero' for f in clean['findings'])


def test_text_profile_raw_blanks_casing_entropy(make_profile):
    d=make_profile(csv_text(['notes'],[[''],['  '],['NA'],['none'],['blank'],['HELLO!'],['Hello!'],['hello!']])).document
    s=d['columns'][0]['univariate']['statistics']
    assert s['candidate_blanks']['empty']==1 and s['candidate_blanks']['whitespace']==1
    assert s['candidate_blanks']['tokens']==3
    assert s['casing']=={'upper':2,'lower':3,'mixed':1,'uncased':2}
    assert s['special_characters'][0]=={'value':'!','count':3}
    assert any(x['value']=='hello' and x['count']==3 for x in s['common_substrings'])
    assert s['entropy_bits']>0 and s['length']['min']==0


def test_noniso_dates_two_digit_future_and_placeholder(make_profile):
    rows=[['Jun 12 1998'],['Jul 15 1999'],['08/01/44'],['1900-01-01'],['Feb 30 2001']]
    d=make_profile(csv_text(['release_date'],rows),{'context':{'snapshot_date':'2026-11-01'}}).document
    c=d['columns'][0];s=c['univariate']['statistics']
    assert c['effective_type']=='temporal'
    assert s['valid']==4 and s['invalid']==1 and s['two_digit_years']==1
    assert s['after_reference']==1 and s['placeholder_dates']==1
    assert s['latest']=='2044-08-01'
    for rule in ('two_digit_year','future_date','placeholder_date'):
        assert any(f.get('rule')==rule for f in d['findings'])
    assert s['parse_formats']['MON_D_Y']==2
    clean=make_profile('release_date\nJun 12 1998\nJul 15 1999\n',{'context':{'snapshot_date':'2026-11-01'}}).document
    assert not any(f.get('rule') in {'two_digit_year','future_date','placeholder_date'} for f in clean['findings'])


def test_identifier_repetition_and_override(make_profile):
    d=make_profile('title\nAlpha\nBeta\nAlpha\n').document
    assert any(f.get('rule')=='repeated_identifier' and f['kind']=='observation' for f in d['findings'])
    clean=make_profile('title\nAlpha\nBeta\nGamma\n').document
    assert not any(f.get('rule')=='repeated_identifier' for f in clean['findings'])


def test_layout_labels_hidden_technical_and_roundtrip(make_profile,tmp_path):
    p=make_profile(csv_text(['gross','release_date'],[[i,'Jun 12 1998'] for i in range(5)]))
    for view in (render_html(p),render_markdown(p)):
        titles=['Dictionary','Provenance','Dataset summary','Findings','Relations']
        offsets=[view.index(('<h2>'+t+'</h2>') if view.startswith('<!doctype') else '## '+t) for t in titles]
        assert offsets==sorted(offsets)
    html=render_html(p)
    assert 'Provenance internals' in html and '<details' in html
    assert 'Rows (count)' in html and 'Value' in html
    assert 'First rows' in html and 'Last rows' in html and 'Random rows' in html
    saved=tmp_path/'p.json';saved.write_text(p.to_json());r=ProfilingResult.load(saved)
    assert render_html(r)==html and render_markdown(r)==render_markdown(p)


@pytest.mark.parametrize('cfg',[{'sample_rows':True},{'sample_rows':101},{'sample_seed':-1},{'sample_text_limit':1},{'columns':{'x':{'date_format':'guess'}}}])
def test_invalid_new_configuration(make_profile,cfg):
    with pytest.raises(ValueError):make_profile('x\n1\n',cfg)


def test_small_empty_sample_windows_and_inference(make_profile):
    d=make_profile('x\n1\n2\n').document
    assert len(d['samples']['random'])==2 and d['dataset']['description']['status']=='inferred'
    e=make_profile('x\n').document
    assert e['samples']['first']==[]


def test_numeric_moments_counts_and_blank_decoy(make_profile):
    c=make_profile('amount\n-2\n0\n1.5\n4\n5\nNA\n').document['columns'][0]
    assert c['effective_type']=='numeric' and c['statistics']['invalid']==1
    s=c['univariate']['statistics']
    assert s['negatives']=={'count':1,'share':.2}
    assert s['integers']==4 and s['non_integers']==1
    assert s['percentiles']['1']==pytest.approx(-1.92)
    assert s['skewness'] is not None and s['excess_kurtosis'] is not None


def test_temporal_breakdowns_and_explicit_dmy(make_profile):
    d=make_profile('date\n01/02/2001\n02/02/2001\n03/03/2001\n',{'columns':{'date':{'date_format':'DMY'}}}).document
    s=d['columns'][0]['univariate']['statistics']
    assert s['earliest']=='2001-02-01' and s['span_days']==30
    assert sum(s['weekday_counts'].values())==3 and s['month_counts']['february']==2
    assert s['quarter_counts']['Q1']==3 and s['year_counts']=={'2001':3}
    assert s['ambiguous_dates']==0 and s['after_reference'] is None


def test_entropy_coverage_and_common_values(make_profile):
    s=make_profile('category\nA\nB\nA\nB\n').document['columns'][0]['univariate']['statistics']
    assert s['entropy_bits']==1 and s['top_n_coverage']['share']==1
    assert s['length']=={'min':1,'max':1,'mean':1,'median':1}


def test_invalid_chart_artifact_is_rejected(make_profile):
    import copy
    d=copy.deepcopy(make_profile('x\n1\n2\n').document)
    d['columns'][0]['univariate']['charts'][1].pop('box')
    with pytest.raises(ValueError):ProfilingResult(d)


def test_builder_film_clean_and_late_tables():
    from fathom.config import load_config
    root=Path(__file__).parent/'fixtures'/'univariate'
    cfg=load_config(root/'film.yaml')
    d=profile(CSVConnector(root/'film.csv').load(),cfg).document
    rules={f.get('rule') for f in d['findings']}
    assert {'repeated_identifier','two_digit_year','future_date','placeholder_date','implausible_zero'}<=rules
    assert d['columns'][2]['univariate']['statistics']['invalid']==1
    clean=profile(CSVConnector(root/'clean.csv').load(),cfg).document
    assert not [f for f in clean['findings'] if f['kind']=='action']
    late=profile(CSVConnector(root/'late.csv').load(),cfg).document
    assert late['columns'][1]['univariate']['statistics']['ambiguous_dates']==1
    assert late['columns'][1]['univariate']['statistics']['invalid_examples']==['Dec 1999']
