"""Re-render the same public-film artifact and compare fresh analysis bytes."""
import json,hashlib
from pathlib import Path
from fathom.connectors import CSVConnector
from fathom.config import load_config
from fathom.profiler import profile
from fathom.models import ProfilingResult
from fathom.renderers import render_html,render_markdown
from fathom.exports import export_bundle
from fathom.tidy import tidy_files

old=Path('/tmp/fix34-before');out=Path('/tmp/fix34-after');out.mkdir(exist_ok=True)
p=profile(CSVConnector(Path('tests/fixtures/polish/movies.csv')).load(),load_config('tests/fixtures/target/movies.yaml'))
assert p.to_json()==(old/'profile.json').read_text()
q=ProfilingResult(json.loads(p.to_json()))
(out/'report.html').write_text(render_html(q));(out/'report.md').write_text(render_markdown(q));(out/'profile.json').write_text(p.to_json())
assert render_html(q)==render_html(q) and render_markdown(q)==render_markdown(q)
# Small authored table checks real optional export and tidy bytes without enormous decks.
r=profile(CSVConnector(Path('tests/fixtures/summary/mixed.csv')).load(),load_config('tests/fixtures/summary/config.yaml'))
def bundle():
 files,status=export_bundle(r,['pdf','pptx'],deck='full')
 assert all(v['status']=='written' for v in status['formats'].values())
 return {'profile.json':r.to_json().encode(),'report.html':render_html(r).encode(),'report.md':render_markdown(r).encode(),**files,**{k:v.encode() for k,v in tidy_files(r.document).items()}}
a,b=bundle(),bundle();assert a==b
identity={'public_films_source':'tests/fixtures/polish/movies.csv (Vega movies, sources.json beside fixture)','public_profile_unchanged':True,'public_profile_sha256':hashlib.sha256(p.to_json().encode()).hexdigest(),'public_html_md_rerun_identical':True,'synthetic_all_extra_rerun_sha256':{k:hashlib.sha256(v).hexdigest() for k,v in a.items()}}
Path(__file__).with_name('identity.json').write_text(json.dumps(identity,indent=2,sort_keys=True)+'\n')
print(json.dumps(identity,indent=2))
