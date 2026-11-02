"""Person-first offline views, derived solely from the saved result."""

from collections import Counter
from html import escape
import re

from .models import ProfilingResult
from .charts import svg_chart
from .presentation import formatted, column_tables, html_table, markdown_table, metric_table, structured_tables
from pathlib import Path

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
    return [(title,formatted(value),s.get('finding_links',{}).get(key,[])) for key,title,value in items]


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
        if rule is None or rule in {'dataset_summary','selected_relation','conditional_missingness'} or (f.get('columns') and len(f['columns'])!=1):
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


def sample_cell(value):
    if value is None:return '[missing; original lexeme unavailable]'
    if value=='':return '[empty string]'
    if not value.strip():return repr(value)+' [whitespace]'
    return value


def samples_html(d):
    samples=d.get('samples')
    if not samples:return '<p>Sample rows unavailable in this saved artifact.</p>'
    out=['<p>'+escape(samples['note'])+' Seed: '+str(samples['seed'])+'; requested rows per view: '+str(samples['size'])+'.</p>']
    for key,title in [('first','First rows'),('last','Last rows'),('random','Random rows')]:
        out += ['<details><summary>'+title+'</summary><div class="sample-scroll"><table><thead><tr><th>Input row</th>']
        out += ['<th>'+escape(name)+'</th>' for name in samples['columns']]
        out += ['</tr></thead><tbody>']
        for row in samples[key]:out.append('<tr><td>'+str(row['position'])+'</td>'+''.join('<td>'+escape(sample_cell(v))+'</td>' for v in row['values'])+'</tr>')
        out += ['</tbody></table></div></details>']
    return ''.join(out)


def samples_markdown(d):
    samples=d.get('samples')
    if not samples:return 'Sample rows unavailable in this saved artifact.\n'
    lines=[samples['note']+f" Seed: {samples['seed']}; requested rows per view: {samples['size']}",'']
    for key,title in [('first','First rows'),('last','Last rows'),('random','Random rows')]:
        lines += ['<details><summary>'+title+'</summary>','', '| Input row | '+' | '.join(md_text(x) for x in samples['columns'])+' |','| '+' | '.join('---' for _ in range(len(samples['columns'])+1))+' |']
        for row in samples[key]:lines.append('| '+str(row['position'])+' | '+' | '.join(md_text(sample_cell(v)) for v in row['values'])+' |')
        lines += ['','</details>','']
    return '\n'.join(lines)


def charts_markdown(col):
    return '\n'.join(markdown_table(t) for t in column_tables(col))+'\n'+'\n'.join(svg_chart(ch) for ch in col.get('univariate',{}).get('charts',[]))


def bars(items, title):
    return svg_chart({'kind':'bar','title':title,'x_label':'Missing cells (count)' if 'Missing' in title else 'Rows (count)',
                      'y_label':'Column' if 'column' in title else 'Value','data':[{'label':k,'count':v} for k,v in items]}) if items else ''


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


def dictionary_and_provenance_html(d):
    out=['<section><h2>Dictionary</h2><p>Inferred readings are lexical and uncalibrated; meanings are human declarations or unknown.</p><p>Charts use a fixed drawing area: pan horizontally if needed. Exact plotted values are available below each chart.</p>',
         bars([(c['name'],c['missing']) for c in d['columns'][:20]],'Missing cells by column (first 20)')]
    masks=d.get('missingness_patterns')
    if masks:
        out += [svg_chart(masks['chart']),'<p>'+escape(masks['basis'])+' '+str(masks['omitted_patterns'])+' patterns / '+str(masks['omitted_rows'])+' rows omitted; '+str(masks['omitted_columns'])+' columns beyond the display limit.</p>']
        out += [html_table({'caption':'Exact row masks — share of all rows','headers':['Pattern / missing columns','Count','Share'],'numeric':[1,2],
                            'rows':[['P'+str(i+1)+': '+(', '.join(p['missing']) or 'Complete rows'),formatted(p['count']),formatted(p['share'],True)] for i,p in enumerate(masks['patterns'])]})]
    out += [samples_html(d)]
    for c in d['columns']:
        meaning=c['meaning']['value']+' (human)' if c['meaning'] else 'Unknown meaning'
        basis='human override; inferred '+c['inference']['type'] if c['override'] else 'inferred, not a domain fact'
        out += ['<article class="column-entry"><h3>'+escape(c['name'])+'</h3><p>'+escape(meaning)+' · '+escape(c['effective_type'])+' ('+escape(basis)+')</p>',
                '<p>Examples: '+escape(', '.join(v[:120]+('… [truncated]' if len(v)>120 else '') for v in c['examples']))+'</p>']
        tables=column_tables(c)
        primary=[t for t in tables if t['caption'].startswith(('Column overview','Univariate statistics','Percentiles','Most common nonmissing'))]
        extra=[t for t in tables if t not in primary]
        out += [html_table(t) for t in primary[:1]]
        out += [svg_chart(ch) for ch in c.get('univariate',{}).get('charts',[])]
        out += [html_table(t) for t in primary[1:]]
        if extra:out += ['<details><summary>Additional statistics</summary>',''.join(html_table(t) for t in extra),'</details>']
        out += ['<details><summary>Raw evidence</summary>'+readable_html(c)+'</details></article>']
    out += ['</section><section><h2>Provenance</h2><p>Source and context are recorded; expand for technical detail.</p><details><summary>Provenance internals</summary>',readable_html({'source':d['source'],'context':d['context'],'schema':d['schema'],'dependencies':d['dependencies'],'identity_basis':d.get('dataset',{}).get('basis',{})}),
            '<h3>Working record (human declarations)</h3>',readable_html(d['working_record']),'</details></section>']
    return ''.join(out)


def render_html(result: ProfilingResult):
    d=result.document
    identity=d.get('dataset',{})
    title=identity.get('title',{}).get('text',Path(d.get('source',{}).get('origin','Fathom')).stem)
    out=['<h1>'+escape(title)+'</h1>']
    if identity:out += ['<p>'+escape(identity['description']['text'])+'</p><p><small>Title: '+escape(identity['title']['status'])+' · description: '+escape(identity['description']['status'])+'</small></p>']
    if d['kind']=='comparison':
        for title,value in [('Contexts',d['contexts']),('Context differences',d['context_differences']),('Measured deltas',d['deltas']),('Limitations',d['limitations'])]:
            out += ['<section><h2>'+title+'</h2>',''.join(html_table(t) for t in structured_tables(title,value)),'</section>']
    else:
        out += [dictionary_and_provenance_html(d)]
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
                    ''.join(html_table(t) for t in structured_tables('Relationship statistics',pair['statistics'])),'<p>'+escape(pair['uncertainty'])+'</p></article>']
        out += ['<details><summary>Ranking and exclusions</summary>',readable_html(d['selection']),'</details>']
        if 'quality' in d:
            out += ['<details><summary>Quality rules and screening coverage</summary>',readable_html(d['quality']),'</details>']
        out += ['</section>']
    if d.get('annotations'):
        out += ['<section><h2>Labelled annotations</h2>',readable_html(d['annotations']),'</section>']
    css='''body{font:16px/1.55 system-ui,sans-serif;background:#f5f8f7;color:#193e42;max-width:1120px;padding:32px;margin:auto}h1{font-size:44px;margin-bottom:8px}h2{border-bottom:2px solid #28777c;padding-bottom:7px;margin-top:40px}h3{margin-top:24px}section{margin-bottom:30px}.opening{background:white;padding:24px;border:1px solid #d5e1df;border-radius:8px}table{border-collapse:collapse;width:100%;background:white}td,th{padding:10px;text-align:left;border-bottom:1px solid #d5e1df;vertical-align:top}td{overflow-wrap:anywhere}article{background:white;border-left:3px solid #b9d3cf;padding:8px 16px;margin:10px 0}article>p{margin:7px 0}details{margin:8px 0}summary{cursor:pointer;color:#12656b;font-weight:600}details[open]{padding-bottom:10px}a{color:#12656b}small{color:#4d676b}dt{font-weight:600;margin-top:8px}dd{margin-left:20px;overflow-wrap:anywhere}ul{padding-left:24px}.sample-scroll{overflow-x:auto}.sample-scroll td{min-width:90px;max-width:260px;white-space:pre-wrap}svg{width:100%;max-width:800px}svg text{font:13px system-ui,sans-serif}label{cursor:pointer;font-weight:600;margin-left:8px}.summary-view{background:#e9f2ee;padding:12px;margin-top:12px}.repetitive{display:none}.repetitive:target{display:block}#full-view:checked ~ .summary-view{display:none}#full-view:checked ~ .full-view .summary-view{display:none}#full-view:checked ~ .full-view .repetitive{display:block}@media(max-width:700px){body{padding:12px}td,th{padding:6px;font-size:14px}.opening{padding:12px}}@media print{body{background:white;padding:0}details{break-inside:avoid}.repetitive{display:block}}'''
    css += '.column-entry{box-sizing:border-box;width:100%;border:1px solid #d5e1df;border-radius:6px;padding:20px;margin:24px 0}.column-entry h3{margin-top:0;overflow-wrap:anywhere}.review-table{table-layout:fixed;margin:12px 0 20px}.review-table td,.review-table th{padding:6px 10px}caption{text-align:left;font-weight:600;padding:8px 0}.num{text-align:right;font-variant-numeric:tabular-nums}.table-scroll{overflow-x:auto;max-width:100%}.chart{margin:20px 0;max-width:100%;overflow-x:auto}.chart svg{width:720px;max-width:none;display:block}.chart svg text{font:15px system-ui,sans-serif}.chart-title{font-weight:600}figcaption{font-size:14px;margin:8px 0;color:#4d676b}p{overflow-wrap:anywhere}'
    return '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fathom — '+escape(d['kind'])+'</title><style>'+css+'</style></head><body>'+'\n'.join(out)+'</body></html>\n'


def dictionary_and_provenance_markdown(d):
    lines=['## Dictionary','','Inferred readings are lexical and uncalibrated; meanings are human declarations or unknown.','',samples_markdown(d)]
    if d.get('missingness_patterns'):lines += [svg_chart(d['missingness_patterns']['chart'])]
    for c in d['columns']:
        meaning=c['meaning']['value']+' (human)' if c['meaning'] else 'Unknown meaning'
        lines += ['### '+md_text(c['name']),'',md_text(meaning+'; effective '+c['effective_type']+(' (human override)' if c['override'] else ' (inferred)')),'',charts_markdown(c),'',
                  '<details><summary>Raw evidence</summary>','',readable_md(c),'</details>','']
    lines += ['## Provenance','','Source and context are recorded; technical details are collapsed.','','<details><summary>Provenance internals</summary>','',readable_md({'source':d['source'],'context':d['context'],'schema':d['schema'],'dependencies':d['dependencies'],'identity_basis':d.get('dataset',{}).get('basis',{})}),
              '### Working record (human declarations)','',readable_md(d['working_record']),'</details>','']
    return lines


def render_markdown(result: ProfilingResult):
    d=result.document
    identity=d.get('dataset',{})
    lines=['# '+md_text(identity.get('title',{}).get('text','Fathom — '+d['kind'])),'']
    if identity:lines += [md_text(identity['description']['text']),'', 'Title: '+identity['title']['status']+'; description: '+identity['description']['status']+'.','']
    if d['kind']=='comparison':
        for title,value in [('Contexts',d['contexts']),('Context differences',d['context_differences']),('Measured deltas',d['deltas']),('Limitations',d['limitations'])]:
            lines += ['## '+title,'','\n'.join(markdown_table(t) for t in structured_tables(title,value)),'']
    else:
        lines += dictionary_and_provenance_markdown(d)
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
            lines += ['### '+md_text(pair['left'])+' × '+md_text(pair['right']),'',md_text(pair['method']+' · '+pair['semantics']),'','\n'.join(markdown_table(t) for t in structured_tables('Relationship statistics',pair['statistics'])),md_text(pair['uncertainty']),'']
        lines += ['<details><summary>Ranking and exclusions</summary>','',readable_md(d['selection']),'</details>','']
        if 'quality' in d:
            lines += ['<details><summary>Quality rules and screening coverage</summary>','',readable_md(d['quality']),'</details>','']
    if d.get('annotations'): lines += ['## Labelled annotations','',readable_md(d['annotations'])]
    return '\n'.join(lines).rstrip()+'\n'


def markdown_finding(f):
    return [f'<a id="{escape(f["id"],quote=True)}"></a>',md_text(f['message']),'',
            '<details><summary>Evidence and uncertainty</summary>','',readable_md({'evidence':f['evidence'],'generator':f['generator'],'uncertainty':f['uncertainty'],'provenance':f['provenance']}),'</details>','']
