"""Fourth-field violations, explicit declarations and ordinary-clock decoys."""
import copy
import json
from pathlib import Path
import shutil
import subprocess

import pytest
from fathom.temporal_formats import parse_temporal
from fathom.connectors import CSVConnector
from fathom.profiler import profile
from fathom.config import validate_config

FIX=Path('tests/fixtures/time_definition/clocks.csv')

@pytest.mark.parametrize('raw,clock,fourth',[('02:39:34:07 AM','02:39:34','07'),('14:05:09:23','14:05:09','23'),('12:00:00:00 PM','12:00:00','00')])
def test_undeclared_fourth_preserves_clock_without_subsecond_guess(raw,clock,fourth):
    p=parse_temporal(raw,'TIME');assert p and p['time']==clock and 'date' not in p
    assert p['precision']=='second' and p['fourth_field']=={'kind':'undeclared','raw':fourth}
    assert 'microsecond' not in p and 'fractional_digits' not in p
    assert parse_temporal(raw)==p
    assert 'fourth_field' not in parse_temporal('14:05:09','TIME')


def test_declared_fraction_or_frames_never_silently_interchange():
    from fathom.temporal_formats import temporal_fault
    a=parse_temporal('14:05:09:07','%H:%M:%S:%f');assert a['microsecond']==70000
    f=parse_temporal('14:05:09:07','%H:%M:%S:%F',24)
    assert f['fourth_field']=={'kind':'frame','raw':'07','frame':7,'frame_rate':24}
    assert f['precision']=='frame' and 'microsecond' not in f
    assert parse_temporal('14:05:09:24','%H:%M:%S:%F',24) is None
    assert temporal_fault('14:05:09:24','%H:%M:%S:%F',24)['code']=='frame_at_or_above_rate'
    assert parse_temporal('14:05:09:29','%H:%M:%S:%F',29.97)
    assert parse_temporal('14:05:09:30','%H:%M:%S:%F',29.97) is None
    assert parse_temporal('14:05:09:29','%H:%M:%S:%f')['microsecond']==290000


@pytest.mark.parametrize('meta',[{'date_format':'%H:%M:%S:%F'}, {'date_format':'%H:%M:%S:%F','frame_rate':0}, {'date_format':'%H:%M:%S:%F','frame_rate':True}, {'date_format':'%H:%M:%S:%F','frame_rate':float('inf')}, {'date_format':'TIME','frame_rate':24}, {'date_format':'%H:%M:%F','frame_rate':24}, {'date_format':'%H:%M:%S:%f:%F','frame_rate':24}])
def test_frame_declarations_fail_before_output(tmp_path,meta):
    with pytest.raises(ValueError):validate_config({'columns':{'clock':meta}})
    import yaml
    from fathom.cli import main
    cfg=tmp_path/'bad.yaml';cfg.write_text(yaml.safe_dump({'columns':{'clock':meta}}))
    out=tmp_path/'no';assert main(['profile',str(FIX),'--config',str(cfg),'--out',str(out)])!=0
    assert not out.exists()


def test_profile_explains_ambiguity_and_named_frame_faults_with_clean_decoy():
    from fathom.renderers import render_html,render_markdown
    data=CSVConnector(FIX).load();p=profile(data)
    c=p.document['columns'][0];s=c['univariate']['statistics']
    assert c['statistics']['valid']==6 and s['subsecond']['undeclared_count']==6
    assert s['subsecond']['fraction_count']==0 and s['subsecond']['frame_count']==0
    b=s['intraday']['bases'][0];assert b['hour_counts']['02']==3 and b['second_counts']['34']==4
    assert any(f.get('rule')=='ambiguous_clock_fourth' and 'clock' in f.get('columns',[]) for f in p.document['findings'])
    assert not any(f.get('rule')=='ambiguous_clock_fourth' and 'ordinary' in f.get('columns',[]) for f in p.document['findings'])
    assert 'fourth' in render_html(p).lower() and 'fourth' in render_markdown(p).lower()
    cfg={'columns':{'clock':{'date_format':'%I:%M:%S:%F %p','frame_rate':24}}}
    p=profile(data,cfg);c=p.document['columns'][0];s=c['univariate']['statistics']
    assert c['statistics']['valid']==3 and s['subsecond']['frame_count']==3
    assert s['parse_faults']['frame_at_or_above_rate']['count']==3
    assert any(f.get('rule')=='temporal_frame_fault' for f in p.document['findings'])
    assert 'frame_at_or_above_rate' in render_html(p)
    assert p.to_json()==profile(data,cfg).to_json()


def test_frame_timestamp_series_declines_chronology_explicitly():
    from fathom.timeseries import analyse
    cfg=validate_config({'columns':{'stamp':{'date_format':'%Y-%m-%d %H:%M:%S:%F','frame_rate':24}}})
    result=analyse([['2026-04-03 14:05:09:07']],['stamp'],cfg,{'time':'stamp','value':None,'granularities':['hour']},{})
    assert not result['granularities'] and 'frame' in result['observation_process']['unsupported_clock_reason'].lower()


@pytest.mark.skipif(shutil.which('node') is None,reason='Node runs the exact in-page grammar')
def test_fourth_field_python_browser_value_and_named_fault_parity():
    from fathom.temporal_picker import PARSER_JS
    from fathom.temporal_formats import temporal_fault,validate_declaration
    cases=[('02:39:34:07 AM',None,None),('02:39:34:07 AM','TIME',None),('14:05:09:23','TIME',None),('14:05:09:23','%H:%M:%S:%f',None),('02:39:34:07 AM','%I:%M:%S:%F %p',24),('14:05:09:24','%H:%M:%S:%F',24),('14:05:09:29','%H:%M:%S:%F',29.97),('14:05:09:30','%H:%M:%S:%F',29.97),('2026-04-03 14:05:09:07','%Y-%m-%d %H:%M:%S:%F',24),('14:05:09:9007199254740992','%H:%M:%S:%F',1e20),('14:05:09:000000000000000007','%H:%M:%S:%F',24),('١٤:٠٥:٠٩:٢٣','TIME',None),('14:05:09:٢٣','%H:%M:%S:%F',24),('ordinary','TIME',None),('14:05:09:10000000000000000000','TIME',None)]
    for function,py in [('temporalParse',parse_temporal),('temporalFault',temporal_fault)]:
        script=PARSER_JS+'\nconsole.log(JSON.stringify('+json.dumps(cases)+'.map(x=>'+function+'(...x))));'
        js=json.loads(subprocess.check_output(['node','-e',script],text=True));assert js==[py(*x) for x in cases]
    for fmt,rate in [('%H:%M:%S:%F',None),('%H:%M:%S:%F',0),('%H:%M:%F',24),('%H:%M:%S:%f:%F',24),('TIME',24)]:
        script=PARSER_JS+'\ntry{temporalDeclaration('+json.dumps(fmt)+','+json.dumps(rate)+');}catch(e){console.log(e.message);}'
        js=subprocess.check_output(['node','-e',script],text=True).strip()
        with pytest.raises(ValueError) as error:validate_declaration(fmt,rate)
        assert js==str(error.value)


def test_card_fields_evidence_literal_safety_and_yaml_rate_roundtrip():
    from fathom.configure import build_schema,config_yaml,render_page,yaml_js_from_page
    from fathom.time_definition import definition_pattern,lexical_fields
    data=CSVConnector(FIX).load();s=build_schema(profile(data).document,data.frame,{})
    p=s['columns'][0]['temporal_picker'];d=p['definition']
    assert [f['raw'] for f in d['fields']]==['02','39','34','07','AM']
    assert d['fields'][3]['evidence']['min']==0 and d['fields'][3]['evidence']['max']==99
    roles=['I','M','S','F','p'];fmt=definition_pattern(d,roles);assert fmt=='%I:%M:%S:%F %p'
    assert [f['raw'] for f in lexical_fields('03/04/2026 14:05+02:00')['fields']]==['03','04','2026','14','05','+02:00']
    assert [f['raw'] for f in lexical_fields('03-04-2026')['fields']]==['03','04','2026']
    raw={'columns':{'clock':{'type':'temporal','date_format':fmt,'frame_rate':24}}}
    s=build_schema(profile(data,raw).document,data.frame,raw)
    assert s['columns'][0]['temporal_picker']['fourth_ambiguity']==[]
    selected=copy.deepcopy(s['initial']);selected['columns']['clock']['frame_rate']=30
    y=config_yaml(s,selected);assert 'frame_rate: 30' in y and 'frame_rate: 24' not in y
    validate_config(__import__('yaml').safe_load(y))
    legacy=copy.deepcopy(s)
    for c in legacy['columns']:
        if c.get('temporal_picker'):c['temporal_picker'].pop('definition',None)
    assert 'Define time fields' in render_page(legacy)
    assert all('definition' not in c.get('temporal_picker',{}) for c in legacy['columns'])
    page=render_page(s)
    assert page.count('data-definition=')==sum(bool(c.get('temporal_picker')) for c in s['columns'])
    assert 'Define time fields' in page and 'Observed min / max' in page and 'Field tokens and terminal fallback' in page
    s['columns'][0]['temporal_picker']['definition']['fields'][0]['raw']='</script><img src=x onerror=alert(1)>'
    assert '</script><img' not in render_page(s)
    if shutil.which('node'):
        script=yaml_js_from_page(page)+'\nconsole.log(configYaml('+json.dumps(s)+','+json.dumps(selected)+'));'
        assert subprocess.check_output(['node','-e',script],text=True).rstrip()==y.rstrip()
        from fathom.temporal_picker import PARSER_JS
        script=PARSER_JS+'\nconsole.log(definitionPattern('+json.dumps(d)+','+json.dumps(roles)+'));'
        assert subprocess.check_output(['node','-e',script],text=True).strip()==fmt


def test_new_subsecond_artifact_validation_and_clean_legacy():
    from fathom.models import ProfilingResult
    data=CSVConnector(FIX).load();p=profile(data)
    d=copy.deepcopy(p.document);d['columns'][0]['univariate']['statistics']['subsecond']['undeclared_count']='six'
    with pytest.raises(ValueError,match='subsecond'):ProfilingResult(d)
    d=copy.deepcopy(p.document)
    for c in d['columns']:c.get('univariate',{}).get('statistics',{}).pop('subsecond',None)
    ProfilingResult(d)


def test_all_out_of_rate_and_decimal_clock_clean_profiles():
    from fathom.models import GuideDataFrame
    import pandas as pd
    data=CSVConnector(FIX).load();data.frame['clock']=['02:39:34:99 AM']*len(data.frame);data.raw_rows=None
    p=profile(data,{'columns':{'clock':{'date_format':'%I:%M:%S:%F %p','frame_rate':24}}})
    s=p.document['columns'][0]['univariate']['statistics']
    assert s['temporal_kind']=='time'
    assert s['valid']==0 and s['parse_faults']['frame_at_or_above_rate']['count']==6
    assert s['subsecond']['frame_count']==0
    p=profile(data,{'columns':{'clock':{'date_format':'%I:%M:%S:%f %p'}}})
    s=p.document['columns'][0]['univariate']['statistics']
    assert s['valid']==6 and s['subsecond']['fraction_count']==6 and s['subsecond']['fraction_min_microsecond']==990000
    assert not any(f.get('rule') in ('ambiguous_clock_fourth','temporal_frame_fault') and 'clock' in f.get('columns',[]) for f in p.document['findings'])


def test_custom_clock_with_literal_prefix_keeps_named_faults_when_all_invalid():
    data=CSVConnector(FIX).load();data.frame['clock']=['at 14:05:09:99']*len(data.frame);data.raw_rows=None
    p=profile(data,{'columns':{'clock':{'date_format':'at %H:%M:%S:%F','frame_rate':24}}})
    s=p.document['columns'][0]['univariate']['statistics']
    assert s['temporal_kind']=='time' and s['parse_faults']['frame_at_or_above_rate']['count']==6
