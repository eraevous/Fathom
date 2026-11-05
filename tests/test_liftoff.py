"""Spec013: discovery is not a declaration; every new behavior has a clean decoy."""
import copy,json,os,subprocess,sys,shutil
from pathlib import Path
import pytest,yaml
from fathom.connectors import CSVConnector
from fathom.profiler import profile
from fathom.models import ProfilingResult
from fathom.configure import build_schema,config_yaml,YAML_JS,schema_from_page

FIX=Path(__file__).parent/'fixtures/liftoff'

def lift(name='planted'):
    from fathom.liftoff import build_liftoff
    return build_liftoff(CSVConnector(FIX/(name+'.csv')).load())


def test_default_profile_is_not_modified_by_provisional_measurements():
    p=lift();d=copy.deepcopy(p.document);d.pop('liftoff')
    assert d==profile(CSVConnector(FIX/'planted.csv').load()).document
    b=p.document['liftoff'];assert b['effective_configuration']=={}
    assert p.document['purpose']['target'] is None and p.document['row_structure']['intervals']==[] and p.document['time_series']['declared']==[]
    assert config_yaml(b['configuration'],{})=='{}\n'
    assert lift('clean').document['liftoff']['previews']=={'intervals':[],'time_series':[]}


def test_interval_preview_matches_unchanged_declared_engine():
    p=lift();entry=next(e for e in p.document['liftoff']['previews']['intervals'] if e['declaration']=={'start':'start','end':'end'})
    d=profile(CSVConnector(FIX/'planted.csv').load(),{'intervals':[entry['declaration']]}).document
    assert entry['result']==d['row_structure']['intervals'][0] and entry['result']['end_equals_start']==1
    assert all(f['status']=='provisional' and f['message'].startswith('If you declare') for f in entry['findings'])
    clean=lift('periodic').document['liftoff']['previews']['intervals'][0]
    assert clean['result']['end_equals_start']==0


def test_series_preview_retains_states_and_matches_declared_engine():
    p=lift('periodic');entry=p.document['liftoff']['previews']['time_series'][0]
    d=profile(CSVConnector(FIX/'periodic.csv').load(),{'time_series':[entry['declaration']]}).document
    assert entry['result']==d['time_series']['series'][0]
    g=next(g for g in entry['result']['groups'][0]['granularities'] if g['granularity']=='hour')
    assert any(l['lag']==24 for l in g['wavelength']['values']['dominant_lags'])
    assert all(f['kind'] in ('observation','question') and f['status']=='provisional' for f in entry['findings'])
    assert any(s['absent'] or s['insufficient evidence'] for s in entry['result']['groups'][0]['signals'])


def test_zero_discovery_is_counted_not_asserted_as_a_mechanism():
    p=lift();fs=p.document['liftoff']['automated_findings'];f=next(f for f in fs if f['kind']=='observation')
    assert f['rule']=='all_zero_group' and f['evidence'][0]['value']['group_zeros']==31
    assert any('structural' in f['message'] and f['kind']=='question' for f in fs)
    assert not any(f.get('rule')=='all_zero_group' for f in p.document['findings'])
    assert lift('clean').document['liftoff']['automated_findings']==[]


def test_short_and_constant_series_decoys(make_profile):
    from fathom.liftoff import build_liftoff
    p=make_profile('when,x\n'+''.join(f'2020-01-{i+1:02},0\n' for i in range(10)))
    # Build on the input CSV that make_profile wrote.
    d=build_liftoff(CSVConnector(p.document['source']['origin']).load()).document
    assert d['liftoff']['previews']['time_series']==[] and d['liftoff']['automated_findings']==[]
    p=lift('constant');entry=p.document['liftoff']['previews']['time_series'][0]
    g=next(g for g in entry['result']['groups'][0]['granularities'] if g['granularity']=='hour')
    assert g['wavelength']['values']['status']=='undefined'
    assert not any(f['kind']=='action' for f in entry['findings'])


def test_candidate_omissions_are_counted(monkeypatch):
    import fathom.liftoff as m
    monkeypatch.setattr(m,'MAX_SERIES_PREVIEWS',1)
    d=lift().document['liftoff']
    assert len(d['previews']['time_series'])==1 and d['coverage']['series_omitted']==1
    assert len(d['configuration']['time_series_suggestions'])==2


def test_series_yaml_generators_and_unchanged_configure():
    p=lift();schema=p.document['liftoff']['configuration']
    sel={'target':'amount','intervals':[['start','end']],'time_series':[{'time':'start','value':None,'granularities':['hour']} ]}
    text=config_yaml(schema,sel);doc=yaml.safe_load(text)
    from fathom.config import validate_config
    cfg=validate_config(doc,[c['name'] for c in p.document['columns']]);assert cfg['time_series'][0]['time']=='start'
    assert 'source:' not in text and cfg['target']=='amount'
    plain=build_schema(profile(CSVConnector(FIX/'planted.csv').load()).document,CSVConnector(FIX/'planted.csv').load().frame,None)
    assert 'time_series_suggestions' not in plain and config_yaml(plain,{})=='{}\n'
    node=shutil.which('node')
    if node:
        r=subprocess.run([node,'-e',YAML_JS+'\nvar a=JSON.parse(require("fs").readFileSync(0,"utf8"));process.stdout.write(configYaml(a[0],a[1]));'],input=json.dumps([schema,sel]),text=True,capture_output=True)
        assert r.returncode==0 and r.stdout==text


@pytest.mark.parametrize('key,value',[('stage','declared'),('effective_configuration',{'target':'amount'}),('previews',[])])
def test_malformed_liftoff_envelope_fails_at_load(tmp_path,key,value):
    d=copy.deepcopy(lift().document);d['liftoff'][key]=value
    path=tmp_path/'bad.json';path.write_text(json.dumps(d))
    with pytest.raises(ValueError):ProfilingResult.load(path)


def test_brief_is_static_precedes_configurations_and_escapes_names(tmp_path):
    from fathom.liftoff import build_liftoff,render_liftoff
    evil='</script><img src=x onerror=alert(1)>'
    path=tmp_path/'evil.csv'
    import csv
    with path.open('w',newline='') as f:
        w=csv.writer(f);w.writerow([evil,'amount']);w.writerows([[f'2020-01-{i+1:02}',i] for i in range(30)])
    page=render_liftoff(build_liftoff(CSVConnector(path).load()))
    brief=page.split('<section id="brief">',1)[1].split('<!-- end brief -->',1)[0]
    assert '<script' not in brief and '<img' not in page
    assert page.index('id="brief"')<page.index('id="configurations"')<page.index('Evidentiary rules (read-only)')
    assert schema_from_page(page)['initial']['target'] is None
    assert 'If you declare' in page


def test_liftoff_command_fresh_bytes_and_no_config_option(tmp_path):
    files=[]
    for seed in ['1','99']:
        out=tmp_path/seed
        r=subprocess.run([sys.executable,'-m','fathom','liftoff',str(FIX/'planted.csv'),'--out',str(out)],env={**os.environ,'PYTHONPATH':str(Path(__file__).parents[1]/'src'),'PYTHONHASHSEED':seed},text=True,capture_output=True)
        assert r.returncode==0,r.stderr
        files.append({p.name:p.read_bytes() for p in out.iterdir()})
    assert files[0]==files[1] and set(files[0])=={'liftoff.html','liftoff-profile.json'}
    r=subprocess.run([sys.executable,'-m','fathom','liftoff',str(FIX/'planted.csv'),'--config','not.yaml','--out',str(tmp_path/'bad')],capture_output=True)
    assert r.returncode==2 and not (tmp_path/'bad').exists()


def test_optional_stats_absence_does_not_block_liftoff(monkeypatch):
    import builtins
    original=builtins.__import__
    def no_stats(name,*a,**k):
        if name.startswith('scipy'):raise ImportError('absent in clean core decoy')
        return original(name,*a,**k)
    monkeypatch.setattr(builtins,'__import__',no_stats)
    d=lift('periodic').document
    assert d['liftoff']['previews']['time_series'] and d['time_series']['declared']==[]
    g=d['liftoff']['previews']['time_series'][0]['result']['groups'][0]['granularities'][0]
    assert g['wavelength']['spectral']['status']=='not computed' and 'scipy' in g['wavelength']['spectral']['reason'].lower()


def test_saved_liftoff_render_roundtrip(tmp_path):
    from fathom.liftoff import render_liftoff
    p=lift();path=tmp_path/'profile.json';path.write_text(p.to_json());out=tmp_path/'render'
    r=subprocess.run([sys.executable,'-m','fathom','render',str(path),'--out',str(out)],env={**os.environ,'PYTHONPATH':str(Path(__file__).parents[1]/'src')},capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    assert (out/'liftoff.html').read_text()==render_liftoff(p)


@pytest.mark.parametrize('field',['ordinary_interval','ordinary_series','selected_target'])
def test_saved_discovery_cannot_claim_applied_declarations(field):
    d=copy.deepcopy(lift().document)
    if field=='ordinary_interval':d['row_structure']['intervals']=[{'start':'start','end':'end'}]
    elif field=='ordinary_series':d['time_series']['declared']=[{'time':'start'}]
    else:d['liftoff']['configuration']['initial']['target']='amount'
    with pytest.raises(ValueError):ProfilingResult(d)


def test_hostile_series_names_and_granularity_roundtrip(tmp_path):
    from datetime import datetime,timedelta
    import csv
    from fathom.liftoff import build_liftoff
    path=tmp_path/'special.csv'
    with path.open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['__proto__','constructor']);w.writerows([[str(datetime(2019,1,1)+timedelta(hours=i)),i+.5] for i in range(60)])
    p=build_liftoff(CSVConnector(path).load());schema=p.document['liftoff']['configuration'];sel={'time_series':[{'time':'__proto__','value':'constructor','granularities':['hour','day']}]}
    text=config_yaml(schema,sel)
    from fathom.config import validate_config
    assert validate_config(yaml.safe_load(text),['__proto__','constructor'])['time_series'][0]['value']=='constructor'
    node=shutil.which('node')
    if node:
        r=subprocess.run([node,'-e',YAML_JS+'\nvar a=JSON.parse(require("fs").readFileSync(0,"utf8"));process.stdout.write(configYaml(a[0],a[1]));'],input=json.dumps([schema,sel]),capture_output=True,text=True)
        assert r.returncode==0 and r.stdout==text


@pytest.mark.parametrize('a,b_zeros',[(10,10),(9,0),(10,8)])
def test_balanced_zeros_small_groups_and_small_contrast_are_clean(a,b_zeros):
    from fathom.liftoff import zero_contrasts
    rows=[['A','0']]*a+[['B','0']]*b_zeros+[['B','1']]*(10-b_zeros)
    cols=[{'name':'g','effective_type':'categorical'},{'name':'v','effective_type':'numeric'}]
    block,fs=zero_contrasts(rows,cols,{'source':{'sha256':'a'*64}})
    assert block['results']==[] and fs==[]


def test_zero_denominators_exclude_missing_labels_and_distinguish_invalid_cells():
    from fathom.liftoff import zero_contrasts
    rows=[['A','0']]*10+[['A',None],['A','bad']]+[['B','1']]*10+[[None,'0']]
    cols=[{'name':'g','effective_type':'categorical'},{'name':'v','effective_type':'numeric'}]
    block,fs=zero_contrasts(rows,cols,{'source':{'sha256':'a'*64}})
    v=block['results'][0]
    assert (v['group_finite'],v['group_zeros'],v['group_missing'],v['group_invalid'],v['missing_group_rows'])==(10,10,1,1,1)
    assert all(f['kind'] in ['observation','question'] for f in fs)
