"""Clock/timestamp parsing: violating values and calendar/text decoys."""
import json
from pathlib import Path
import pytest
from fathom.temporal_formats import parse_temporal,validate_format
from fathom.profiler import profile
from fathom.connectors import CSVConnector
from fathom.config import validate_config

@pytest.mark.parametrize('raw,expected', [('14:05','14:05:00'),('2:05 PM','14:05:00'),('12:00 AM','00:00:00'),('12:00 PM','12:00:00'),('14:05:09.123','14:05:09.123000')])
def test_time_has_clock_but_never_a_date(raw,expected):
    p=parse_temporal(raw,'TIME');assert p['kind']=='time' and p['time']==expected and 'date' not in p
    assert p['clock_basis']=='naive'
    for bad in ['24:00','14:60','14:05:60','0:05 PM','13:05 PM','words','2026-04-03']:assert parse_temporal(bad,'TIME') is None


def test_timestamp_preserves_written_date_clock_and_offset():
    a=parse_temporal('2026-04-03T14:05:09.123+02:00','DATETIME')
    b=parse_temporal('2026-04-03T12:05:09.123Z','DATETIME')
    n=parse_temporal('2026-04-03 14:05','DATETIME')
    assert a['date']=='2026-04-03' and a['time']=='14:05:09.123000' and a['clock_basis']=='+02:00'
    assert b['time']=='12:05:09.123000' and b['clock_basis']=='+00:00'
    assert n['clock_basis']=='naive' and n['kind']=='timestamp'
    for bad in ['2026-02-30T14:00','2026-01-01T24:00','2026-01-01T14:00+24:00']:assert parse_temporal(bad,'DATETIME') is None


def test_custom_pattern_is_explicit_portable_and_validated():
    p=parse_temporal('03/04/2026 14:05','%d/%m/%Y %H:%M')
    assert p['date']=='2026-04-03' and p['time']=='14:05:00'
    assert parse_temporal('30/02/2026 14:05','%d/%m/%Y %H:%M') is None
    assert parse_temporal('2:05 PM','%I:%M %p')['time']=='14:05:00'
    for pattern,token in [('%Q','%Q'),('%Y-%m-%d %','%'),('%-d/%m/%Y','%-'),('%m/%d','%Y'),('%I:%M','%p')]:
        with pytest.raises(ValueError,match=__import__('re').escape(token)):validate_format(pattern)
        with pytest.raises(ValueError):validate_config({'columns':{'x':{'date_format':pattern}}})
    assert parse_temporal('1976') is None and parse_temporal('hello') is None
    assert parse_temporal('1976','YEAR')['date']=='1976-01-01'


def test_mixed_clock_profiles_separate_bases_and_keep_invalid_values():
    p=profile(CSVConnector(Path('tests/fixtures/temporal/clocks.csv')).load(),{'columns':{'clock':{'type':'temporal','date_format':'TIME'},'stamp':{'type':'temporal','date_format':'DATETIME'},'custom':{'type':'temporal','date_format':'%d/%m/%Y %H:%M'}}})
    cs={c['name']:c for c in p.document['columns']}
    c=cs['clock'];assert c['statistics']['valid']==23 and c['statistics']['invalid']==1
    s=c['univariate']['statistics'];assert s['temporal_kind']=='time' and not s.get('earliest') and not s.get('year_counts')
    assert s['intraday']['bases'][0]['hour_counts']['14']==11
    assert s['intraday']['bases'][0]['earliest']=='00:05:00'
    t=cs['stamp']['univariate']['statistics'];assert t['temporal_kind']=='timestamp'
    assert {x['basis'] for x in t['intraday']['bases']}=={'naive','+02:00','-05:00'}
    assert sum(x['count'] for x in t['intraday']['bases'])==23
    assert all('weekday_hour_counts' in x for x in t['intraday']['bases'])
    assert cs['number']['effective_type']=='numeric'
    assert any(f.get('rule')=='temporal_clock_bases' for f in p.document['findings'])
    assert p.to_json()==profile(CSVConnector(Path('tests/fixtures/temporal/clocks.csv')).load(),{'columns':{'clock':{'type':'temporal','date_format':'TIME'},'stamp':{'type':'temporal','date_format':'DATETIME'},'custom':{'type':'temporal','date_format':'%d/%m/%Y %H:%M'}}}).to_json()


def test_invalid_pattern_fails_before_output(tmp_path):
    from fathom.cli import main
    cfg=tmp_path/'bad.yaml';cfg.write_text('columns: {clock: {date_format: "%Q"}}\n')
    out=tmp_path/'never'
    assert main(['profile','tests/fixtures/temporal/clocks.csv','--config',str(cfg),'--out',str(out)])!=0
    assert not out.exists()


def test_declared_series_cannot_invent_dates_or_mix_offsets():
    from fathom.timeseries import analyse
    from fathom.config import validate_config
    rows=[['14:05'],['15:05']]
    cfg=validate_config({'columns':{'t':{'date_format':'TIME'}}})
    item={'time':'t','value':None,'granularities':['hour']}
    r=analyse(rows,['t'],cfg,item,{})
    assert not r['granularities'] and 'no calendar date' in r['observation_process']['unsupported_clock_reason']
    mixed=[['2026-04-03T14:05+02:00'],['2026-04-03T14:05']]
    cfg=validate_config({'columns':{'t':{'date_format':'DATETIME'}}})
    r=analyse(mixed,['t'],cfg,item,{})
    assert not r['granularities'] and r['observation_process']['rows_with_temporal_reading']==2
    assert 'Mixed' in r['observation_process']['unsupported_clock_reason']
    clean=[['2026-04-03T14:05+02:00'],['2026-04-03T15:05+02:00']]
    r=analyse(clean,['t'],cfg,item,{})
    assert '+02:00' in r['observation_process']['first'] and r['observation_process']['rows_with_parsed_time']==2


def test_saved_intraday_validation_and_legacy_note_remain_explicit():
    import copy
    from fathom.models import ProfilingResult
    from fathom.renderers import datetime_note
    p=profile(CSVConnector(Path('tests/fixtures/temporal/clocks.csv')).load())
    d=copy.deepcopy(p.document);c=next(c for c in d['columns'] if c['name']=='stamp')
    assert 'no date invented' in datetime_note(c)
    c['univariate']['statistics']['intraday']['bases'][0]['hour_counts']['00']='two'
    with pytest.raises(ValueError,match='intraday counts'):ProfilingResult(d).validate()
    old={'name':'old','effective_type':'temporal','univariate':{'statistics':{'parse_formats':{'ISO_DATETIME':1}}}}
    assert 'time of day excluded' in datetime_note(old)
