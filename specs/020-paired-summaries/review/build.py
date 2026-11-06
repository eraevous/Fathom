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
(out/'profile.json').write_text(p.to_json());(out/'profile.html').write_text(render_html(p));(out/'profile.md').write_text(render_markdown(p))
files,_=export_bundle(p,['pdf','pptx'])
for name,value in files.items():(out/name).write_bytes(value)
print(hashlib.sha256(p.to_json().encode()).hexdigest())
