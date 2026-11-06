"""Portable browser/Python picker parity, raw-sample fidelity and declared choices."""
import copy,json,shutil,subprocess
from pathlib import Path
import pytest
from fathom.temporal_formats import parse_temporal,validate_format
from fathom.temporal_picker import PARSER_JS,picker_schema
from fathom.configure import build_schema,config_yaml,render_page,yaml_js_from_page
from fathom.connectors import CSVConnector
from fathom.profiler import profile

FIX=Path('tests/fixtures/temporal/clocks.csv')

def test_sample_rank_denominator_ambiguity_and_no_declaration():
    data=CSVConnector(FIX).load();p=profile(data);s=build_schema(p.document,data.frame,{})
    clock=s['columns'][0]['temporal_picker'];assert len(clock['samples'])==20 and len({v['position'] for v in clock['samples']})==20
    assert clock['formats'][0]['format']=='TIME' and clock['formats'][0]['matches']==20
    assert not s['initial']['columns'] and config_yaml(s,{})=='{}\n'
    custom=s['columns'][2]['temporal_picker'];assert custom['ambiguity']
    # Clean date decoy has only one viable numeric reading.
    d=copy.deepcopy(p.document);d['samples']['first'][0]['values'][2]='23/04/2026';d['samples']['first']=d['samples']['first'][:1];d['samples']['last']=[];d['samples']['random']=[]
    assert not picker_schema(d,2)['ambiguity']
    d['samples']['first'][0]['values'][2]='x… [truncated]'
    q=picker_schema(d,2,'DATETIME');assert q['denominator']==0 and q['samples'][0]['truncated']
    d.pop('samples');assert len(picker_schema(d,0)['samples'])==3


@pytest.mark.skipif(shutil.which('node') is None,reason='Node is a test-only browser-function runner')
def test_portable_python_javascript_values_and_errors_match():
    cases=[('14:05','TIME'),('2:05 PM','TIME'),('14:05:09.123','TIME'),('24:00','TIME'),('2026-04-03T14:05Z','DATETIME'),('2026-04-03T14:05:09.123-05:30','DATETIME'),('03/04/2026 14:05','%d/%m/%Y %H:%M'),('30/02/2026 14:05','%d/%m/%Y %H:%M'),('03.04.2026','%d.%m.%Y'),('03x04x2026','%d.%m.%Y'),('Jun 12 1998','MON_D_Y'),('2048','YEAR'),('03/04/2026','DMY'),('09:05:09.000','%H:%M:%S.%f')]
    script=PARSER_JS+'\nconsole.log(JSON.stringify('+json.dumps(cases)+'.map(x=>temporalParse(x[0],x[1]))));'
    js=json.loads(subprocess.check_output(['node','-e',script],text=True));py=[parse_temporal(*x) for x in cases]
    assert js==py
    for pattern in ['%Q','%Y-%m-%d %','%m/%d','%I:%M','%-d/%m/%Y']:
        script=PARSER_JS+'\ntry{temporalValidate('+json.dumps(pattern)+');}catch(e){console.log(e.message);}'
        message=subprocess.check_output(['node','-e',script],text=True).strip()
        with pytest.raises(ValueError) as exc:validate_format(pattern)
        assert message==str(exc.value)


def test_custom_yaml_roundtrip_and_hostile_sample_escaping():
    data=CSVConnector(FIX).load();raw={'columns':{'custom':{'type':'temporal','date_format':'%d/%m/%Y %H:%M'}}};p=profile(data,raw);s=build_schema(p.document,data.frame,raw)
    y=config_yaml(s,s['initial']);assert '%d/%m/%Y %H:%M' in y
    for name,fmt in [('clock','TIME'),('custom','%d/%m/%Y %H:%M')]:
        selected={'columns':{name:{'date_format':fmt}}};assert fmt in config_yaml(s,selected)
    if shutil.which('node'):
        script=yaml_js_from_page(render_page(s))+'\nconsole.log(configYaml('+json.dumps(s)+','+json.dumps(s['initial'])+'));'
        assert subprocess.check_output(['node','-e',script],text=True).rstrip()==y.rstrip()
    s['columns'][0]['temporal_picker']['samples'][0]['raw']='</script><img src=x onerror=alert(1)>'
    page=render_page(s);assert '</script><img' not in page and '&lt;img' in page
    assert 'aria-live="polite"' in page and 'Formats and samples above work offline' in page
    with pytest.raises(ValueError):config_yaml(s,{'columns':{'clock':{'date_format':'%Q'}}})
