"""Identifier roles/keys: violating and clean exact-value decoys."""
import copy,json,shutil,subprocess
from pathlib import Path
import pytest
from fathom.identifiers import identifier_profile
from fathom.profiler import profile,rank_pairs
from fathom.connectors import CSVConnector
from fathom.configure import build_schema,config_yaml,render_page,yaml_js_from_page
from fathom.models import ProfilingResult
from fathom.renderers import render_html,render_markdown
from fathom.summary_view import summary_tables

FIX=Path('tests/fixtures/identifiers/keys.csv')
CFG={'target':'value','columns':{n:{'role':'identifier'} for n in ['row_code','entity_key','sequence','format_code']}}

def result():return profile(CSVConnector(FIX).load(),CFG)


def test_exact_identifier_duplicates_gaps_and_clean_decoys():
    s=identifier_profile(['001','002','004','002',None,'009'],'human')
    assert (s['missing'],s['distinct'],s['duplicate_values'],s['duplicate_rows'],s['rows_in_repeated_values'])==(1,4,1,1,2)
    assert s['duplicates'][0]=={'value':'002','count':2,'positions':[2,4],'omitted_positions':0}
    assert s['numeric']['missing_integer_labels']==5 and s['numeric']['order']=='mixed'
    assert s['leading_zeros']['count']==5 and not s['unique_per_row']
    clean=identifier_profile(['001','002','003'],'human');assert clean['unique_per_row'] and clean['numeric']['order']=='strictly increasing' and clean['numeric']['missing_integer_labels']==0
    huge=identifier_profile(['9007199254740992','9007199254740993','9007199254740995'],'human')
    assert huge['distinct']==3 and huge['numeric']['missing_integer_labels']==1
    assert huge['numeric']['gaps'][0]['from']=='9007199254740994'
    from fathom.identifier_view import identifier_tables
    extreme=identifier_profile(['1','1e1000'],'human')
    assert identifier_tables({'identifier':extreme})
    blank=identifier_profile([None,None],'human');assert blank['unique_nonmissing'] is None and blank['numeric']['status']=='not computed'
    varied=identifier_profile(['AB-001','ab-2','AB_003'],'human');assert len(varied['patterns'])==3 and varied['numeric']['status']=='not computed'
    fractional=identifier_profile(['1.1','1.2','1.3'],'human');assert fractional['numeric']['order']=='strictly increasing' and fractional['numeric']['missing_integer_labels'] is None


def test_identifiers_report_links_counts_and_distribution_exclusion():
    p=result();before=p.to_json();d=p.document
    cs={c['name']:c for c in d['columns']};assert cs['row_code']['identifier']['missing']==1
    assert cs['row_code']['identifier']['duplicate_rows']==1
    assert cs['entity_key']['identifier']['duplicate_rows']==12
    assert all(c['univariate']['role']=='identifier' for c in d['columns'] if 'identifier' in c)
    names={row[0] for t in summary_tables(d) for row in t['rows']}
    assert not names&{'row_code','entity_key','sequence','format_code'} and 'value' in names
    assert not {'row_code','entity_key','sequence','format_code'}&{r['left'] for r in d['selection']['ranked']}
    for text in [render_html(p),render_markdown(p)]:
        assert 'Identifiers' in text and 'leading zeros' in text.lower()
        assert 'rows-key-1' in text and 'identifier role' in text.lower()
        assert 'missing records' in text and '0004' in text
    assert 'href="#rows-key-1"' in render_html(p)
    assert p.to_json()==before and render_html(ProfilingResult(json.loads(before)))==render_html(p)


def test_identifier_target_and_quality_pair_cannot_reenter_budget():
    from fathom.config import validate_config
    p=result();d=p.document;rows=CSVConnector(FIX).load().frame.values.tolist()
    cfg=validate_config({**CFG,'target':'sequence'})
    q=profile(CSVConnector(FIX).load(),cfg)
    assert not q.document['selection']['ranked'] and not q.document['bivariate']
    assert any('identifier' in r['reason'] for r in q.document['selection']['excluded'])
    candidates=[{'left':'entity_key','right':'value','method':'missingness_by_group','statistics':{'spread':1,'n':len(rows)},'uncertainty':'synthetic'}]
    cfg=validate_config({'pair_budget':1})
    s,pairs,deps=rank_pairs(rows,d['columns'],cfg,{'target':None,'budget':1,'selected':[],'excluded':[]},candidates,{})
    assert not pairs and not s['ranked'] and any('identifier' in x['reason'] for x in s['excluded'])


def test_roles_suggestions_are_unticked_and_roundtrip_both_yaml_generators():
    data=CSVConnector(FIX).load();p=profile(data);s=build_schema(p.document,data.frame,{})
    offered=next(c for c in s['columns'] if c['name']=='row_code');assert any(x['key']=='role' and x['value']=='identifier' for x in offered['suggestions'])
    assert config_yaml(s,{})=='{}\n'
    raw={'columns':{'row_code':{'role':'identifier'},'entity_key':{'role':'quantity'}}}
    p=profile(data,raw);s=build_schema(p.document,data.frame,raw)
    assert s['initial']['columns']['row_code']['role']=='identifier'
    y=config_yaml(s,{'columns':{'row_code':{'role':'quantity'}}});assert 'quantity' in y and 'identifier' not in y
    assert not any(c['name']=='entity_key' and 'identifier' in c for c in p.document['columns'])
    if shutil.which('node'):
        for choices in [s['initial'],{'columns':{'row_code':{'role':'quantity'}}}]:
            js=yaml_js_from_page(render_page(s))+'\nconsole.log(configYaml('+json.dumps(s)+','+json.dumps(choices)+'));'
            assert subprocess.check_output(['node','-e',js],text=True).rstrip()==config_yaml(s,choices).rstrip()
    assert 'data-field="role"' in render_page(s)


def test_identifier_schema_key_basis_and_malformed_saved_values():
    p=profile(CSVConnector(FIX).load(),{'schema':{'key':['row_code']}})
    c=p.document['columns'][0];assert 'human' in c['univariate']['role_basis'] and 'inferred' not in c['identifier']['basis']
    d=copy.deepcopy(p.document);d['columns'][0]['identifier']['missing']='one'
    with pytest.raises(ValueError,match='identifier'):ProfilingResult(d).validate()


def test_panel_identifiers_link_actual_series_entries(tmp_path):
    from fathom.panel import build_panel
    from fathom.panel_view import html,markdown
    data=CSVConnector(Path('tests/fixtures/panel/panel.csv')).load()
    cfg={'series':['series'],'time':'time','value':'value','period':'day','exposure':'exposure','observation_state':'state'}
    p=build_panel(data,cfg);assert p.document['identifiers'][0]['column']=='series'
    h=html(p);m=markdown(p)
    assert 'href="#panel-series-0"' in h and 'id="panel-series-0"' in h
    assert '## Identifiers' in m and '<a id="panel-series-0">' in m
    assert 'whole input' in h and 'not training-model parameters' in h
    assert p.to_json()==build_panel(data,cfg).to_json()
