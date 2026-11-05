"""Presentation controls: verdict algorithms remain independently tested."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
from fathom.connectors import CSVConnector
from fathom.profiler import profile
from fathom.renderers import render_html, render_markdown
from fathom.liftoff import build_liftoff, render_liftoff


def test_headline_cap_order_and_clean_decoy():
    from fathom.verdicts import key_findings
    d={'findings':[{'id':f'f{i}','kind':'observation','message':str(i),'rule':'dummy'} for i in range(8)],'selection':{}}
    assert len(key_findings(d))==5
    assert key_findings({'findings':[],'selection':{}})==[]
    assert key_findings(d)==key_findings(deepcopy(d))


def test_group_rows_explain_failed_and_passed_gates():
    from fathom.target import summarize_groups,target_tables
    cs=[{'name':'g','effective_type':'categorical'},{'name':'y','effective_type':'numeric'}]
    s=summarize_groups([['A','0']]*10+[['B','1']]*10+[['C','10']]*10,cs,0,1)
    tables=target_tables({'target_analysis':{'target':'y','ranked':[],'excluded':[],'groups':[s]}})
    rows=tables[-1]['rows'];assert all('gap' in r[-1] and 'SD' in r[-1] for r in rows)
    assert any('→ marked' in r[-1] for r in rows)
    # A near-overall group is a clean non-contrast decoy.
    s=summarize_groups([['A','0'],['A','10'],['B','0'],['B','10']],cs,0,1)
    assert not any(g['contrasts'] for g in s['groups'])
    assert all('→ not marked' in r[-1] for r in target_tables({'target_analysis':{'target':'y','ranked':[],'excluded':[],'groups':[s]}})[-1]['rows'])


def test_skew_conjunction_is_visible_even_when_it_fails(tmp_path):
    path=tmp_path/'values.csv';path.write_text('x\n'+'\n'.join(map(str,list(range(100))+[1000]))+'\n')
    d=profile(CSVConnector(path).load()).document
    gate=d['quality']['skew_gates']['x'];assert gate['moment_passed'] and not gate['displacement_passed']
    text=render_html(type('R',(),{'document':d})())
    assert 'not strongly skewed' in text and '½' in text and 'IQR' in text
    assert not any(f.get('rule')=='skew' for f in d['findings'])


def test_headline_precedes_dictionary_and_preserves_saved_result():
    from fathom.models import ProfilingResult
    p=profile(CSVConnector(Path('tests/fixtures/liftoff/planted.csv')).load())
    html=render_html(p);assert html.index('Key findings')<html.index('<h2>Dictionary')
    assert render_markdown(p).index('Key findings')<render_markdown(p).index('## Dictionary')
    assert html==render_html(ProfilingResult(json.loads(p.to_json())))


def test_brief_headline_conditional_status_and_zero_pattern():
    from fathom.verdicts import key_findings
    p=build_liftoff(CSVConnector(Path('tests/fixtures/liftoff/periodic.csv')).load())
    items=key_findings(p.document);assert len(items)<=5
    assert any('If you declare' in i['message'] and '24 hour cycle' in i['message'] for i in items)
    assert render_liftoff(p).index('Key findings')<render_liftoff(p).index('What the table looks like')
    p=build_liftoff(CSVConnector(Path('tests/fixtures/liftoff/planted.csv')).load())
    assert any('is 0 in' in i['message'] for i in key_findings(p.document))


def test_legacy_group_gate_unavailable_is_explicit():
    from fathom.target import target_tables
    s={'group_column':'g','value_column':'y','value_type':'numeric','share_denominator':5,'group_missing':0,'groups':[{'value':'A','n':5,'share':1,'valid':5,'missing':0,'statistics':{},'small':False,'contrasts':[]}]}
    row=target_tables({'target_analysis':{'target':'y','ranked':[],'excluded':[],'groups':[s]}})[-1]['rows'][0]
    assert 'gate evidence unavailable' in row[-1]
