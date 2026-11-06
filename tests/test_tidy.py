"""Saved-artifact CSV fidelity, stable paths and CLI-only export controls."""
import csv,io,json,os,subprocess,sys,copy
from pathlib import Path
import pytest
from fathom.connectors import CSVConnector
from fathom.profiler import profile
from fathom.config import load_config
FIX=Path('tests/fixtures/summary')

def result():return profile(CSVConnector(FIX/'mixed.csv').load(),load_config(FIX/'config.yaml'))
def rows(text):return list(csv.DictReader(io.StringIO(text)))

def test_tidy_scalar_metrics_findings_relations_samples_are_faithful():
    from fathom.tidy import tidy_files
    p=result();before=p.to_json();files=tidy_files(p.document)
    assert set(files)=={'columns.csv','findings.csv','relations.csv','samples.csv'}
    data=rows(files['columns.csv']);r=next(r for r in data if r['column']=='amount' and r['metric']=='statistics.mean')
    assert float(r['value'])==next(c for c in p.document['columns'] if c['name']=='amount')['statistics']['mean'] and r['unit']=='credits'
    fs=rows(files['findings.csv']);assert len(fs)==len(p.document['findings'])
    assert [r['message'] for r in fs]==[f['message'] for f in p.document['findings']]
    assert any(k.startswith('evidence.') for k in fs[0])
    assert len(rows(files['relations.csv']))==len(p.document['bivariate'])
    samples=rows(files['samples.csv']);assert len(samples)==sum(len(p.document['samples'][k]) for k in ['first','last','random'])
    assert {r['sample'] for r in samples}=={'first','last','random'}
    assert files==tidy_files(json.loads(p.to_json())) and p.to_json()==before

def test_flat_paths_empty_and_hostile_values_do_not_collide():
    from fathom.tidy import flatten,tidy_files
    f=flatten({'a.b':1,'a':{'b':2},'x~y':True,'empty':[],'null':None})
    assert f['a~2b']==1 and f['a.b']==2 and f['x~0y'] is True and f['empty']==[] and f['null'] is None
    p=result();d=copy.deepcopy(p.document);d.pop('samples',None);d['bivariate']=[]
    d['findings'][0]['message']='literal =formula, "quote"\nand newline'
    files=tidy_files(d);assert 'samples.csv' not in files and rows(files['relations.csv'])==[]
    assert rows(files['findings.csv'])[0]['message']==d['findings'][0]['message']

def test_tidy_only_cli_requires_no_office_out_or_network(tmp_path):
    p=result();artifact=tmp_path/'profile.json';artifact.write_text(p.to_json());out=tmp_path/'tidy'
    cmd=[sys.executable,'tests/offline_runner.py','export',str(artifact),'--tidy',str(out)]
    env={**os.environ,'PYTHONPATH':'src','FATHOM_DENY_NETWORK':'1'}
    a=subprocess.run(cmd,env=env,capture_output=True);assert a.returncode==0,a.stderr.decode()
    files={p.name:p.read_bytes() for p in out.iterdir()};b=subprocess.run(cmd,env=env,capture_output=True)
    assert (a.stdout,a.stderr)==(b.stdout,b.stderr) and files=={p.name:p.read_bytes() for p in out.iterdir()}
    assert set(files)=={'columns.csv','findings.csv','relations.csv','samples.csv'}
    assert artifact.read_text()==p.to_json()

def test_nesting_measurement_depth_definition_is_explicit():
    from fathom.tidy import nesting_metrics
    m=nesting_metrics({'a':{'b':[1,{'c':2}]},'empty':[],'scalar':3})
    assert m['keys']['a']['max_depth']==3 and m['keys']['a']['median_depth']==2.5
    assert m['keys']['empty']['max_depth']==0 and m['keys']['scalar']['median_depth']==0
    assert '/a/b/1/c' in m['deepest_paths']


def test_liftoff_findings_include_all_automatic_and_conditional_collections():
    from fathom.liftoff import build_liftoff
    from fathom.tidy import tidy_files
    p=build_liftoff(CSVConnector('tests/fixtures/liftoff/planted.csv').load());d=p.document
    data=rows(tidy_files(d)['findings.csv'])
    expected=len(d['findings'])+len(d['liftoff']['automated_findings'])+sum(len(p['findings']) for previews in d['liftoff']['previews'].values() for p in previews)
    assert len(data)==expected
    assert any(r['collection']=='liftoff.automated_findings' for r in data)
    assert any(r['collection'].startswith('liftoff.previews.time_series') and r['message'].startswith('If you declare') for r in data)
