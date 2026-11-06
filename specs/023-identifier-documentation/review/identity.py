"""Repeated blocked-network commands, preserving identifier lexemes in all artifacts."""
from pathlib import Path
import os,sys,json,subprocess,hashlib
root=Path('/tmp/id23-identity')
commands=[['profile','tests/fixtures/identifiers/keys.csv','--config','tests/fixtures/identifiers/config.yaml','--out',str(root/'profile')],['configure','tests/fixtures/identifiers/keys.csv','--out',str(root/'configure')],['panel','tests/fixtures/panel/panel.csv','--config','tests/fixtures/panel/joined.yaml','--out',str(root/'panel')],['export',str(root/'profile/guide-profile.json'),'--out',str(root/'exports')]]
first=None
for seed in ['1','73']:
 for args in commands:
  r=subprocess.run([sys.executable,'tests/offline_runner.py',*args],env={**os.environ,'PYTHONHASHSEED':seed,'FATHOM_DENY_NETWORK':'1','PYTHONPATH':'src'},capture_output=True)
  assert r.returncode==0,(args,r.stderr.decode())
 files={str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
 if first is None:first=files
 else:assert first==files
Path(__file__).with_name('identity.json').write_text(json.dumps({'blocked_network':True,'hash_seeds':[1,73],'file_sha256':{k:hashlib.sha256(v).hexdigest() for k,v in files.items()}},sort_keys=True,indent=2)+'\n')
print(len(files),'files identical under networking denial')
