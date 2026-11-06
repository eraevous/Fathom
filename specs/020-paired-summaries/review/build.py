"""Deterministic synthetic review outputs; use parent/new PYTHONPATH for baseline."""
import sys,json,hashlib
from pathlib import Path
from fathom.connectors import CSVConnector
from fathom.config import load_config
from fathom.profiler import profile
from fathom.renderers import render_html,render_markdown
from fathom.exports import export_bundle

root=Path(__file__).resolve().parents[3];fixture=root/'tests/fixtures/summary'
p=profile(CSVConnector(fixture/'mixed.csv').load(),load_config(fixture/'config.yaml'))
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
baseline='--baseline' in sys.argv
opts={'summary_orientation':sys.argv[2]} if len(sys.argv)>2 and not baseline else None
(out/'profile.json').write_text(p.to_json());(out/'profile.html').write_text(render_html(p) if baseline else render_html(p,report=opts));(out/'profile.md').write_text(render_markdown(p) if baseline else render_markdown(p,report=opts))
files,_=export_bundle(p,['pdf','pptx']) if baseline else export_bundle(p,['pdf','pptx'],report=opts)
for name,value in files.items():(out/name).write_bytes(value)
print(hashlib.sha256(p.to_json().encode()).hexdigest())

if not baseline:
 from fathom.tidy import tidy_files
 for name,value in tidy_files(p.document).items():(out/name).write_text(value)
