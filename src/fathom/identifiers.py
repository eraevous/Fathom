"""Exact lexical key documentation. Repetition and label gaps do not establish meaning."""
from collections import Counter
from decimal import Decimal,InvalidOperation
from itertools import groupby
import re

LIMIT=10
NUMERIC=re.compile(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?')


def is_identifier(column):return column.get('univariate',{}).get('role')=='identifier'


def identifier_reason(column):
    declared=column.get('univariate',{}).get('role_basis','').startswith('human')
    return ('excluded by config: ' if declared else 'inferred ')+'identifier role; excluded from target ranking'


def signature(value):
    def kind(c):return 'D' if c.isdecimal() else 'U' if c.isupper() else 'L' if c.islower() else 'A' if c.isalpha() else 'W' if c.isspace() else repr(c)
    return ' '.join(k+'{'+str(len(list(g)))+'}' for k,g in groupby(map(kind,value))) or '[empty]'


def numeric_reading(values):
    basis='exact numeric labels in input-row order, missing omitted; raw key identity is unchanged'
    unavailable={'status':'not computed','basis':basis,'reason':'not all populated labels are plain finite numeric strings (or magnitude exceeds1000digits)'}
    if not values:return {**unavailable,'reason':'no populated values'}
    if any(not NUMERIC.fullmatch(v.strip()) for v in values):return unavailable
    try:nums=[Decimal(v.strip()) for v in values]
    except InvalidOperation:return unavailable
    if any(not v.is_finite() or abs(v.adjusted())>1000 for v in nums if v):return unavailable
    signs={0 if b==a else 1 if b>a else -1 for a,b in zip(nums,nums[1:])}
    order='insufficient values' if len(nums)<2 else 'constant' if signs=={0} else 'strictly increasing' if signs=={1} else 'strictly decreasing' if signs=={-1} else 'nondecreasing' if signs<={0,1} else 'nonincreasing' if signs<={-1,0} else 'mixed'
    integral=all(v==v.to_integral_value() for v in nums);gaps=[];count=0
    if integral:
        ints=sorted({int(v) for v in nums})
        for a,b in zip(ints,ints[1:]):
            if b-a>1:gaps.append({'from':str(a+1),'to':str(b-1),'count':b-a-1});count+=b-a-1
    return {'status':'computed','basis':basis,'order':order,'numeric_distinct':len(set(nums)),'raw_distinct':len(set(values)),
            'integer_labels':integral,'missing_integer_labels':count if integral else None,'gap_range_count':len(gaps),'gaps':gaps[:LIMIT],'omitted_gap_ranges':max(0,len(gaps)-LIMIT),
            'gap_basis':'unobserved integer labels strictly between sorted observed labels; not a claim of missing records' if integral else 'consecutive integer gaps not defined for fractional labels'}


def identifier_profile(values,basis):
    populated=[v for v in values if v is not None];counts=Counter(populated);duplicates=[]
    repeats=[(v,n) for v,n in counts.items() if n>1]
    for v,n in sorted(repeats,key=lambda p:(-p[1],p[0]))[:LIMIT]:
        positions=[i+1 for i,x in enumerate(values) if x==v]
        duplicates.append({'value':v,'count':n,'positions':positions[:LIMIT],'omitted_positions':max(0,len(positions)-LIMIT)})
    lengths=Counter(map(len,populated));patterns=Counter(map(signature,populated));leading=[v for v in populated if re.fullmatch(r'[+-]?0[0-9]+',v.strip())]
    n=len(populated)
    return {'basis':basis,'rows':len(values),'nonmissing':n,'missing':len(values)-n,'distinct':len(counts),
            'unique_nonmissing':len(counts)==n if n else None,'unique_per_row':len(counts)==n==len(values) if n else None,
            'duplicate_values':len(repeats),'duplicate_rows':sum(n-1 for _,n in repeats),'rows_in_repeated_values':sum(n for _,n in repeats),
            'duplicates':duplicates,'omitted_duplicate_values':max(0,len(repeats)-LIMIT),'example_limit':LIMIT,'position_basis':'1-based data rows, header excluded',
            'length':{'min':min(lengths) if lengths else None,'max':max(lengths) if lengths else None,'distinct_lengths':len(lengths)},
            'patterns':[{'pattern':p,'count':n} for p,n in sorted(patterns.items(),key=lambda p:(-p[1],p[0]))[:LIMIT]],'pattern_count':len(patterns),'omitted_patterns':max(0,len(patterns)-LIMIT),
            'pattern_basis':'run-length Unicode digit(D), upper(U), lower(L), other letter(A), whitespace(W), literal punctuation; descriptive, no validity rule',
            'leading_zeros':{'count':len(leading),'examples':list(dict.fromkeys(leading))[:LIMIT],'basis':'signed/unsigned integer lexeme with a zero before further digits; raw strings preserved'},
            'numeric':numeric_reading(populated)}


def enrich_identifiers(columns,rows,emit):
    for i,c in enumerate(columns):
        if not is_identifier(c):continue
        stats=identifier_profile([r[i] for r in rows],c['univariate'].get('role_basis','unknown'))
        c['identifier']=stats
        status='unique per row' if stats['unique_per_row'] else 'unique among populated values; incomplete row key' if stats['unique_nonmissing'] else 'repeats' if stats['duplicate_rows'] else 'insufficient populated values'
        emit('identifier-'+str(i),'observation',f"{c['name']}: {status}; {stats['missing']} missing; {stats['duplicate_rows']} rows repeat an earlier raw identifier. Role basis: {stats['basis']}.",
             [{'path':f'columns.{i}.identifier','value':stats}], 'Uniqueness/repetition describes this snapshot, not entity meaning or a valid key constraint.','rule:identifier-v1',rule='identifier_structure',columns=[c['name']])


def validate_identifier(s):
    def count(v):return type(v) is int and v>=0
    if not isinstance(s,dict) or any(not isinstance(s.get(k),str) for k in ['basis','position_basis','pattern_basis']):raise ValueError('invalid identifier metadata')
    for k in ['rows','nonmissing','missing','distinct','duplicate_values','duplicate_rows','rows_in_repeated_values','omitted_duplicate_values','example_limit','pattern_count','omitted_patterns']:
        if not count(s.get(k)):raise ValueError('invalid identifier count: '+k)
    if s['nonmissing']+s['missing']!=s['rows'] or s['distinct']>s['nonmissing'] or s['duplicate_rows']!=s['nonmissing']-s['distinct']:raise ValueError('inconsistent identifier counts')
    for k in ['unique_nonmissing','unique_per_row']:
        if s.get(k) is not None and type(s[k]) is not bool:raise ValueError('invalid identifier uniqueness')
    if not isinstance(s.get('duplicates'),list) or not isinstance(s.get('patterns'),list):raise ValueError('invalid identifier examples')
    for x in s['duplicates']:
        if not isinstance(x,dict) or not isinstance(x.get('value'),str) or not count(x.get('count')) or not count(x.get('omitted_positions')) or not isinstance(x.get('positions'),list) or any(type(p) is not int or p<1 for p in x['positions']):raise ValueError('invalid identifier duplicate')
    for x in s['patterns']:
        if not isinstance(x,dict) or not isinstance(x.get('pattern'),str) or not count(x.get('count')):raise ValueError('invalid identifier pattern')
    for key in ['length','leading_zeros','numeric']:
        if not isinstance(s.get(key),dict):raise ValueError('invalid identifier '+key)
    length=s['length'];leading=s['leading_zeros'];n=s['numeric']
    if any(length.get(k) is not None and not count(length[k]) for k in ['min','max']) or not count(length.get('distinct_lengths')):raise ValueError('invalid identifier length')
    if not count(leading.get('count')) or not isinstance(leading.get('basis'),str) or not isinstance(leading.get('examples'),list) or any(not isinstance(x,str) for x in leading['examples']):raise ValueError('invalid identifier leading zeros')
    if n.get('status') not in {'computed','not computed'} or not isinstance(n.get('basis'),str):raise ValueError('invalid identifier numeric status')
    if n['status']=='not computed':
        if not isinstance(n.get('reason'),str):raise ValueError('invalid identifier numeric reason')
    else:
        if n.get('order') not in {'insufficient values','constant','strictly increasing','strictly decreasing','nondecreasing','nonincreasing','mixed'} or type(n.get('integer_labels')) is not bool:raise ValueError('invalid identifier numeric ordering')
        if any(not count(n.get(k)) for k in ['numeric_distinct','raw_distinct','gap_range_count','omitted_gap_ranges']) or n.get('missing_integer_labels') is not None and not count(n['missing_integer_labels']) or not isinstance(n.get('gap_basis'),str):raise ValueError('invalid identifier numeric count')
        if not isinstance(n.get('gaps'),list) or any(not isinstance(g,dict) or any(not isinstance(g.get(k),str) for k in ['from','to']) or not count(g.get('count')) for g in n['gaps']):raise ValueError('invalid identifier gaps')
