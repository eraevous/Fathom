"""Person-first offline views, derived solely from the saved result."""

from collections import Counter
from html import escape
import re

from .models import ProfilingResult

KINDS = (("observation", "Observations"), ("interpretation", "Interpretations"),
         ("hypothesis", "Hypotheses"), ("action", "Suggested actions"), ("question", "Open questions"))


def md_text(value):
    return re.sub(r"([\\`*_{}\[\]()#|])", r"\\\1", escape(str(value), quote=False)).replace("\n", " ")


def label(key):
    return str(key).replace("_", " ").replace(".", " / ").capitalize()


def scalar(value):
    if value is None: return "Unknown / unavailable"
    if isinstance(value, bool): return "Yes" if value else "No"
    if isinstance(value, float): return f"{value:.10g}"
    return str(value)


def readable_html(value):
    if isinstance(value, dict):
        if not value: return '<p>None recorded.</p>'
        return '<dl>' + ''.join('<dt>'+escape(label(k))+'</dt><dd>'+readable_html(v)+'</dd>' for k,v in sorted(value.items(),key=lambda item:str(item[0]))) + '</dl>'
    if isinstance(value, (list,tuple)):
        return '<ul>'+''.join('<li>'+readable_html(v)+'</li>' for v in value)+'</ul>' if value else 'None recorded'
    return escape(scalar(value))


def readable_md(value, depth=0):
    if isinstance(value, dict):
        return ''.join('  '*depth+'- '+md_text(label(k))+': '+ ('\n'+readable_md(v,depth+1) if isinstance(v,(dict,list,tuple)) else md_text(scalar(v))+'\n') for k,v in sorted(value.items(),key=lambda item:str(item[0]))) or '  '*depth+'- None recorded.\n'
    if isinstance(value,(list,tuple)):
        return ''.join('  '*depth+'- '+ ('\n'+readable_md(v,depth+1) if isinstance(v,(dict,list,tuple)) else md_text(scalar(v))+'\n') for v in value) or '  '*depth+'- None recorded.\n'
    return '  '*depth+md_text(scalar(value))+'\n'


def fraction(measure, total):
    if not isinstance(measure,dict): return str(measure)
    rate = measure.get('share')
    return f"{measure['count']}/{total}" + (f" ({rate:.1%})" if rate is not None else ' (share unavailable)')


def summary_rows(d):
    s, overview = d.get('dataset_summary'), d['overview']
    if s is None:
        unavailable = 'Unavailable in this saved artifact'
        s = {**overview, 'complete_rows': unavailable, 'complete_columns': unavailable,
             'duplicate_columns': unavailable, 'lockstep_columns': unavailable,
             'constant_columns': unavailable, 'near_constant_columns': unavailable,
             'inferred_types': dict(sorted(Counter(c['inference']['type'] for c in d['columns']).items())),
             'finding_links': {}}
    items = [('rows','Rows',s['rows']),('columns','Columns',s['columns']),
             ('complete_rows','Complete rows',fraction(s['complete_rows'],s['rows'])),
             ('complete_columns','Complete columns',fraction(s['complete_columns'],s['columns'])),
             ('duplicate_rows','Exact duplicate rows beyond the first',s['duplicate_rows']),
             ('duplicate_columns','Duplicated columns beyond the first',s['duplicate_columns']),
             ('lockstep_columns','Lockstep columns beyond representatives',s['lockstep_columns']),
             ('inferred_types','Columns by inferred type',', '.join(f'{k}: {v}' for k,v in s['inferred_types'].items()) or 'No columns'),
             ('constant_columns','Constant columns',', '.join(s['constant_columns']) or 'None flagged' if isinstance(s['constant_columns'],list) else s['constant_columns']),
             ('near_constant_columns','Near-constant columns',', '.join(s['near_constant_columns']) or 'None flagged' if isinstance(s['near_constant_columns'],list) else s['near_constant_columns']),
             ('missing_cells','Overall missing cells',fraction(s['missing_cells'],s['rows']*s['columns']))]
    for key in ('duplicate_groups','lockstep_groups'):
        if key in s: items.append((key,label(key),'; '.join(', '.join(g) for g in s[key]) or 'None flagged'))
    return [(title,scalar(value),s.get('finding_links',{}).get(key,[])) for key,title,value in items]


def repetitive(f, ids=None):
    if ids is not None: return f["id"] in ids
    return bool(re.fullmatch(r'column-\d+-(?:type|meaning)', f['id']))


def repetition_groups(d):
    types=[f for f in d['findings'] if re.fullmatch(r'column-\d+-type',f['id'])]
    meanings=[f for f in d['findings'] if re.fullmatch(r'column-\d+-meaning',f['id'])]
    result = [(f'{len(types)} columns have inferred type readings; human overrides are retained separately.', types),
              (f'Domain meaning is unknown for {len(meanings)} columns; ask the data owner.', meanings)]
    buckets = {}
    for f in d['findings']:
        if repetitive(f): continue
        match = re.fullmatch(r'column-\d+-(missing|invalid)(-review)?', f['id'])
        rule = f.get('rule') or (match.group(1) if match else None)
        if rule not in {'missing','invalid','sentinel','dummy','placeholder','dominant','constant','skew','temporal_gap'}:
            continue
        buckets.setdefault((rule,f['kind']),[]).append(f)
    for (rule,kind),items in buckets.items():
        if len(items)<2: continue
        names=[]
        for f in items:
            affected=f.get('columns') or [d['columns'][int(f['id'].split('-')[1])]['name']]
            for name in affected:
                if name not in names: names.append(name)
        message=items[0]['message'].rstrip('.')+'; review the same concern across '+str(len(names))+' columns ('+', '.join(names)+').'
        result.append((message,items))
    return result


def unknowns(d):
    questions = [f['message'] for f in d['findings'] if f['id'].startswith('unknown-')]
    return questions or ['Recorded context is supplied by humans; the table does not independently establish domain meaning, causation or fitness for use.']


def bars(items, title):
    if not items: return ''
    maximum=max((n for _,n in items),default=0) or 1
    out=[f'<svg role="img" aria-label="{escape(title,quote=True)}" viewBox="0 0 640 {len(items)*30+12}"><title>{escape(title)}</title>']
    for i,(name,n) in enumerate(items):
        y=10+i*30
        out += [f'<text x="0" y="{y+14}">{escape(name[:28])}</text><rect x="230" y="{y}" width="{round(n/maximum*330,3)}" height="20" fill="#216e73"/><text x="575" y="{y+14}">{n}</text>']
    return ''.join(out)+'</svg>'


def finding_html(f, repeated_ids):
    fid=escape(f['id'],quote=True)
    cls='finding repetitive' if repetitive(f,repeated_ids) else 'finding'
    out=[f'<article id="{fid}" class="{cls}"><p>{escape(f["message"])}</p><details><summary>Evidence and uncertainty</summary>']
    for item in f['evidence']:
        if 'finding' in item:
            ref=escape(item['finding'],quote=True)
            out.append(f'<p>Supported by <a href="#{ref}">{ref}</a>.</p>')
        else:
            out.append(readable_html({label(item['path']):item['value']}))
    out.append('<p>Generator: '+escape(f['generator'])+'</p><p>Uncertainty: '+escape(f['uncertainty'])+'</p>')
    out.append(readable_html({'provenance':f['provenance']}))
    return ''.join(out)+'</details></article>'


def render_html(result: ProfilingResult):
    d=result.document
    out=['<h1>Fathom</h1>']
    if d['kind']=='comparison':
        for title,value in [('Contexts',d['contexts']),('Context differences',d['context_differences']),('Measured deltas',d['deltas']),('Limitations',d['limitations'])]:
            out += ['<section><h2>'+title+'</h2>',readable_html(value),'</section>']
    else:
        out += ['<section class="opening"><h2>Dataset summary</h2><table><thead><tr><th>Measure</th><th>Snapshot</th><th>Evidence</th></tr></thead><tbody>']
        for title,value,refs in summary_rows(d):
            links=' '.join(f'<a href="#{escape(ref,quote=True)}">Finding</a>' for ref in refs) or 'Stored measurement'
            out.append('<tr><th>'+escape(title)+'</th><td>'+escape(value)+'</td><td>'+links+'</td></tr>')
        out += ['</tbody></table><h3>Usefulness</h3><p>'+escape(d['purpose'].get('question') or d['purpose'].get('fallback','Reference, understanding, QA and validation.'))+'</p>',
                '<p>Use these observations to choose what to review; they do not certify fitness or authorize automatic cleaning.</p>',
                '<h3>What the data cannot tell</h3>'+readable_html(unknowns(d))+'</section>',
                '<section id="findings"><h2>Findings</h2><input id="full-view" type="checkbox"><label for="full-view">Show full per-item detail</label>',
                '<div class="full-view">']
        summaries=repetition_groups(d)
        repeated_ids={f['id'] for _,items in summaries for f in items}
        for kind,title in KINDS:
            out.append('<h3>'+title+'</h3>')
            for message,items in summaries:
                if not items or items[0]['kind']!=kind: continue
                links=''.join('<p><a href="#'+escape(f['id'],quote=True)+'">Original item</a>: '+escape(f['message'])+'</p>'+readable_html({'evidence':f['evidence'],'generator':f['generator'],'uncertainty':f['uncertainty'],'provenance':f['provenance']}) for f in items)
                out.append('<div class="summary-view"><p>'+escape(message)+'</p><details><summary>Evidence, uncertainty and original items</summary>'+links+'</details></div>')
            fs=[f for f in d['findings'] if f['kind']==kind]
            out.extend(finding_html(f,repeated_ids) for f in fs)
            if not fs: out.append('<p>None recorded.</p>')
        out += ['</div></section><section><h2>Relations</h2><p>'+escape(d['selection'].get('ranking_rule','Legacy input-order selection; no relevance ranking recorded.'))+'</p>',
                '<p>Selected '+str(len(d['bivariate']))+' relationship(s); budget '+str(d['selection']['budget'])+'.</p>']
        for pair in d['bivariate']:
            out += ['<article><h3>'+escape(pair['left'])+' × '+escape(pair['right'])+'</h3><p>'+escape(pair['method'])+' · '+escape(pair['semantics'])+'</p>',
                    readable_html(pair['statistics']),'<p>'+escape(pair['uncertainty'])+'</p></article>']
        out += ['<details><summary>Ranking and exclusions</summary>',readable_html(d['selection']),'</details>']
        if 'quality' in d:
            out += ['<details><summary>Quality rules and screening coverage</summary>',readable_html(d['quality']),'</details>']
        out += ['</section><section><h2>Dictionary</h2><p>Inferred readings are lexical and uncalibrated; meanings are human declarations or unknown.</p>',
                bars([(c['name'],c['missing']) for c in d['columns'][:20]],'Missing cells by column (first 20)'),
                '<table><thead><tr><th>Column / meaning</th><th>Type / basis</th><th>Missing / distinct</th><th>Details</th></tr></thead><tbody>']
        for c in d['columns']:
            meaning=c['meaning']['value']+' (human)' if c['meaning'] else 'Unknown meaning'
            basis='human override; inferred '+c['inference']['type'] if c['override'] else 'inferred'
            details={k:c[k] for k in ('observed_type','inference','override','statistics','examples','frequencies')}
            out.append('<tr><td>'+escape(c['name'])+'<br><small>'+escape(meaning)+'</small></td><td>'+escape(c['effective_type'])+'<br><small>'+escape(basis)+'</small></td><td>'+str(c['missing'])+'/'+str(c['count'])+' missing; '+str(c['distinct'])+' distinct</td><td><details><summary>Column evidence</summary>'+readable_html(details)+'</details></td></tr>')
        out += ['</tbody></table></section><section><h2>Provenance</h2>',readable_html({'source':d['source'],'context':d['context'],'schema':d['schema'],'dependencies':d['dependencies']}),
                '<h3>Working record (human declarations)</h3>',readable_html(d['working_record']),'</section>']
    if d.get('annotations'):
        out += ['<section><h2>Labelled annotations</h2>',readable_html(d['annotations']),'</section>']
    css='''body{font:16px/1.55 system-ui,sans-serif;background:#f5f8f7;color:#193e42;max-width:1120px;padding:32px;margin:auto}h1{font-size:44px;margin-bottom:8px}h2{border-bottom:2px solid #28777c;padding-bottom:7px;margin-top:40px}h3{margin-top:24px}section{margin-bottom:30px}.opening{background:white;padding:24px;border:1px solid #d5e1df;border-radius:8px}table{border-collapse:collapse;width:100%;background:white}td,th{padding:10px;text-align:left;border-bottom:1px solid #d5e1df;vertical-align:top}td{overflow-wrap:anywhere}article{background:white;border-left:3px solid #b9d3cf;padding:8px 16px;margin:10px 0}article>p{margin:7px 0}details{margin:8px 0}summary{cursor:pointer;color:#12656b;font-weight:600}details[open]{padding-bottom:10px}a{color:#12656b}small{color:#4d676b}dt{font-weight:600;margin-top:8px}dd{margin-left:20px;overflow-wrap:anywhere}ul{padding-left:24px}svg{width:100%;max-width:760px}svg text{font:13px system-ui,sans-serif}label{cursor:pointer;font-weight:600;margin-left:8px}.summary-view{background:#e9f2ee;padding:12px;margin-top:12px}.repetitive{display:none}.repetitive:target{display:block}#full-view:checked ~ .summary-view{display:none}#full-view:checked ~ .full-view .summary-view{display:none}#full-view:checked ~ .full-view .repetitive{display:block}@media(max-width:700px){body{padding:12px}td,th{padding:6px;font-size:14px}.opening{padding:12px}}@media print{body{background:white;padding:0}details{break-inside:avoid}.repetitive{display:block}}'''
    return '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fathom — '+escape(d['kind'])+'</title><style>'+css+'</style></head><body>'+'\n'.join(out)+'</body></html>\n'


def render_markdown(result: ProfilingResult):
    d=result.document
    lines=['# Fathom — '+d['kind'],'']
    if d['kind']=='comparison':
        for title,value in [('Contexts',d['contexts']),('Context differences',d['context_differences']),('Measured deltas',d['deltas']),('Limitations',d['limitations'])]:
            lines += ['## '+title,'',readable_md(value),'']
    else:
        lines += ['## Dataset summary','','| Measure | Snapshot | Evidence |','| --- | --- | --- |']
        for title,value,refs in summary_rows(d):
            links=', '.join('[Finding](#'+ref+')' for ref in refs) or 'Stored measurement'
            lines.append('| '+md_text(title)+' | '+md_text(value)+' | '+links+' |')
        lines += ['','### Usefulness','',md_text(d['purpose'].get('question') or d['purpose'].get('fallback','Reference, understanding, QA and validation.')),'',
                  'Choose what to review; these observations do not certify fitness or authorize automatic cleaning.','','### What the data cannot tell','',readable_md(unknowns(d)),
                  '## Findings','']
        summaries=repetition_groups(d)
        repeated=[f for _,items in summaries for f in items]
        repeated_ids={f['id'] for f in repeated}
        for kind,title in KINDS:
            lines += ['### '+title,'']
            for message,items in summaries:
                if items and items[0]['kind']==kind: lines += [md_text(message),'']
            fs=[f for f in d['findings'] if f['kind']==kind and not repetitive(f,repeated_ids)]
            for f in fs: lines += markdown_finding(f)
            if not fs: lines += ['No additional items recorded.','']
        if repeated:
            lines += ['<details><summary>Full repetitive per-column findings</summary>','']
            for f in repeated: lines += markdown_finding(f)
            lines += ['</details>','']
        lines += ['## Relations','',md_text(d['selection'].get('ranking_rule','Legacy input-order selection; no relevance ranking recorded.')),'',
                  f"Selected {len(d['bivariate'])} relationship(s); budget {d['selection']['budget']}.",'']
        for pair in d['bivariate']:
            lines += ['### '+md_text(pair['left'])+' × '+md_text(pair['right']),'',md_text(pair['method']+' · '+pair['semantics']),'',readable_md(pair['statistics']),md_text(pair['uncertainty']),'']
        lines += ['<details><summary>Ranking and exclusions</summary>','',readable_md(d['selection']),'</details>','']
        if 'quality' in d:
            lines += ['<details><summary>Quality rules and screening coverage</summary>','',readable_md(d['quality']),'</details>','']
        lines += ['## Dictionary','','Inferred readings are lexical and uncalibrated; meanings are human declarations or unknown.','',
                  '| Column | Meaning | Effective type / basis | Missing | Distinct |','| --- | --- | --- | --- | --- |']
        for c in d['columns']:
            meaning=c['meaning']['value']+' (human)' if c['meaning'] else 'Unknown'
            basis='human override; inferred '+c['inference']['type'] if c['override'] else 'inferred'
            lines += ['| '+ ' | '.join(md_text(x) for x in (c['name'],meaning,c['effective_type']+' / '+basis,f"{c['missing']}/{c['count']}",c['distinct']))+' |']
        lines += ['','<details><summary>Full column evidence</summary>','']
        for c in d['columns']:
            lines += ['### '+md_text(c['name']),'',readable_md({k:c[k] for k in ('observed_type','inference','override','statistics','examples','frequencies')}),'']
        lines += ['</details>','','## Provenance','',readable_md({'source':d['source'],'context':d['context'],'schema':d['schema'],'dependencies':d['dependencies']}),
                  '### Working record (human declarations)','',readable_md(d['working_record'])]
    if d.get('annotations'): lines += ['## Labelled annotations','',readable_md(d['annotations'])]
    return '\n'.join(lines).rstrip()+'\n'


def markdown_finding(f):
    return [f'<a id="{escape(f["id"],quote=True)}"></a>',md_text(f['message']),'',
            '<details><summary>Evidence and uncertainty</summary>','',readable_md({'evidence':f['evidence'],'generator':f['generator'],'uncertainty':f['uncertainty'],'provenance':f['provenance']}),'</details>','']
