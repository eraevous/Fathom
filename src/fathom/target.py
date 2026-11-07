"""Light target-column evidence; detailed groups and plots stay inside pair budget."""

from collections import Counter, defaultdict
import math
import statistics

from .parsing import finite_number
from .quality import copy_evidence
from .univariate import percentile, safe, coefficient
from .presentation import formatted

NUMERIC={'numeric','latitude','longitude'}
CATEGORY={'categorical','boolean'}
WARNING='Descriptive complete-case association, not causation. Types/meanings may be inferred. Unlike measures are priority heuristics, not interchangeable effect sizes; sparse/small groups can inflate apparent association. Unmarked leakage cannot be inferred reliably from correlation.'


def cell(value,typ):
    if value is None:return None
    if typ in NUMERIC:return finite_number(value)
    if typ=='boolean':return value.casefold() if value.casefold() in {'true','false'} else None
    return value


def association(a,b,cases):
    if len(cases)<2:return None
    xs,ys=zip(*cases)
    if len(set(xs))<2 or len(set(ys))<2:return None
    if a in NUMERIC and b in NUMERIC:
        sx=max(abs(x) for x in xs) or 1;sy=max(abs(y) for y in ys) or 1
        try:value=statistics.correlation([x/sx for x in xs],[y/sy for y in ys])
        except (ArithmeticError,statistics.StatisticsError):return None
        return {'measure':'Pearson r','value':coefficient(value),'strength':coefficient(abs(value))}
    if (a in CATEGORY and b in NUMERIC) or (b in CATEGORY and a in NUMERIC):
        groups=defaultdict(list);pairs=cases if a in CATEGORY else [(y,x) for x,y in cases]
        scale=max(abs(v) for _,v in pairs) or 1
        for g,v in pairs:groups[g].append(v/scale)
        nums=[v for group in groups.values() for v in group];mean=statistics.mean(nums)
        total=math.fsum((v-mean)**2 for v in nums)
        between=math.fsum(len(v)*(statistics.mean(v)-mean)**2 for v in groups.values())
        value=math.sqrt(min(1,max(0,between/total))) if total else None
        return {'measure':'Correlation ratio eta','value':coefficient(value),'strength':coefficient(value)} if value is not None else None
    if a in CATEGORY and b in CATEGORY:
        cx,cy=Counter(xs),Counter(ys);counts=Counter(cases);n=len(cases)
        chi=math.fsum((counts[x,y]-cx[x]*cy[y]/n)**2/(cx[x]*cy[y]/n) for x in cx for y in cy)
        value=math.sqrt(min(1,max(0,chi/n/min(len(cx)-1,len(cy)-1))))
        return {'measure':"Cramer's V",'value':coefficient(value),'strength':coefficient(value)}
    return None


def target_candidates(rows,columns,cfg,quality):
    target=cfg['target'];ti=next(i for i,c in enumerate(columns) if c['name']==target);tc=columns[ti];b=tc['effective_type']
    selection={'target':target,'budget':cfg['pair_budget'],'selected':[],'excluded':[]};pairs=[]
    from .identifiers import is_identifier,identifier_reason
    target_identifier=is_identifier(tc)
    blocked=quality.get('value_exclusions',{});target_excluded=cfg['columns'].get(target,{}).get('exclude_from_target',False)
    for i,c in enumerate(columns):
        a=c['effective_type'];name=c['name'];values=[cell(r[i],a) for r in rows];tv=[cell(r[ti],b) for r in rows]
        cases=[(x,y) for x,y in zip(values,tv) if x is not None and y is not None]
        nonmissing=[v for v in values if v is not None];reason=None
        if is_identifier(c):reason=identifier_reason(c)
        elif target_identifier:reason=('target excluded by config: ' if tc.get('univariate',{}).get('role_basis','').startswith('human') else 'target inferred as ')+'identifier role; association ranking not performed'
        elif i==ti:reason='target column'
        elif target_excluded:reason='target excluded by config'
        elif cfg['columns'].get(name,{}).get('exclude_from_target'):reason='excluded by config: exclude_from_target'
        elif a=='temporal' and c['statistics'].get('parse_failure'):
            from .parsing import temporal_failure_message
            reason=temporal_failure_message(name,c['statistics']['parse_failure'])
        elif copy_evidence([r[i] for r in rows],[r[ti] for r in rows])['near']:reason='near-duplicate of target (row agreement >=95%)'
        elif name in blocked:reason='constant numeric input' if blocked[name]=='constant column' and a in NUMERIC else blocked[name]
        elif (a in CATEGORY and len(set(nonmissing))>20) or (b in CATEGORY and len(set(v for v in tv if v is not None))>20):reason='more than twenty groups; summary omitted'
        elif c.get('univariate',{}).get('role')=='identifier':reason='identifier-like column'
        elif a not in NUMERIC and a!='temporal' and len(nonmissing)>=5 and len(set(nonmissing))/len(nonmissing)>=.9:reason='near-unique identifier-like category/text (>=90% distinct)'
        elif not ((a in NUMERIC|CATEGORY) and (b in NUMERIC|CATEGORY)):reason=f'unsupported type pair: {a} × {b}'+('; use declared time_series or guide panel for temporal dimensions' if 'temporal' in (a,b) else '')
        elif len(cases)<2:reason='fewer than two complete finite cases'
        else:
            measure=association(a,b,cases)
            if measure is None:reason='constant numeric input' if a in NUMERIC and b in NUMERIC else 'constant or undefined target association'
        if reason:
            selection['excluded'].append({'column':name,'reason':reason});continue
        if a in NUMERIC and b in NUMERIC:
            method='pearson';stats={'n':len(cases),'pearson_r':measure['value'],'p_value':None,'p_value_status':'unavailable'}
        elif a in NUMERIC or b in NUMERIC:
            method='grouped_numeric';gi,ni=(i,ti) if a in CATEGORY else (ti,i);groups=defaultdict(list)
            for row in rows:
                g,v=cell(row[gi],columns[gi]['effective_type']),cell(row[ni],columns[ni]['effective_type'])
                if g is not None and v is not None:groups[g].append(v)
            stats={'n':len(cases),'group_column':columns[gi]['name'],'numeric_column':columns[ni]['name'],
                   'groups':[{'value':g,'n':len(v),'mean':safe(statistics.mean(v))} for g,v in sorted(groups.items())],'eta':measure['value']}
        else:method='categorical_association';stats={'n':len(cases),'cramers_v':measure['value']}
        pairs.append({'left':name,'right':target,'method':method,'statistics':stats,'association':measure,
                      'generator':'rule:target-v1','semantics':'human-declared' if c['override'] and tc['override'] else 'inferred','uncertainty':WARNING+(' Optional Pearson p-values assume independent paired observations and a suitable null model; the table cannot establish these assumptions.' if method=='pearson' else '')})
    return selection,pairs


def summarize_groups(rows,columns,gi,vi):
    gc,vc=columns[gi],columns[vi];gt,vt=gc['effective_type'],vc['effective_type'];groups=defaultdict(list);missing_group=0
    for row in rows:
        g=cell(row[gi],gt)
        if g is None:missing_group+=1
        else:groups[g].append(cell(row[vi],vt))
    allvalues=[v for values in groups.values() for v in values if v is not None]
    scale=max((abs(v) for v in allvalues),default=1) or 1 if vt in NUMERIC else 1
    sd=statistics.pstdev([v/scale for v in allvalues]) if vt in NUMERIC and allvalues else 0
    levels=sorted(set(allvalues)) if vt in CATEGORY else []
    result=[]
    for g,values in sorted(groups.items()):
        nums=[v for v in values if v is not None];rest=[v for key,vs in groups.items() if key!=g for v in vs];rv=[v for v in rest if v is not None]
        n=len(values);valid=len(nums);item={'value':g,'n':n,'share':safe(n/len(rows)) if rows else None,'valid':valid,'missing':n-valid,'missing_share':safe((n-valid)/n),'small':valid<5,'statistics':{},'contrasts':[],'rest_n':len(rest),'rest_valid':len(rv),'gates':[]}
        if vt in NUMERIC and nums:
            if rv and sd:
                gap=abs(statistics.mean([v/scale for v in nums])-statistics.mean([v/scale for v in rv]))
                item['gates'].append({'measure':'mean','gap':safe(gap*scale),'threshold':safe(sd*scale),'marked':gap>=sd,'status':'computed'})
            else:item['gates'].append({'measure':'mean','status':'not estimable','reason':'no rest values or zero overall SD'})
            item['statistics']={'mean':safe(statistics.mean(nums)),'median':percentile(nums,50),'min':min(nums),'max':max(nums)}
            if rv and sd and abs(statistics.mean([v/scale for v in nums])-statistics.mean([v/scale for v in rv]))>=sd:
                item['contrasts'].append({'measure':'mean','group':item['statistics']['mean'],'rest':safe(statistics.mean(rv)),'basis':'gap >= overall population SD'})
        elif vt in CATEGORY:
            counts=Counter(nums);rc=Counter(rv)
            item['statistics']['rates']=[{'value':level,'count':counts[level],'share':safe(counts[level]/valid) if valid else None} for level in levels]
            for level in levels:
                if nums and rv:item['gates'].append({'measure':'rate: '+level,'gap':safe(abs(counts[level]/valid-rc[level]/len(rv))),'threshold':.3,'marked':abs(counts[level]/valid-rc[level]/len(rv))>=.3,'status':'computed'})
                if nums and rv and abs(counts[level]/valid-rc[level]/len(rv))>=.3:item['contrasts'].append({'measure':'rate: '+level,'group':safe(counts[level]/valid),'rest':safe(rc[level]/len(rv)),'basis':'absolute gap >=30 percentage points'})
        if rest:item['gates'].append({'measure':'missing share','gap':safe(abs((n-valid)/n-(len(rest)-len(rv))/len(rest))),'threshold':.3,'marked':abs((n-valid)/n-(len(rest)-len(rv))/len(rest))>=.3,'status':'computed'})
        if rest and abs((n-valid)/n-(len(rest)-len(rv))/len(rest))>=.3:
            item['contrasts'].append({'measure':'missing share','group':item['missing_share'],'rest':safe((len(rest)-len(rv))/len(rest)),'basis':'absolute gap >=30 percentage points'})
        result.append(item)
    return {'group_column':gc['name'],'value_column':vc['name'],'value_type':vt,'group_missing':missing_group,'share_denominator':len(rows),'groups':result}


def has_log(col):return any(c.get('scale')=='log10' for c in col.get('univariate',{}).get('charts',[]))


def axis_label(col,log=False):
    units=col.get('univariate',{}).get('units')
    return col['name']+(' ('+units['value']+')' if units else '')+(' (log scale)' if log else '')


def geometry_percentile(values,p):
    """Unrounded normalized quantile for geometry; statistical percentile stays rounded."""
    ordered=sorted(values);position=(len(ordered)-1)*p/100
    lo=int(position);hi=min(lo+1,len(ordered)-1);weight=position-lo
    scale=max(abs(ordered[lo]),abs(ordered[hi])) or 1
    value=(ordered[lo]/scale*(1-weight)+ordered[hi]/scale*weight)*scale
    return min(ordered[hi],max(ordered[lo],value))


def relationship_chart(rows,columns,pair):
    ix,iy=[next(i for i,c in enumerate(columns) if c['name']==name) for name in (pair['left'],pair['right'])]
    xcol,ycol=columns[ix],columns[iy];a,b=xcol['effective_type'],ycol['effective_type'];cases=[(cell(r[ix],a),cell(r[iy],b)) for r in rows]
    complete=[(x,y) for x,y in cases if x is not None and y is not None];n=len(complete)
    base={'title':'Target: '+pair['left']+' × '+pair['right'],'x_label':pair['left'],'y_label':pair['right'],'note':WARNING,'n':n,'total_rows':len(rows)}
    if a in NUMERIC and b in NUMERIC:
        xl,yl=has_log(xcol),has_log(ycol);eligible=sorted((x,y) for x,y in complete if (not xl or x>0) and (not yl or y>0))
        chosen=eligible if len(eligible)<=200 else [eligible[round(i*(len(eligible)-1)/199)] for i in range(200)]
        return {**base,'kind':'scatter','points':[{'x':x,'y':y} for x,y in chosen],'x_label':axis_label(xcol,xl),'y_label':axis_label(ycol,yl),'x_scale':'log10' if xl else 'linear','y_scale':'log10' if yl else 'linear','omitted_nonpositive':n-len(eligible),'omitted_points':max(0,len(eligible)-200),'plotted':len(chosen)} if chosen else None
    if b in CATEGORY:
        levels=sorted(set(y for _,y in complete));groups=[]
        if a in NUMERIC:
            xs=[x for x,_ in complete];lo,hi=min(xs),max(xs);scale=max(abs(lo),abs(hi),1);span=hi/scale-lo/scale
            for k in range(4):
                values=[y for x,y in complete if min(3,int((x/scale-lo/scale)/span*4))==k] if span else [y for _,y in complete] if k==0 else []
                low=(lo/scale+span*k/4)*scale;high=(lo/scale+span*(k+1)/4)*scale
                groups.append({'label':formatted(low)+' to '+formatted(high),'n':len(values),'rates':{v:safe(values.count(v)/len(values)) if values else 0 for v in levels}})
        else:
            for g in sorted(set(x for x,_ in complete)):
                values=[y for x,y in complete if x==g];groups.append({'label':g,'n':len(values),'rates':{v:safe(values.count(v)/len(values)) for v in levels}})
        return {**base,'kind':'rates','data':groups,'levels':levels,'x_label':'Target category share among complete cases','y_label':pair['left']+(' (four equal-width bins)' if a in NUMERIC else ''),'plotted':n}
    groups=[];log=has_log(ycol)
    for g in sorted(set(x for x,_ in complete)):
        raw=[y for x,y in complete if x==g];values=[v for v in raw if not log or v>0]
        groups.append({'label':g,'n':len(values),'excluded_nonpositive':len(raw)-len(values),'box':{k:geometry_percentile(values,p) for k,p in [('min',0),('q1',25),('median',50),('q3',75),('max',100)]} if values else None})
    return {**base,'kind':'group_box','data':groups,'x_label':axis_label(ycol,log),'y_label':pair['left'],'x_scale':'log10' if log else 'linear','omitted_nonpositive':sum(y<=0 for _,y in complete) if log else 0,'plotted':sum(y>0 for _,y in complete) if log else n}


def build_target_analysis(rows,columns,cfg,selection,pairs,emit):
    target=cfg.get('target');ranked=[r for r in selection.get('ranked',[]) if r.get('measure')]
    result={'target':target,'status':'active' if target and ranked else 'skipped','reason':'Target declared; detailed relationships share pair_budget.' if target and ranked else 'No target declared; documentation/QA fallback applies.' if not target else 'No eligible target relationships; see exclusions.','warning':WARNING,'grouping_policy':selection.get('grouping_policy','Within-group summaries accompany selected category-bearing pairs only.'),'ranked':[{'column':r['left'],**{k:r[k] for k in ('rank','measure','value','strength','n','selected')}} for r in ranked],'excluded':selection['excluded'],'groups':[],'charts':[]}
    for pi,pair in enumerate(pairs):
        if 'association' not in pair:continue
        ix,iy=[next(i for i,c in enumerate(columns) if c['name']==name) for name in (pair['left'],pair['right'])]
        if columns[iy]['effective_type'] in CATEGORY:gi,vi=iy,ix
        elif columns[ix]['effective_type'] in CATEGORY:gi,vi=ix,iy
        else:gi=None
        if gi is not None:
            summary=summarize_groups(rows,columns,gi,vi);result['groups'].append(summary)
            for j,group in enumerate(summary['groups']):
                if not group['contrasts']:continue
                caution=' Too small to read reliably (valid n<5).' if group['small'] else ''
                fid=f'target-group-{pi}-{j}';message=f"{summary['value_column']} differs descriptively in {summary['group_column']}={group['value']!r}: {group['n']} rows, {group['valid']} valid; rest {group['rest_n']} rows. "+'; '.join(c['measure']+' '+formatted(c['group'])+' versus rest '+formatted(c['rest']) for c in group['contrasts'])+'.'+caution
                emit(fid,'observation',message,[{'path':f'target_analysis.groups.{len(result["groups"])-1}.groups.{j}','value':group}],WARNING,'rule:target-v1',rule='target_group_contrast',columns=[summary['group_column'],summary['value_column']])
                emit(fid+'-review','action',f"Review the collection context and sample sizes for {summary['group_column']}={group['value']!r} before interpreting the {summary['value_column']} contrast.",[{'finding':fid}],WARNING,'rule:target-v1',rule='target_group_contrast',columns=[summary['group_column'],summary['value_column']])
        ch=relationship_chart(rows,columns,pair)
        if ch:result['charts'].append(ch)
    return result


def target_tables(d):
    ta=d.get('target_analysis');tables=[]
    if not ta or not ta['target']:return tables
    tables.append({'caption':'Descriptive target ranking — unlike measures are priority heuristics, not causal','headers':['Column','Measure','Value','Complete n','Selected'],'rows':[[r['column'],r['measure'],formatted(r['value']),formatted(r['n']),'Yes' if r['selected'] else 'No'] for r in ta['ranked']],'numeric':[2,3]})
    if ta['excluded']:tables.append({'caption':'Target exclusions and budget limits','headers':['Column','Reason'],'rows':[[r['column'],r['reason']] for r in ta['excluded']],'numeric':[]})
    for s in ta['groups']:
        rows=[]
        for g in s['groups']:
            from .verdicts import gate_text
            gates='; '.join(gate_text(x) for x in g.get('gates',[])) or 'gate evidence unavailable in this saved artifact'
            stats=g['statistics'];detail='\n'.join(k+': '+formatted(v) for k,v in stats.items() if k!='rates')
            if 'rates' in stats:detail='\n'.join(r['value']+': '+formatted(r['share'],True)+f" ({r['count']}/{g['valid']})" for r in stats['rates'])
            rows.append([g['value'],formatted(g['n']),formatted(g['share'],True),f"{g['valid']} / {g['missing']}",detail,('too small to read reliably (valid n<5); ' if g['small'] else '')+('marked descriptive contrast' if g['contrasts'] else 'No marked contrast')+'; '+gates])
        tables.append({'caption':f"{s['value_column']} within {s['group_column']} — shares of {s['share_denominator']} rows; {s['group_missing']} missing grouping rows",'headers':['Group','Count','Share','Valid / missing','Key statistics / rates','Caution'],'rows':rows,'numeric':[1,2]})
    return tables
