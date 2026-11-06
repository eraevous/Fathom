"""Build synthetic card/reports via normal commands under independent socket denial."""
import json
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[3]
OUT=Path('/tmp/fathom-clock25');OUT.mkdir(exist_ok=True)
FIX=ROOT/'tests/fixtures/time_definition/clocks.csv'
commands=[['profile',str(FIX),'--out',str(OUT/'profile')],['profile',str(FIX),'--config',str(FIX.with_name('frames.yaml')),'--out',str(OUT/'frames')],['configure',str(FIX),'--out',str(OUT/'configure')],['liftoff',str(FIX),'--out',str(OUT/'liftoff')],['export',str(OUT/'frames/guide-profile.json'),'--out',str(OUT/'exports')]]
prior=None
for seed in ['1','73']:
 env={**os.environ,'PYTHONPATH':str(ROOT/'src'),'FATHOM_DENY_NETWORK':'1','PYTHONHASHSEED':seed}
 for args in commands:
  r=subprocess.run([sys.executable,str(ROOT/'tests/offline_runner.py'),*args],env=env,capture_output=True)
  assert r.returncode==0,r.stderr.decode()
 current={str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.rglob('*') if p.is_file()}
 if prior is not None:assert prior==current
 prior=current
(Path(__file__).parent/'identity.json').write_text(json.dumps({'hash_seeds':[1,73],'socket_attempts':0,'identical_files':prior},sort_keys=True,indent=2)+'\n')
