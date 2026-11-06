"""Fresh-process denied-network commands, byte-identical across two hash seeds."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
root=Path('/tmp/time22-identity');cfg=Path('/tmp/time22-review.yaml')
cfg.write_text('columns:\n  clock: {type: temporal, date_format: TIME}\n  stamp: {type: temporal, date_format: DATETIME}\n  custom: {type: temporal, date_format: "%d/%m/%Y %H:%M"}\n')
commands=[['profile','tests/fixtures/temporal/clocks.csv','--config',str(cfg),'--out',str(root/'profile')],['configure','tests/fixtures/temporal/clocks.csv','--config',str(cfg),'--out',str(root/'configure')],['liftoff','tests/fixtures/temporal/clocks.csv','--out',str(root/'liftoff')],['export',str(root/'profile/guide-profile.json'),'--out',str(root/'exports')]]
first=None
for seed in ['1','99']:
 for args in commands:
  r=subprocess.run([sys.executable,'tests/offline_runner.py',*args],env={**os.environ,'FATHOM_DENY_NETWORK':'1','PYTHONHASHSEED':seed,'PYTHONPATH':'src'},capture_output=True)
  assert r.returncode==0,(args,r.stderr.decode())
 files={str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
 if first is None:first=files
 else:assert first==files
Path(__file__).with_name('identity.json').write_text(json.dumps({'commands':commands,'blocked_network':True,'hash_seeds':[1,99],'file_sha256':{k:hashlib.sha256(v).hexdigest() for k,v in files.items()}},sort_keys=True,indent=2)+'\n')
print(len(files),'files match, denied networking')
