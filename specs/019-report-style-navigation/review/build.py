import json,sys,hashlib
from pathlib import Path
from fathom.connectors import CSVConnector
from fathom.config import load_config
from fathom.profiler import profile
from fathom.models import ProfilingResult
from fathom.renderers import render_html,render_markdown
from fathom.liftoff import build_liftoff,render_liftoff
from fathom.panel import build_panel
from fathom.panel_view import html as panel_html,markdown as panel_md
from fathom.exports import export_bundle
root=Path(__file__).resolve().parents[3];out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
data=CSVConnector(root/'tests/fixtures/liftoff/planted.csv').load()
# Readability fixture reuses authored data, explicit target and hourly structure.
config={'title':'Synthetic payments review','description':'Authored hourly rows: repeated timestamps and cash zeros; no real observations.','target':'amount','columns':{'group':{'type':'categorical'}},'time_series':[{'time':'start','value':'amount','granularities':['hour']}],'pair_budget':4}
r=profile(data,config);b=build_liftoff(data)
panel=build_panel(CSVConnector(root/'tests/fixtures/years/panel.csv').load(),{'series':['entity','candidate'],'time':'year','value':'value','period':'year','date_format':'YEAR'},root)
for name,result,html,md in [('profile',r,render_html(r),render_markdown(r)),('brief',b,render_liftoff(b),None),('panel',panel,panel_html(panel),panel_md(panel))]:
 (out/(name+'.json')).write_text(result.to_json());(out/(name+'.html')).write_text(html)
 if md:(out/(name+'.md')).write_text(md)
files,_=export_bundle(r,['pdf','pptx'])
for name,v in files.items():(out/name).write_bytes(v if isinstance(v,bytes) else v.encode())
(out/'hashes.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.name!='hashes.json'},indent=2,sort_keys=True)+'\n')
