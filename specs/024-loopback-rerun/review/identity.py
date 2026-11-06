"""Cross-hash-seed real-session report identity against ordinary blocked CLI."""
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import http.client
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[3]
OUT=Path('/tmp/fathom-serve24-identity');OUT.mkdir(exist_ok=True)
DATA=Path(__file__).parent/'synthetic.csv'
base={**os.environ,'PYTHONPATH':str(ROOT/'src'),'FATHOM_DENY_NETWORK':'1'}
hashes=[]
for seed in ['1','73']:
 env={**base,'FATHOM_ALLOW_LOOPBACK':'1','PYTHONHASHSEED':seed}
 process=subprocess.Popen([sys.executable,'-u',str(ROOT/'tests/offline_runner.py'),'serve',str(DATA),'--out',str(OUT),'--idle-timeout','60'],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 try:
  assert select.select([process.stdout],[],[],15)[0]
  u=urlsplit(process.stdout.readline().strip());assert u.hostname=='127.0.0.1'
  def post(route,body):
   c=http.client.HTTPConnection(u.netloc,timeout=10);c.request('POST',route+'?'+u.query,body=body,headers={'Origin':'http://'+u.netloc,'Content-Type':'application/yaml'});r=c.getresponse();b=r.read();assert r.status==200;c.close()
  post('/rerun',b'pair_budget: 0\n')
  files={n:(OUT/n).read_bytes() for n in ['report.html','report.md','guide-profile.json']}
  hashes.append({n:hashlib.sha256(b).hexdigest() for n,b in files.items()})
  post('/stop',b'');process.wait(timeout=5);assert process.returncode==0,process.stderr.read()
 finally:
  if process.poll() is None:process.terminate();process.wait(timeout=5)
 cli=OUT/'ordinary'
 r=subprocess.run([sys.executable,str(ROOT/'tests/offline_runner.py'),'profile',str(DATA),'--out',str(cli),'--config',str(OUT/'server-config.yaml')],env={**base,'FATHOM_ALLOW_LOOPBACK':'0','PYTHONHASHSEED':seed},capture_output=True)
 assert r.returncode==0,r.stderr.decode()
 assert files=={n:(cli/n).read_bytes() for n in files}
assert hashes[0]==hashes[1]
(Path(__file__).parent/'identity.json').write_text(json.dumps({'hash_seeds':[1,73],'server_matches_cli':True,'outbound_attempts':0,'sha256':hashes[0]},sort_keys=True,indent=2)+'\n')
