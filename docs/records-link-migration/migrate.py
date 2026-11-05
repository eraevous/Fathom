"""Append metadata-only versions; default dry-run, --write appends. No acceptance inferred."""
import copy,json,sys
from pathlib import Path

# Current partial implementation paths, reviewed against the feature specs.
PATHS={
 'FT-R2':['quality.quality_profile'],
 'FT-R3':['profiler.rank_pairs'],
 'FT-R4':['renderers.render_html'],
 'FT-R5':['quality.quality_profile','renderers.render_html'],
 'FT-R6':['renderers.render_html','renderers.render_markdown'],
 'FT-R7':['target.association','target.target_candidates','target.summarize_groups','target.build_target_analysis','target.relationship_chart','target_marks.plot_marks','profiler.rank_pairs'],
 'FT-R9':['univariate.identity_and_samples'],
 'FT-R10':['charts.svg_chart','target.relationship_chart','exports.pdf_bytes','exports.pptx_bytes'],
 'FT-R11':['univariate.identity_and_samples'],
 'FT-R12':['special.infer_special','special.enrich_special'],
 'FT-R13':['exports.export_bundle','exports.pdf_bytes','exports.pptx_bytes'],
 'FT-R14':['parsing.parse_date','parsing.finite_number','univariate.enrich_columns','univariate.numeric_profile','univariate.temporal_profile','univariate.text_profile'],
 'FT-R15':['univariate.numeric_profile','univariate.text_profile','univariate.temporal_profile','univariate.missingness_patterns'],
 'FT-R16':['presentation.column_tables','presentation.html_table','renderers.dictionary_and_provenance_html'],
 'FT-R17':['specs.007-target-analysis.review.capture.capture'],
 'FT-R18':['presentation.column_tables','presentation.formatted_examples','univariate.numeric_profile','univariate.enrich_columns','charts.svg_chart','renderers.dictionary_and_provenance_html','exports.pptx_bytes'],
 'FT-R19':['univariate.numeric_profile','charts.svg_chart','renderers.dictionary_and_provenance_html','exports.pdf_bytes','exports.pptx_bytes'],
}
NOTE='Relation metadata only: prior text, epistemic/authority/tier, anchors and evidence method/limits unchanged; no acceptance or new observation. Implementation paths are partial satisfaction-review bindings, not proof of satisfaction.'
def ref(r):return r['id']+'@'+str(r['version'])
def migrate(raw):
 records=[json.loads(l) for l in raw.splitlines() if l.strip() and not l.startswith('//')]
 latest={r['id']:r for r in records};byref={ref(r):r for r in records}
 # Idempotent on this migration's output; history retains deprecated relations.
 if any(r.get('migration_note')==NOTE for r in latest.values()):return [],{}
 seeds={ref(r) for r in latest.values() if r['id'] in PATHS or any(e['rel']=='implements' or e['rel']=='implemented_by' and r['type']!='requirement' for e in r.get('relations',[]))}
 changed=set(seeds)
 while True:
  extra={ref(r) for r in latest.values() if any(e['rel']!='supersedes' and e['to'] in changed for e in r.get('relations',[]))}
  if extra<=changed:break
  changed|=extra
 mapping={old:byref[old]['id']+'@'+str(byref[old]['version']+1) for old in sorted(changed)}
 appended=[]
 for old in sorted(changed):
  previous=byref[old];r=copy.deepcopy(previous);r['version']+=1;r['migration_note']=NOTE
  relations=[]
  for e in previous.get('relations',[]):
   if e['rel']=='supersedes':continue
   e=copy.deepcopy(e)
   if e['rel']=='implements' or e['rel']=='implemented_by' and previous['type']!='requirement':e['rel']='depends_on'
   e['to']=mapping.get(e['to'],e['to']);relations.append(e)
  for symbol in PATHS.get(r['id'],[]):
   target='code:'+('src.fathom.'+symbol if not symbol.startswith('specs.') else symbol)
   relations.append({'rel':'implemented_by','to':target})
  relations.append({'rel':'supersedes','to':old})
  r['relations']=[dict(pair) for pair in sorted({tuple(sorted(e.items())) for e in relations})]
  appended.append(r)
 return appended,mapping

def main():
 p=Path('.aec/records.jsonl');new,mapping=migrate(p.read_text())
 if not new:
  print('No migration needed; ledger and manifest unchanged.');return
 if '--write' in sys.argv:
  import tempfile
  from aec.records import Store,check
  from aec.edges import snapshot
  with tempfile.NamedTemporaryFile(mode='w+',suffix='.jsonl') as tmp:
   tmp.write(p.read_text()+''.join(json.dumps(r)+'\n' for r in new));tmp.flush()
   errors=[f for f in check(Store.load(tmp.name),snapshot('.')) if f.level=='error']
   if errors:raise ValueError(errors)
  with p.open('a') as f:
   for r in new:f.write(json.dumps(r,ensure_ascii=False)+'\n')
  Path('docs/records-link-migration/versions.json').write_text(json.dumps(mapping,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'new_versions':len(new),'mapping':mapping},indent=2,sort_keys=True))
if __name__=='__main__':main()
