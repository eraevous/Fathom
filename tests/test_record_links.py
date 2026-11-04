"""Ledger semantics plus optional pinned-AEC diagnostics; application has no AEC dependency."""
import copy,hashlib,json,runpy
from pathlib import Path
import pytest

ROOT=Path(__file__).parents[1]
DOC=ROOT/'docs/records-link-migration'
AUDIT=json.loads((DOC/'audit.json').read_text())
HELPER=runpy.run_path(str(DOC/'migrate.py'))

def records(raw):return [json.loads(l) for l in raw.splitlines() if l.strip() and not l.startswith('//')]
def latest(rs):return {r['id']:r for r in rs}
def ref(r):return r['id']+'@'+str(r['version'])
def before():return (ROOT/'.aec/records.jsonl').read_bytes()[:AUDIT['original_prefix_bytes']]

def test_migration_is_append_only_and_preserves_assertions():
    assert hashlib.sha256(before()).hexdigest()==AUDIT['original_prefix_sha256']
    old={ref(r):r for r in records(before().decode())};now={ref(r):r for r in records((ROOT/'.aec/records.jsonl').read_text())}
    assert all(now[k]==v for k,v in old.items())
    mapping=json.loads((DOC/'versions.json').read_text());assert len(mapping)==67
    for a,b in mapping.items():
        previous,current=old[a],now[b]
        assert {k:v for k,v in current.items() if k not in ('version','relations','migration_note')}=={k:v for k,v in previous.items() if k not in ('version','relations')}
        assert {'rel':'supersedes','to':a} in current['relations']
        assert current['version']==previous['version']+1
    # All original historical contract pins with different wording stay pinned.
    assert {'rel':'depends_on','to':'FT-R6@2'} in now['FT-DQ-C1@2']['relations']


def test_latest_relation_directions_and_support_lineage():
    current=latest(records((ROOT/'.aec/records.jsonl').read_text()))
    assert not any(e['rel']=='implements' for r in current.values() for e in r.get('relations',[]))
    for r in current.values():
        for e in r.get('relations',[]):
            if e['rel']=='implemented_by':assert r['type']=='requirement' and e['to'].startswith('code:')
        if r['type']=='claim':
            assert any(e['rel']=='depends_on' for e in r['relations'])
            assert any(e['rel']=='supports' and e['to']==ref(r) for evidence in current.values() for e in evidence.get('relations',[])), ref(r)
    assert current['FT-R8']['version']==1  # Unbuilt axis switching gets no invented implementation.
    assert current['FT-SD-Q1']['status']==current['FT-SD-Q2']['status']=='proposed'


def test_migration_is_deterministic_and_idempotent():
    original=before().decode();a,m=HELPER['migrate'](original);b,n=HELPER['migrate'](original)
    assert a==b and m==n
    data=original+''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in a)
    assert data==(ROOT/'.aec/records.jsonl').read_text()
    assert HELPER['migrate'](data)==([],{})
    for name,sha in AUDIT['snapshot_sha256'].items():assert hashlib.sha256((DOC/'snapshots'/name).read_bytes()).hexdigest()==sha


def impact(rs):
    pytest.importorskip('aec')
    from aec.records import Record,Store
    from aec.edges import loads
    from aec.code_impact import code_impact
    from aec.impact import render
    known={'id','version','type','text','subject','relations'}
    store=Store([Record(id=r['id'],version=r['version'],type=r['type'],text=r.get('text',''),subject=r.get('subject'),relations=r.get('relations',[]),data={k:v for k,v in r.items() if k not in known}) for r in rs])
    report,events=code_impact(store,loads((DOC/'snapshots/base.edges.jsonl').read_text()),loads((DOC/'snapshots/head.edges.jsonl').read_text()))
    text=f'# derived {len(events)} change event(s) from the structural diff\n'+render(store,report)+'\n'
    return report,text


def test_pinned_impact_reaches_obligations_after_migration():
    old,old_text=impact(records(before().decode()));new,new_text=impact(records((ROOT/'.aec/records.jsonl').read_text()))
    assert old_text==(DOC/'before.md').read_text() and new_text==(DOC/'after.md').read_text()
    assert not {'FT-R7@2','FT-R18@1'} & old.impacts.keys()
    assert {'FT-R7@3','FT-R18@2'}<=new.impacts.keys()
    assert len(old.impacts)==28 and len(new.impacts)==42


def test_link_ablation_decoy_loses_governing_reach():
    rs=copy.deepcopy(records((ROOT/'.aec/records.jsonl').read_text()));curr=latest(rs)
    for rid in HELPER['PATHS']:
        curr[rid]['relations']=[e for e in curr[rid]['relations'] if e['rel']!='implemented_by']
    report,text=impact(rs)
    assert not {'FT-R7@3','FT-R18@2'} & report.impacts.keys()
    assert 'FT-TA-R1@3' in report.impacts
    assert text==(DOC/'ablated.md').read_text() and len(report.impacts)==30
