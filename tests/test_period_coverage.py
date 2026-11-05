"""Timestamp-span disclosures retain the old period totals and signals."""
import calendar
from fathom.renderers import render_html,render_markdown,DATETIME_NOTE
from fathom.configure import build_schema
from fathom.connectors import CSVConnector
import pytest


def series(d):return d['time_series']['series'][0]['groups'][0]
def declare(grain):return {'time_series':[{'time':'when','value':'value','granularities':[grain]}]}


def test_month_stub_is_flagged_and_amplitude_is_labelled(make_profile):
    p=make_profile('when,value\n2023-01-31 23:30,1\n2023-02-01 00:00,10\n2023-02-15 12:00,20\n2023-02-28 23:59,30\n',declare('month'))
    g=series(p.document)['granularities'][0];edges=g['edge_coverage']
    assert len(edges)==2 and edges[0]['partial'] and edges[0]['covered_seconds']==1800
    assert edges[0]['period_seconds']==31*86400 and not edges[1]['partial']
    assert g['amplitude']['nonzero']['median']==30.5 and g['series'][0]['value']==1
    assert g['series'][0]['partial_edge'] and not g['series'][1]['partial_edge']
    for text in [render_html(p),render_markdown(p)]:
        assert 'partial edge' in text and 'timestamp-span' in text and 'includes 1 partial' in text


@pytest.mark.parametrize('year,days',[(2023,28),(2024,29)])
def test_complete_date_only_month_is_a_clean_decoy(make_profile,year,days):
    p=make_profile(f'when,value\n{year}-02-01,1\n{year}-02-{days},2\n',declare('month'))
    g=series(p.document)['granularities'][0];assert len(g['edge_coverage'])==1
    e=g['edge_coverage'][0];assert e['position']=='both' and not e['partial']
    assert e['covered_seconds']==e['period_seconds']==days*86400
    assert g['amplitude']['nonzero']['median']==3 and not g['series'][0]['partial_edge']


def test_single_hour_has_one_both_edge_and_lexical_end_resolution(make_profile):
    p=make_profile('when,value\n2024-01-01 03:15,2\n2024-01-01 03:45,4\n',declare('hour'))
    e=series(p.document)['granularities'][0]['edge_coverage'];assert len(e)==1
    assert e[0]['position']=='both' and e[0]['covered_seconds']==31*60 and e[0]['partial']


def test_hourly_scope_does_not_claim_time_of_day_excluded(make_profile):
    data='when,value\n2024-01-01 00:00,1\n2024-01-02 00:30,2\n'
    p=make_profile(data,declare('hour'))
    for text in [render_html(p),render_markdown(p)]:
        assert DATETIME_NOTE not in text and 'hourly series retains time of day' in text
    for text in [render_html(make_profile(data)),render_markdown(make_profile(data))]:assert DATETIME_NOTE in text


def test_high_cardinality_string_hint_is_optional_and_retains_caps(make_profile,tmp_path):
    data='label\n'+'\n'.join('label-'+str(i) for i in range(21) for _ in range(2))+'\n'
    p=make_profile(data);c=p.document['columns'][0];assert c['effective_type']=='string'
    for text in [render_html(p),render_markdown(p)]:assert 'type: categorical' in text and '20' in text
    path=tmp_path/'hint.csv';path.write_text(data);frame=CSVConnector(path).load().frame
    schema=build_schema(p.document,frame,None);assert any('type: categorical' in f for f in schema['columns'][0]['facts'])
    clean=make_profile('label\nA\nB\nA\nB\n')
    assert 'type: categorical' not in render_html(clean) and clean.document['columns'][0]['effective_type']=='categorical'


def test_legacy_boundary_coverage_is_not_assumed_complete(make_profile):
    p=make_profile('when,value\n2024-01-01,0\n2024-01-02,2\n',declare('day'))
    for g in series(p.document)['granularities']:g.pop('edge_coverage',None)
    assert 'boundary coverage not recorded' in render_html(p)
