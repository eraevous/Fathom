"""Deterministic, stdlib-only scalar CSV views of a saved profile artifact."""
import csv
import io
import json
import math
import statistics


def key(value):return str(value).replace('~','~0').replace('/','~1').replace('.','~2')


def flatten(value,prefix=''):
    out={}
    if isinstance(value,dict) and value:
        for k,v in sorted(value.items()):out.update(flatten(v,prefix+('.' if prefix else '')+key(k)))
    elif isinstance(value,list) and value:
        for i,v in enumerate(value):out.update(flatten(v,prefix+('.' if prefix else '')+str(i)))
    else:out[prefix]=value
    return out


def scalar(value):
    if value is None:return ''
    if isinstance(value,bool):return 'true' if value else 'false'
    if isinstance(value,(dict,list)):return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'))
    if isinstance(value,float) and not math.isfinite(value):raise ValueError('tidy values must be finite')
    return str(value)


def csv_text(rows,first,extras=()):
    headers=list(first)+sorted({k for row in rows for k in row}-set(first)|set(extras))
    out=io.StringIO(newline='');writer=csv.DictWriter(out,fieldnames=headers,lineterminator='\n');writer.writeheader()
    for row in rows:writer.writerow({k:scalar(v) for k,v in row.items()})
    return out.getvalue()


def unit_for(path,column):
    leaf=path.rsplit('.',1)[-1]
    if '.length.' in path:return 'characters'
    if leaf=='span_days':return 'days'
    if leaf in {'count','valid','invalid','finite','missing','distinct','zeros','negatives','raw_lexemes'} or path in {'count','missing','distinct'}:return 'count'
    if leaf in {'share','missing_share','coverage'}:return 'proportion'
    if any(x in path for x in ['entropy','skew','kurtosis','correlation']):return 'bits' if 'entropy' in path else ''
    if leaf in {'mean','median','population_std','min','max','iqr'} or '.percentiles.' in path:
        unit=column.get('univariate',{}).get('units') or {}
        return unit.get('value','') if isinstance(unit,dict) else str(unit)
    return ''


def tidy_files(d):
    if d.get('kind')!='profile':raise ValueError('tidy export requires a profile artifact; panel has its existing CSV export')
    cols=[]
    for c in d['columns']:
        metrics={k:c[k] for k in ['count','missing','distinct']}
        for label,value in [('statistics',c.get('statistics',{})),('univariate.statistics',c.get('univariate',{}).get('statistics',{})),('special',c.get('special',{}))]:
            metrics.update(flatten(value,label))
        for path,v in metrics.items():
            cols.append({'column':c['name'],'effective_type':c['effective_type'],'metric':path,'value':v,'value_type':'null' if v is None else 'boolean' if isinstance(v,bool) else 'number' if isinstance(v,(int,float)) else 'object' if isinstance(v,dict) else 'array' if isinstance(v,list) else 'string','unit':unit_for(path,c)})
    findings=[]
    collections=[('findings',d.get('findings',[]))]
    lift=d.get('liftoff',{})
    if lift:
        collections.append(('liftoff.automated_findings',lift.get('automated_findings',[])))
        for kind in ['intervals','time_series']:
            for i,p in enumerate(lift.get('previews',{}).get(kind,[])):collections.append((f'liftoff.previews.{kind}.{i}.findings',p.get('findings',[])))
    for collection,items in collections:
        for f in items:
            row={'collection':collection,**{k:f.get(k) for k in ['id','kind','message','generator','uncertainty']}}
            row.update({k:v for k,v in flatten(f).items() if k not in row});findings.append(row)
    relations=[flatten(pair) for pair in d.get('bivariate',[])]
    files={'columns.csv':csv_text(cols,['column','effective_type','metric','value','value_type','unit']),
           'findings.csv':csv_text(findings,['collection','id','kind','message','generator','uncertainty']),
           'relations.csv':csv_text(relations,['left','right','method','semantics','generator','uncertainty'])}
    samples=d.get('samples')
    if samples is not None:
        rows=[]
        for kind in ['first','last','random']:
            for row in samples[kind]:rows.append({'sample':kind,'position':row['position'],'seed':samples['seed'],**{'value.'+key(name):v for name,v in zip(samples['columns'],row['values'])}})
        files['samples.csv']=csv_text(rows,['sample','position','seed'],['value.'+key(n) for n in samples['columns']])
    return files


def nesting_metrics(d,limit=20):
    leaves=[];keys={}
    def walk(value,path,depth,local):
        if isinstance(value,dict) and value:
            for k,v in sorted(value.items()):walk(v,path+'/'+str(k).replace('~','~0').replace('/','~1'),depth+1,local)
        elif isinstance(value,list) and value:
            for i,v in enumerate(value):walk(v,path+'/'+str(i),depth+1,local)
        else:local.append(depth);leaves.append((path,depth+1))
    for k,v in sorted(d.items()):
        local=[];walk(v,'/'+k.replace('~','~0').replace('/','~1'),0,local)
        keys[k]={'max_depth':max(local),'median_depth':statistics.median(local),'terminals':len(local)}
    deepest=max((depth for _,depth in leaves),default=0);paths=sorted(p for p,depth in leaves if depth==deepest)
    return {'definition':'Depth is container-edge count below each top-level value; scalar/empty container depth0; arrays count one edge per index. Global depth includes the top-level edge. Median over all terminal leaves.','keys':keys,'max_root_depth':deepest,'deepest_paths':paths[:limit],'omitted_deepest_paths':max(0,len(paths)-limit)}
