"""Follow-up to migrate.py after merging main (#19-#21) into the #16/#18 line.

Records appended on main after the #18 migration still use the old convention (a claim
`implements` its requirement and carries `implemented_by code:`). This appends
relation-only versions in the #18 convention: `implements` becomes `depends_on`, a claim's
code bindings become `depends_on`, and the requirement the claim served gains those
bindings as `implemented_by`, so code-impact reaches the governing obligation.
Default dry-run; --write appends. No acceptance inferred."""
import copy,json,sys
from pathlib import Path

NOTE=('Relation metadata only (post-merge follow-up to the records-link migration): prior text, epistemic/authority/tier, '
      'anchors and evidence method/limits unchanged; no acceptance or new observation. Implementation paths are the '
      "claim's own code bindings moved to the requirement it served, not proof of satisfaction.")
def ref(r):return r['id']+'@'+str(r['version'])
def old_style(r):return any(e['rel']=='implements' or e['rel']=='implemented_by' and r['type']!='requirement' for e in r.get('relations',[]))
def followup(raw):
 records=[json.loads(l) for l in raw.splitlines() if l.strip() and not l.startswith('//')]
 latest={r['id']:r for r in records};byref={ref(r):r for r in records}
 seeds={ref(r) for r in latest.values() if old_style(r)}
 if not seeds:return [],{}
 # requirement id -> code bindings of the claims that implemented it
 code={}
 for r in latest.values():
  if r['type']=='requirement' or not old_style(r):continue
  served=[byref[e['to']]['id'] for e in r['relations'] if e['rel']=='implements' and e['to'] in byref and byref[e['to']]['type']=='requirement']
  for rid in served:
   code.setdefault(rid,[]).extend(e['to'] for e in r['relations'] if e['rel']=='implemented_by' and e['to'].startswith('code:'))
 changed=set(seeds)|{ref(latest[rid]) for rid in code}
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
  for target in code.get(r['id'],[]):relations.append({'rel':'implemented_by','to':target})
  relations.append({'rel':'supersedes','to':old})
  r['relations']=[dict(pair) for pair in sorted({tuple(sorted(e.items())) for e in relations})]
  appended.append(r)
 return appended,mapping

def main():
 p=Path('.aec/records.jsonl');new,mapping=followup(p.read_text())
 if not new:
  print('No follow-up needed; ledger unchanged.');return
 if '--write' in sys.argv:
  with p.open('a') as f:
   f.write('// 2026-11-05: records-link follow-up after merging main (#19-#21) into #16 (claude:dg#reconcile); relation metadata only.\n')
   for r in new:f.write(json.dumps(r,ensure_ascii=False)+'\n')
 print(json.dumps({'new_versions':len(new),'mapping':mapping},indent=2,sort_keys=True))
if __name__=='__main__':main()
