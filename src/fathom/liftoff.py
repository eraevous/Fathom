"""Declaration-free discovery with isolated, explicitly conditional measurements (spec013)."""
from copy import deepcopy
from html import escape
import json

from .config import validate_config
from .configure import build_schema, render_page
from .models import ProfilingResult
from .parsing import finite_number
from .profiler import profile
from .rows import interval
from .timeseries import time_series, undeclared, RULES as TS_RULES

MAX_SERIES_PREVIEWS = 20
ZERO_COLUMNS = 10
ZERO_RESULTS = 20
ZERO_RULE = 'at most10numeric ×10categorical/boolean columns in input order,2..20levels; group/rest each>=10finite; group allzero; zero-rate gap>=0.30; at most20reported patterns'


def finding(doc, fid, kind, message, rule, path, value, status='automated', generator='rule:liftoff-v1'):
    return {'id':fid,'kind':kind,'message':message,'rule':rule,'generator':generator,'status':status,
            'evidence':[{'path':path,'value':value}],
            'uncertainty':'The table does not establish domain meaning or cause. '+('This declaration is hypothetical and is not applied.' if status=='provisional' else 'Automatically measured under a disclosed rule.'),
            'provenance':{'source_sha256':doc['source']['sha256'],'rule_version':1}}


def zero_contrasts(rows, columns, doc):
    """A narrow QA observation, not an analysis selector or stage-two rule."""
    numeric=[(i,c) for i,c in enumerate(columns) if c['effective_type']=='numeric']
    categorical=[(i,c) for i,c in enumerate(columns) if c['effective_type'] in {'categorical','boolean'}]
    results=[];eligible=0
    for vi,vcol in numeric[:ZERO_COLUMNS]:
        vals=[finite_number(r[vi]) if r[vi] is not None else None for r in rows]
        for gi,gcol in categorical[:ZERO_COLUMNS]:
            levels=sorted({r[gi] for r in rows if r[gi] is not None})
            if not 2<=len(levels)<=20:continue
            eligible+=1
            groups={g:[i for i,r in enumerate(rows) if r[gi]==g] for g in levels}
            def counts(indices):
                return {'rows':len(indices),'finite':sum(vals[i] is not None for i in indices),
                        'zeros':sum(vals[i]==0 for i in indices),'missing':sum(rows[i][vi] is None for i in indices),
                        'invalid':sum(rows[i][vi] is not None and vals[i] is None for i in indices)}
            for group,indices in groups.items():
                a=counts(indices);b=counts([i for g,ii in groups.items() if g!=group for i in ii])
                if a['finite']<10 or b['finite']<10 or a['zeros']!=a['finite'] or 1-b['zeros']/b['finite']<.30:continue
                results.append({'column':vcol['name'],'group_column':gcol['name'],'group':group,'group_rows':a['rows'],
                                'group_finite':a['finite'],'group_zeros':a['zeros'],'group_missing':a['missing'],'group_invalid':a['invalid'],
                                'rest':b,'missing_group_rows':sum(r[gi] is None for r in rows),'rule':ZERO_RULE})
    fs=[]
    for i,v in enumerate(results[:ZERO_RESULTS]):
        path=f'liftoff.zero_contrasts.results.{i}'
        message=(f"{v['column']} is 0 in {v['group_zeros']:,} of {v['group_finite']:,} finite values where {v['group_column']}={v['group']!r}; "
                 f"{v['rest']['zeros']:,} of {v['rest']['finite']:,} elsewhere; {v['missing_group_rows']:,} rows with missing group labels excluded.")
        fs.append(finding(doc,f'lift-zero-{i}','observation',message,'all_zero_group',path,v))
        fs.append(finding(doc,f'lift-zero-{i}-question','question',f"Are the {v['column']} zeros for {v['group_column']}={v['group']!r} structural, unrecorded, or literal measured values?",'all_zero_group',path,v))
    return {'rule':ZERO_RULE,'results':results[:ZERO_RESULTS],'omitted_results':max(0,len(results)-ZERO_RESULTS),
            'numeric_columns_screened':[c['name'] for _,c in numeric[:ZERO_COLUMNS]],'group_columns_screened':[c['name'] for _,c in categorical[:ZERO_COLUMNS]],
            'omitted_numeric_columns':max(0,len(numeric)-ZERO_COLUMNS),'omitted_group_columns':max(0,len(categorical)-ZERO_COLUMNS),'eligible_pairs':eligible},fs


def build_liftoff(data):
    default=profile(data);doc=deepcopy(default.document);cfg=validate_config();rows=data.frame.values.tolist();columns=doc['columns']
    schema=build_schema(doc,data.frame,None)
    candidates=(undeclared(rows,columns,cfg) or {}).get('temporal_columns',[])
    schema['time_series_suggestions']=[{**c,'reason':f"{c['distinct_periods']:,} distinct {c['granularity']} periods; event counts are a possible declaration, not an inferred meaning"} for c in candidates]
    schema['series_value_options']=[c['name'] for c in columns if c['effective_type']=='numeric']
    schema['extension_points']=[e for e in schema['extension_points'] if e['key']!='time_series']
    schema['fixed_rules']=schema['fixed_rules']+[{'name':'Liftoff zero contrast','rule':ZERO_RULE,'source':'FT-LIFT-R1@1 (provisional)'},
                                              *({'name':'Temporal structure: '+k,'rule':v,'source':'FT-TS1-R1@2'} for k,v in TS_RULES.items())]
    previews={'intervals':[],'time_series':[]}
    for i,suggestion in enumerate(schema['interval_suggestions']):
        declaration={k:suggestion[k] for k in ('start','end')};fs=[];path=f'liftoff.previews.intervals.{i}.result'
        label=f"If you declare {declaration['start']} → {declaration['end']}"
        def observe(fid,rule,names,message,value,question):
            message=message.replace('Declared interval '+declaration['start']+' → '+declaration['end']+':',label+':',1)
            fs.append(finding(doc,f'lift-interval-{i}','observation',message,rule,path,value,'provisional','rule:rows-v1'))
            if question:fs.append(finding(doc,f'lift-interval-{i}-question','question',label+': '+question,rule,path,value,'provisional','rule:rows-v1'))
        result=interval(rows,columns,declaration,observe)
        previews['intervals'].append({'status':'provisional','declaration':declaration,'result':result,'findings':fs})
    for i,candidate in enumerate(candidates[:MAX_SERIES_PREVIEWS]):
        declaration={'time':candidate['column'],'value':None,'granularities':['auto']};fs=[]
        label=f"If you declare event counts by {candidate['column']} (auto granularities)"
        def emit(fid,kind,message,evidence,uncertainty,generator,**extra):
            fs.append(finding(doc,f'lift-series-{i}-{fid}',kind,label+': '+message,extra['rule'],
                              f'liftoff.previews.time_series.{i}.result',deepcopy(evidence[0].get('value')) if 'value' in evidence[0] else {'related_finding':f'lift-series-{i}-ts-0-0'},'provisional',generator))
            if 'finding' in evidence[0]:fs[-1]['evidence']=[{'finding':f"lift-series-{i}-"+evidence[0]['finding']}]
        ts=time_series(rows,columns,validate_config({'time_series':[declaration]}),emit)
        previews['time_series'].append({'status':'provisional','declaration':declaration,'result':ts['series'][0],'findings':fs,'dependencies':ts['dependencies'],'rules':ts['rules']})
    zeros,automated=zero_contrasts(rows,columns,doc)
    nt=sum(c['effective_type']=='temporal' for c in columns)
    doc['liftoff']={'version':1,'stage':'discovery','effective_configuration':{},'configuration':schema,
                    'automated_findings':automated,'zero_contrasts':zeros,'previews':previews,
                    'coverage':{'interval_candidates':nt*(nt-1),'interval_previewed':len(previews['intervals']),
                                'interval_omitted':max(0,nt*(nt-1)-len(previews['intervals'])),
                                'series_candidates':len(candidates),'series_previewed':len(previews['time_series']),
                                'series_omitted':max(0,len(candidates)-len(previews['time_series']))},
                    'limits':['No meaning, target, interval or series is automatically declared.','Previews use events and auto granularities; changing value/grain changes the question.',
                              'No provisional target associations or by-group series.','Time-series engine caps and optional spectral status are retained.',
                              'Stage-two conditional-zero finding is not added; group n/min/max can corroborate all-zero values.']}
    return ProfilingResult(doc)


def validate_liftoff(doc):
    b=doc['liftoff']
    if not isinstance(b,dict) or type(b.get('version')) is not int or b.get('version')!=1 or b.get('stage')!='discovery' or b.get('effective_configuration')!={}:raise ValueError('invalid liftoff boundary')
    if doc['schema_version']!=2 or doc['purpose'].get('target') is not None:raise ValueError('invalid liftoff default profile')
    if not isinstance(doc.get('row_structure'),dict) or not isinstance(doc.get('time_series'),dict):raise ValueError('invalid liftoff default structures')
    if doc.get('row_structure',{}).get('intervals') or doc.get('time_series',{}).get('declared'):raise ValueError('liftoff must not apply declarations')
    if not isinstance(b.get('configuration'),dict) or not isinstance(b.get('automated_findings'),list):raise ValueError('invalid liftoff fields')
    if not isinstance(b.get('limits'),list) or any(not isinstance(limit,str) for limit in b['limits']):raise ValueError('invalid liftoff limits')
    coverage=b.get('coverage')
    coverage_keys={f'{kind}_{measure}' for kind in ('interval','series') for measure in ('candidates','previewed','omitted')}
    if not isinstance(coverage,dict) or not coverage_keys<=coverage.keys() or any(type(coverage[key]) is not int or coverage[key]<0 for key in coverage_keys):raise ValueError('invalid liftoff coverage')
    zero=b.get('zero_contrasts')
    if (not isinstance(zero,dict) or any(key not in zero for key in ('rule','omitted_numeric_columns','omitted_group_columns','omitted_results'))
            or not isinstance(zero['rule'],str) or any(type(zero[key]) is not int or zero[key]<0 for key in ('omitted_numeric_columns','omitted_group_columns','omitted_results'))):raise ValueError('invalid liftoff zero contrasts')
    def validate_finding(f,status):
        if (not isinstance(f,dict) or not {'id','kind','message','rule','generator','evidence','uncertainty','provenance','status'}<=f.keys()
                or f['status']!=status or f['kind'] not in ('observation','question')
                or any(not isinstance(f[key],str) for key in ('id','kind','message','rule','generator','uncertainty'))
                or not isinstance(f['provenance'],dict) or not isinstance(f['evidence'],list)):
            raise ValueError('invalid liftoff finding')
        for evidence in f['evidence']:
            if not isinstance(evidence,dict) or not (isinstance(evidence.get('finding'),str) or (isinstance(evidence.get('path'),str) and 'value' in evidence)):
                raise ValueError('invalid liftoff finding evidence')
    for f in b['automated_findings']:
        validate_finding(f,'automated')
    schema=b['configuration'];init=schema.get('initial')
    if not isinstance(init,dict) or init.get('target') is not None or init.get('intervals') or init.get('columns') or schema.get('base_columns') or schema.get('base')!={}:raise ValueError('liftoff controls must start unselected')
    if not isinstance(b.get('previews'),dict) or any(not isinstance(b['previews'].get(k),list) for k in ('intervals','time_series')):raise ValueError('invalid liftoff previews')
    for kind in ('intervals','time_series'):
        for p in b['previews'][kind]:
            if not isinstance(p,dict) or p.get('status')!='provisional' or not isinstance(p.get('declaration'),dict) or not isinstance(p.get('result'),dict) or not isinstance(p.get('findings'),list):raise ValueError('invalid liftoff preview')
            validate_config({kind:[p['declaration']]},[c['name'] for c in doc['columns']])
            for f in p['findings']:
                validate_finding(f,'provisional')
                if not f['message'].startswith('If you declare'):raise ValueError('invalid provisional finding')


def brief_html(doc):
    from .renderers import finding_html,unknowns
    from .presentation import html_table
    from .verdicts import headlines_html
    from .temporal_view import temporal_html
    b=doc['liftoff'];out=['<section id="brief"><h1>Fathom liftoff</h1><h2>Brief</h2>',
        headlines_html(doc),'<p>Automatically measured facts come first. Conditional measurements say <strong>If you declare …</strong>. No suggestion is applied; meaning, observation process and analytical relevance remain yours to declare.</p>',
        '<p><a href="#configurations">Configure an analysis</a> · <a href="#lift-questions">Open questions</a></p><h3>What the table looks like</h3>',html_table({'caption':'Dataset snapshot','headers':['Measure','Value'],'numeric':[1],
            'rows':[['Rows',f"{doc['overview']['rows']:,}"],['Columns',doc['overview']['columns']],['Missing cells',doc['overview']['missing_cells']],['Exact duplicate rows',doc['overview']['duplicate_rows']]]}),
        '<p>'+escape(doc['dataset']['description']['text'])+'</p>',
        '<h3>Observation process</h3><p>Row unit and generating process are not declared. Repeated records or timestamps are measured structures, not proof of duplicate events or independent observations.</p>']
    process=[]
    for t in doc.get('row_structure',{}).get('temporal',[]):
        dt=t.get('duplicate_timestamps') or {}
        process.append([t['column'],f"{t['dated_values']:,}",f"{dt['distinct']:,}" if dt else 'Not measured',f"{dt['rows_repeating']:,}" if dt else 'Not measured'])
    if process:out.append(html_table({'caption':'Automatic temporal coverage (timestamp distinctness only where the existing rule applies)','headers':['Column','Parsed dates','Distinct timestamps','Repeat rows'],'numeric':[1,2,3],'rows':process}))
    primary=[f for f in doc['findings'] if f['kind']=='observation' and f.get('rule')!='dataset_summary' and not (f['id']=='duplicates' and not doc['overview']['duplicate_rows'])]
    out+=['<h3>Automatically measured findings</h3>']
    for f in primary+b['automated_findings']:
        if f['kind']=='observation':out+=[finding_html(f,set()),'<p class="muted">Automatic · rule '+escape(f.get('rule',f['generator']))+'</p>']
    if not primary and not b['automated_findings']:out+=['<p>No matching automatic diagnostic under the disclosed rules; silence is not a quality verdict.</p>']
    out+=['<details><summary>All default-profile findings (including rule-generated suggested actions requiring human review)</summary>']+[finding_html(f,set()) for f in doc['findings'] if f not in primary]+['</details>']
    # Primary originals were already rendered; no duplicate IDs in the full disclosure.
    out+=['<h3>Conditional measurements — not declarations</h3>']
    for kind in ('intervals','time_series'):
        for i,p in enumerate(b['previews'][kind]):
            for f in p['findings']:
                shown=f
                if f['rule']=='temporal_structure':
                    shown=deepcopy(f);series=p['result']['groups'][0];process=series['observation_process']
                    cycle=next(x for x in series['signals'] if x['signal'].startswith('repeating cycle'))
                    states='; '.join(k+' at '+', '.join(cycle[k]) for k in ('present','absent','undefined','not estimable','insufficient evidence') if cycle[k])
                    shown['message']=(f"If you declare event counts by {p['declaration']['time']} (auto granularities): "+
                                      f"{process['rows_with_parsed_time']:,} of {process['raw_rows']:,} rows parsed; {process['distinct_timestamps']:,} distinct timestamps; "+
                                      f"{process['duplicate_timestamp_rows']:,} repeat rows. Repeating cycle: {states}.")
                out+=[finding_html(shown,set()),'<p class="muted">Provisional · rule '+escape(f['rule'])+'</p>']
                if shown is not f:out.append('<details><summary>Full temporal signal statement</summary><p>'+escape(f['message'])+'</p></details>')
            if kind=='time_series':
                label='If you declare event counts by '+p['declaration']['time']+' (auto granularities)'
                detail=temporal_html({'time_series':{'rules':p['rules'],'series':[p['result']]}})
                detail=detail.replace('id="temporal-structure"',f'id="lift-series-detail-{i}"').replace('Declared series only.',escape(label)+'. Provisional; not applied.',1)
                out+=['<details><summary>'+escape(label)+' — process, signals and exact lags</summary>'+detail+'</details>']
    if not any(b['previews'].values()):out+=['<p>No eligible interval or event-series preview. The candidate rules and counts are disclosed below.</p>']
    out+=['<h3 id="lift-questions">Open questions</h3>','<ul>']+['<li>'+escape(q)+'</li>' for q in unknowns(doc)]+['</ul>']
    for f in b['automated_findings']:
        if f['kind']=='question':out.append(finding_html(f,set()))
    out+=['<h3>What awaits a declaration or was not examined</h3><ul>']+['<li>'+escape(v)+'</li>' for v in b['limits']]+['</ul>',
           html_table({'caption':'Candidate coverage (bounded, not exhaustive)','headers':['Candidate','Found','Previewed','Omitted'],'numeric':[1,2,3],
                       'rows':[[k,b['coverage'][k+'_candidates'],b['coverage'][k+'_previewed'],b['coverage'][k+'_omitted']] for k in ('interval','series')]}),
           '<p>Zero check: '+escape(b['zero_contrasts']['rule'])+f". Omitted numeric/group columns: {b['zero_contrasts']['omitted_numeric_columns']}/{b['zero_contrasts']['omitted_group_columns']}; matching patterns omitted: {b['zero_contrasts']['omitted_results']}.</p>",
           '</section><!-- end brief -->']
    return ''.join(out)


def render_liftoff(result):
    # Canonicalize once so JSON-loaded and in-memory artifacts render identically.
    from .models import canonical_json
    doc=json.loads(canonical_json(result.document))
    return render_page(doc['liftoff']['configuration'],brief=brief_html(doc),download_name='liftoff.yaml')
