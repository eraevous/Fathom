"""Small authored synthetic panels; fixed seed, no external source or runtime date."""
import csv,json,math,random
from datetime import date,timedelta
from pathlib import Path

root=Path(__file__).parent;rng=random.Random(20261105)
def poisson(mu):
    p=1.0;k=0;limit=math.exp(-mu)
    while p>limit:k+=1;p*=rng.random()
    return k-1
rows=[]
for name,n in [('low_poisson',240),('overdispersed',240),('bursts',240),('closures',84),('missing',84),('regime',120),('weekly',84),('annual_short',365),('annual_long',1096),('exposure',84)]:
    for i in range(n):
        d=date(2018,1,1)+timedelta(days=i);state='observed';exposure=1
        if name=='low_poisson':value=poisson(.4)
        elif name=='overdispersed':value=poisson(rng.gammavariate(.6,4))
        elif name=='bursts':value=20 if rng.random()<.04 else 0
        elif name=='closures':
            state='closed' if d.weekday()==6 else 'observed';exposure=0 if state=='closed' else 1;value=0 if state=='closed' else 2
        elif name=='missing':
            if 30<=i<35:continue
            state='missing' if 10<=i<20 else 'observed';value='' if state=='missing' else 2
        elif name=='regime':value=poisson(1 if i<60 else 8)
        elif name=='weekly':value=[1,2,3,7,14,21,30][d.weekday()]
        elif name.startswith('annual'):value=round(15+12*math.sin(2*math.pi*(d.timetuple().tm_yday-1)/365.25))
        else:exposure=1+i%2;value=exposure*3
        rows.append({'series':name,'time':d.isoformat(),'value':value,'exposure':exposure,'state':state,'cohort':'group_'+str(len(name)%2)})
with (root/'panel.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,['series','time','value','exposure','state','cohort'],lineterminator='\n');w.writeheader();w.writerows(rows)
truth={}
for name in sorted({r['series'] for r in rows}):
    rs=[r for r in rows if r['series']==name];vs=[r['value'] for r in rs if r['state']=='observed']
    truth[name]={'source_rows':len(rs),'observed':len(vs),'zeros':sum(v==0 for v in vs),'closed':sum(r['state']=='closed' for r in rs),'missing':sum(r['state']=='missing' for r in rs),'volume':sum(vs)}
(root/'truth.json').write_text(json.dumps(truth,indent=2,sort_keys=True)+'\n')
# Arbitrary synthetic metric quantities and declared windows; no metric definition/model fitting.
windows=[];metrics=[]
for i,name in enumerate(sorted(truth)):
    for model in ['m_a','m_b']:
        for window,days in [('w_a',42),('w_b',56)]:
            end=date(2018,1,1)+timedelta(days=days-1)
            windows.append({'series':name,'model':model,'window':window,'train_start':'2018-01-01','train_end':end.isoformat(),'eval_start':(end+timedelta(days=1)).isoformat(),'eval_end':(end+timedelta(days=14)).isoformat()})
            for horizon in ['h_a','h_b']:
                metrics.append({'series':name,'model':model,'window':window,'horizon':horizon,'metric_a':i+int(model=='m_b'),'metric_b':10-i+int(window=='w_b'),'metric_c':0})
metrics=[r for r in metrics if not (r['series']=='weekly' and r['model']=='m_b' and r['window']=='w_b')]
metrics.append({'series':'unmatched_synthetic','model':'m_a','window':'w_a','horizon':'h_a','metric_a':1,'metric_b':1,'metric_c':0})
for name,rs in [('windows.csv',windows),('metrics.csv',metrics)]:
    with (root/name).open('w',newline='') as f:
        w=csv.DictWriter(f,list(rs[0]),lineterminator='\n');w.writeheader();w.writerows(rs)
