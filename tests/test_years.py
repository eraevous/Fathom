"""An explicit format recovers annual data without guessing that integers are dates."""
import json,os,subprocess,sys
from pathlib import Path
import pytest
from fathom.parsing import parse_date
from fathom.config import load_config
from fathom.profiler import profile
from fathom.connectors import CSVConnector
from fathom.models import ProfilingResult
from fathom.renderers import render_html,render_markdown
from fathom.panel import build_panel,panel_files

FIX=Path('tests/fixtures/years')


@pytest.mark.parametrize('value,expected',[(1976,'1976-01-01'),('2024','2024-01-01'),('0001','0001-01-01')])
def test_explicit_year_integer_and_string(value,expected):
    p=parse_date(value,'YEAR');assert p['date']==expected and p['format']=='YEAR' and p['precision']=='year'
    assert parse_date(value) is None


@pytest.mark.parametrize('value',[True,1976.0,'76','2024.0','20x4','0000','10000',None])
def test_year_invalid_lexemes_are_not_coerced(value):assert parse_date(value,'YEAR') is None


def test_numeric_yearlooking_decoy_stays_numeric_without_declaration():
    data=CSVConnector(FIX/'panel.csv').load();d=profile(data).document
    assert next(c for c in d['columns'] if c['name']=='year')['effective_type']=='numeric'
    assert next(c for c in d['columns'] if c['name']=='code')['effective_type']=='numeric'
    d=profile(data,load_config(FIX/'profile.yaml')).document
    c=next(c for c in d['columns'] if c['name']=='year')
    assert c['effective_type']=='temporal' and c['statistics']['valid']==52 and c['statistics']['invalid']==0
    assert c['univariate']['statistics']['parse_formats']=={'YEAR':52}
    assert not c['univariate']['statistics']['weekday_counts'] and not c['univariate']['statistics']['month_counts']
    assert all(ch.get('period')=='year' for ch in c['univariate']['charts'])
    for text in [render_html(ProfilingResult(d)),render_markdown(ProfilingResult(d))]:assert 'January anchor' in text


def test_annual_profile_and_panel_preserve_missing_years_and_precision():
    data=CSVConnector(FIX/'panel.csv').load();p=profile(data,load_config(FIX/'profile.yaml'))
    for s in p.document['time_series']['series'][0]['groups']:
        assert [g['granularity'] for g in s['granularities']]==['year']
        g=s['granularities'][0];assert g['periods_in_span']==49 and g['missing_periods']==36
        assert not any(e['partial'] for e in g['edge_coverage'])
    cfg={'series':['entity','candidate'],'time':'year','value':'value','period':'year','date_format':'YEAR'}
    result=build_panel(data,cfg,FIX)
    assert len(result.document['rows'])==4
    for row,periods in zip(result.document['rows'],result.document['periods']):
        assert row['duration']['calendar_span']==49 and row['duration']['usable_observations']==13
        assert row['duration']['states']['absent']==36 and row['frequency']['observed_zero_periods']==0
        assert row['train_start']=='1976-01-01' and row['train_end']=='2024-12-31'
        assert row['wavelength']['year']['strength']['status']=='not estimable'
    assert panel_files(result)==panel_files(ProfilingResult(json.loads(result.to_json())))


def test_year_auto_uses_annual_only_and_iso_auto_is_unchanged(make_profile):
    years='year,value\n'+'\n'.join(f'{y},{1+y%3}' for y in range(1976,2025))+'\n'
    cfg={'columns':{'year':{'type':'temporal','date_format':'YEAR'}},'time_series':[{'time':'year','value':'value'}]}
    d=make_profile(years,cfg).document
    assert [g['granularity'] for g in d['time_series']['series'][0]['groups'][0]['granularities']]==['year']
    d=make_profile('year,value\n2020-01-01,1\n2024-01-01,2\n',{'time_series':[{'time':'year','value':'value'}]}).document
    assert 'year' not in [g['granularity'] for g in d['time_series']['series'][0]['groups'][0]['granularities']]


@pytest.mark.parametrize('declared',[None,'ISO'])
def test_wholly_failed_temporal_year_declaration_explains_nearest_format(make_profile,declared):
    meta={'type':'temporal',**({'date_format':declared} if declared else {})}
    d=make_profile('year,value\n1976,10\n2024,20\n',{'columns':{'year':meta},'target':'value','pair_budget':1}).document
    c=d['columns'][0];f=c['statistics']['parse_failure'];assert c['statistics']['invalid']==2 and f['suggested_formats']==['YEAR']
    assert f['formats_tried']==(['ISO'] if declared else ['DMY','ISO','ISO_DATETIME','MDY','MON_D_Y'])
    finding=next(x for x in d['findings'] if x['id']=='column-0-invalid')
    assert any(e.get('value')==f for e in finding['evidence'])
    text=render_html(ProfilingResult(d));assert 'Formats tried:' in text and 'date_format: YEAR' in text
    assert 'Formats tried:' in next(e['reason'] for e in d['target_analysis']['excluded'] if e['column']=='year')


def test_failure_decoys_no_match_partial_parse_and_reverse_format(make_profile):
    d=make_profile('x\nnot-a-date\nneither\n',{'columns':{'x':{'type':'temporal'}}}).document
    assert d['columns'][0]['statistics']['parse_failure']['suggested_formats']==[]
    d=make_profile('x\n2024-01-01\n1976\n',{'columns':{'x':{'type':'temporal'}}}).document
    assert d['columns'][0]['statistics']['invalid']==1 and 'parse_failure' not in d['columns'][0]['statistics']
    d=make_profile('x\n2024-01-01\n2020-01-01\n',{'columns':{'x':{'type':'temporal','date_format':'YEAR'}}}).document
    assert d['columns'][0]['statistics']['parse_failure']['suggested_formats']==['ISO']


def test_year_anchor_is_not_a_placeholder_or_month_day_pattern(make_profile):
    d=make_profile('year\n1900\n1970\n2024\n',{'columns':{'year':{'type':'temporal','date_format':'YEAR'}}}).document
    s=d['columns'][0]['univariate']['statistics'];assert s['placeholder_dates']==0
    assert not any(f.get('rule')=='placeholder_date' for f in d['findings'])
    assert 'Day ticks omit the year' not in render_html(ProfilingResult(d))
    d=make_profile('year\n'+'2020\n'*100+'2024\n',{'columns':{'year':{'type':'temporal','date_format':'YEAR'}}}).document
    assert d['row_structure']['temporal'][0]['period']['grain']=='year'


def test_failed_temporal_cli_warning_and_empty_decoy(tmp_path,capsys):
    from fathom.cli import main
    src=tmp_path/'x.csv';src.write_text('year\n1976\n2024\n');cfg=tmp_path/'c.yaml';cfg.write_text('columns: {year: {type: temporal}}\n')
    assert main(['profile',str(src),'--config',str(cfg),'--out',str(tmp_path/'out')])==0
    err=capsys.readouterr().err;assert 'Formats tried:' in err and 'date_format: YEAR' in err
    src.write_text('year\n""\n');assert main(['profile',str(src),'--config',str(cfg),'--out',str(tmp_path/'empty')])==0
    assert 'Formats tried:' not in capsys.readouterr().err


@pytest.mark.parametrize('command',['profile','panel'])
def test_annual_cli_socket_denied_byte_identity(tmp_path,command):
    out=tmp_path/'out';args=[command,str(FIX/'panel.csv'),'--config',str(FIX/(command+'.yaml')),'--out',str(out)]
    results=[]
    for denied in ['0','1']:
        r=subprocess.run([sys.executable,str(Path('tests/offline_runner.py').resolve()),*args],env={**os.environ,'PYTHONPATH':str(Path('src').resolve()),'FATHOM_DENY_NETWORK':denied},capture_output=True)
        assert r.returncode==0,r.stderr.decode();results.append((r.stdout,r.stderr,{str(p.relative_to(out)):p.read_bytes() for p in out.rglob('*') if p.is_file()}))
    assert results[0]==results[1]


def test_panel_year_format_is_explicit_and_strict(tmp_path):
    data=CSVConnector(FIX/'panel.csv').load()
    cfg={'series':['entity','candidate'],'time':'year','value':'value','period':'year'}
    with pytest.raises(ValueError,match='date_format: YEAR'):build_panel(data,cfg,FIX)
    with pytest.raises(ValueError,match='date_format'):build_panel(data,{**cfg,'date_format':[]},FIX)
    with pytest.raises(ValueError,match='requires panel period year'):build_panel(data,{**cfg,'date_format':'YEAR','period':'day'},FIX)
    with pytest.raises(ValueError,match='duplicate series/calendar period'):build_panel(data,{**cfg,'date_format':'YEAR','series':['entity']},FIX)
    src=tmp_path/'mixed.csv';src.write_text('year,entity,value\n2020,A,1\n2024-01-01,A,2\n')
    with pytest.raises(ValueError,match='Formats tried: YEAR'):build_panel(CSVConnector(src).load(),{**cfg,'series':['entity'],'date_format':'YEAR'},tmp_path)


def test_year_configurator_generators_retain_explicit_annual_declaration():
    import shutil
    from fathom.configure import build_schema,config_yaml,YAML_JS
    from fathom.config import read_config
    data=CSVConnector(FIX/'panel.csv').load();raw=read_config(FIX/'profile.yaml')
    d=profile(data,raw).document;schema=build_schema(d,data.frame,raw)
    text=config_yaml(schema,schema['initial']);assert 'YEAR' in text and 'year' in schema['ts_granularities']
    node=shutil.which('node')
    if node:
        r=subprocess.run([node,'-e',YAML_JS+';var s=JSON.parse(require("fs").readFileSync(0,"utf8"));process.stdout.write(configYaml(s,s.initial));'],input=json.dumps(schema),text=True,capture_output=True,check=True)
        assert r.stdout==text


def test_failed_format_tie_is_not_resolved_as_domain_knowledge(make_profile):
    d=make_profile('x\n03/04/2020\n05/06/2021\n',{'columns':{'x':{'type':'temporal','date_format':'ISO'}}}).document
    assert d['columns'][0]['statistics']['parse_failure']['suggested_formats']==['DMY','MDY']
