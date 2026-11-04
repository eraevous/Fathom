"""Verify authored fixture truth only; deliberately does not implement the proposed checks."""
import csv,json
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).parent/'fixtures'
def rows(name):
 with (ROOT/(name+'.csv')).open() as f:return list(csv.DictReader(f))
def main():
 out={}
 for suffix in ('','-clean'):
  empty=rows('empty-values'+suffix)
  blank=[i+1 for i,r in enumerate(empty) if all(not r[y].strip() for y in ('2010','2011','2012'))]
  assert len(blank)==(0 if suffix else 9)
  assert all(r['entity'] and r['indicator'] for r in empty)
  out['empty-values'+suffix]={'rows':len(empty),'blank_value_rows':blank}
  mixed=rows('mixed-units'+suffix)
  matches=[r['entity'] for r in mixed if r['entity'] in ['East Asia & Pacific','Europe & Central Asia','Latin America & Caribbean','Middle East & North Africa','Sub-Saharan Africa']]
  assert len(matches)==(0 if suffix else 5)
  out['mixed-units'+suffix]={'rows':len(mixed),'cue_labels':matches}
  groups=defaultdict(list)
  for r in rows('repeated-key'+suffix):groups[r['individual']].append(r)
  sizes=Counter(len(g) for g in groups.values());assert sizes==({1:840} if suffix else {4:210})
  if not suffix:
   assert all(len({r[c] for r in g})==1 for g in groups.values() for c in ('hinc','psize'))
   assert all(sum(int(r['choice']) for r in g)==1 for g in groups.values())
   assert all(len({g[0][c] for g in groups.values()})>1 for c in ('hinc','psize'))
  out['repeated-key'+suffix]={'groups':len(groups),'size_distribution':dict(sizes)}
  zs=rows('zero-concentration'+suffix);zeros=Counter(r['mode'] for r in zs if float(r['ttme'])==0)
  assert sum(zeros.values())==210
  assert zeros==({'1':53,'2':53,'3':52,'4':52} if suffix else {'4':210})
  out['zero-concentration'+suffix]={'rows':len(zs),'zero_counts':dict(zeros),'rows_per_mode':dict(Counter(r['mode'] for r in zs))}
 result=json.dumps(out,indent=2,sort_keys=True)+'\n'
 assert result==(ROOT/'truth.json').read_text(), 'Fixture truth manifest mismatch'
 print('Eight fixture/decoy tables match truth.json; no application behavior claimed.')
if __name__=='__main__':main()
