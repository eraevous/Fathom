"""CLI-only configuration uses the same default state as the offline page."""
import json,os,shutil,subprocess,sys
from pathlib import Path
import pytest
from fathom.cli import main,summary_line
from fathom.configure import schema_from_page,config_yaml,YAML_JS


def test_terminal_yaml_matches_page_defaults_and_runs_second_stage(tmp_path):
    source=Path('tests/fixtures/liftoff/planted.csv');out=tmp_path/'discovery';dest=tmp_path/'nested/config.yaml'
    assert main(['liftoff',str(source),'--out',str(out),'--yaml',str(dest)])==0
    schema=schema_from_page((out/'liftoff.html').read_text())
    assert dest.read_bytes()==config_yaml(schema,schema['initial']).encode()==b'{}\n'
    assert main(['profile',str(source),'--config',str(dest),'--out',str(tmp_path/'profile')])==0
    d=json.loads((tmp_path/'profile/guide-profile.json').read_text())
    assert d['purpose']['target'] is None and not d['time_series']['declared'] and not d['row_structure']['intervals']
    assert 'guide liftoff DATA.csv --out discovery --yaml liftoff.yaml' in (out/'liftoff.html').read_text()
    node=shutil.which('node')
    if node:
        r=subprocess.run([node,'-e',YAML_JS+';var s=JSON.parse(require("fs").readFileSync(0,"utf8"));process.stdout.write(configYaml(s,s.initial));'],input=json.dumps(schema),text=True,capture_output=True,check=True)
        assert r.stdout.encode()==dest.read_bytes()


@pytest.mark.parametrize('collision',['source','html','artifact'])
def test_yaml_cannot_overwrite_source_or_standard_artifacts(tmp_path,collision):
    source=tmp_path/'x.csv';source.write_text('x\n1\n2\n');out=tmp_path/'out'
    dest={'source':source,'html':out/'liftoff.html','artifact':out/'liftoff-profile.json'}[collision]
    assert main(['liftoff',str(source),'--out',str(out),'--yaml',str(dest)])==2
    assert source.read_text()=='x\n1\n2\n' and not out.exists()


def test_exclusion_summary_preserves_the_reason_categories():
    ta={'target':'y','excluded':[{'column':'y','reason':'target column'},
        {'column':'human','reason':'excluded by config: exclude_from_target'},
        {'column':'when','reason':'unsupported type pair: temporal × numeric'},
        {'column':'ranked','reason':'pair budget exhausted'},
        {'column':'constant','reason':'constant numeric input'}]}
    text=summary_line({'target_analysis':ta})
    for label,name in [('by config','human'),('unsupported type','when'),('budget','ranked'),('other eligibility','constant')]:assert f'{label}: {name}' in text
    assert 'by config: when' not in text and 'by config: constant' not in text
    assert 'target: not declared' in summary_line({})


def test_yaml_option_remains_socket_free_and_byte_identical(tmp_path):
    source=Path('tests/fixtures/liftoff/clean.csv');out=tmp_path/'out';dest=tmp_path/'config.yaml'
    args=['liftoff',str(source),'--out',str(out),'--yaml',str(dest)]
    runner=Path('tests/offline_runner.py').resolve();seen=[]
    for blocked in ['0','1']:
        r=subprocess.run([sys.executable,str(runner),*args],env={**os.environ,'PYTHONPATH':str(Path('src').resolve()),'FATHOM_DENY_NETWORK':blocked},capture_output=True)
        assert r.returncode==0,r.stderr.decode();seen.append((r.stdout,r.stderr,dest.read_bytes(),{p.name:p.read_bytes() for p in out.iterdir()}))
    assert seen[0]==seen[1]
