"""Person-first offline views, derived solely from the saved result."""

from collections import Counter
import json
from html import escape
import re

from .models import ProfilingResult,canonical_json
from .charts import svg_chart
from .palette import THEMES, KIND_COLOURS, theme_css
from .target import target_tables
from .temporal_view import temporal_html, temporal_markdown, TEMPORAL_CSS
from .presentation import formatted, column_tables, html_table, markdown_table, metric_table, structured_tables, formatted_examples, display_charts, top_n_reason, categorical_hint
from pathlib import Path
from .verdicts import headlines_html, key_findings, skew_text, inline_rule
from .report_style import style_html, STYLE_CSS, NAV_SCRIPT, navigation, markdown_text

KINDS = (("observation", "Observations"), ("interpretation", "Interpretations"),
         ("hypothesis", "Hypotheses"), ("action", "Suggested actions"), ("question", "Open questions"))
PALETTE = {"themes": THEMES, "kinds": KIND_COLOURS}  # the recorded palette; values live in fathom.palette
KIND_CSS = ('.kind-tag{display:inline-block;font-size:12px;line-height:1.5;font-weight:700;letter-spacing:.04em;text-transform:uppercase;'
            'padding:0 8px;margin-right:8px;border:1px solid currentColor;border-radius:999px;background:var(--panel);vertical-align:1px}'
            + ''.join(f'.kind-{k} .kind-tag,.kind-heading.kind-{k}{{color:var(--kind-{k})}}article.kind-{k}{{border-left-color:var(--kind-{k})}}' for k, _ in KINDS))


def md_text(value, **context):
    return markdown_text(value, **context)


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
        return ('<ul>'+''.join('<li>'+readable_html(v)+'</li>' for v in value)+'</ul>' if len(value)>=3 else ''.join('<div>'+readable_html(v)+'</div>' for v in value)) if value else 'None recorded'
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
    return formatted(measure['count'])+'/'+formatted(total) + (f" ({rate:.1%})" if rate is not None else ' (share unavailable)')


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


DATETIME_NOTE='analysed by calendar date only; time of day excluded'


def hourly_columns(d):
    ts=(d or {}).get('time_series',{})
    names={e['time'] for e in ts.get('declared',[]) if 'hour' in e.get('granularities',[])}
    names.update(e['time'] for e in ts.get('series',[]) if any(g['granularity']=='hour' for s in e.get('groups',[]) for g in s.get('granularities',[])))
    return names


def datetime_note(c, d=None):
    """Scope the date-only dictionary summary separately from declared hourly work."""
    formats=(c.get('univariate') or {}).get('statistics',{}).get('parse_formats') or {}
    if c.get('effective_type')!='temporal' or 'ISO_DATETIME' not in formats:return ''
    hours=hourly_columns(d)
    if c['name'] in hours:return 'univariate summaries use calendar dates; declared hourly series retains time of day'
    if hours:return 'univariate calendar-date summary; time-of-day analyses are separate declarations'
    return DATETIME_NOTE


def omitted(d):
    """Keys of optional sections omitted by configuration (spec012); legacy artifacts omit none."""
    return {s['key'] for s in (d.get('report') or {}).get('omitted_sections', [])}


def omitted_notes(d):
    return [f"{s['title']} section omitted by configuration (sections.{s['key']}: false); the saved artifact still holds it."
            for s in (d.get('report') or {}).get('omitted_sections', [])]


def bins_note(d):
    rule = (d.get('report') or {}).get('bin_rule')
    return f'Histogram bins: {rule}.' if rule else ''


def unknowns(d):
    questions = [f['message'] for f in d['findings'] if f['id'].startswith('unknown-')]
    result = (questions or ['Recorded context is supplied by humans; the table does not independently establish domain meaning, causation or fitness for use.']) + omitted_notes(d)
    dated = [c['name'] for c in d.get('columns', []) if datetime_note(c,d)==DATETIME_NOTE]
    if dated:
        result = result + [f"Date-time columns ({', '.join(dated)}) are {DATETIME_NOTE}."]
    return result


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
    return '\n'.join(markdown_table(t) for t in column_tables(col))+'\n'+'\n'.join(svg_chart(ch) for ch in display_charts(col))


def bars(items, title):
    return svg_chart({'kind':'bar','title':title,'x_label':'Missing cells (count)' if 'Missing' in title else 'Rows (count)',
                      'y_label':'Column' if 'column' in title else 'Value','data':[{'label':k,'count':v} for k,v in items]}) if items else ''


def kind_tag(kind):
    return '<span class="kind-tag">'+escape(kind.capitalize())+'</span>'


def finding_html(f, repeated_ids, context=None):
    fid=escape(f['id'],quote=True)
    cls=('finding repetitive' if repetitive(f,repeated_ids) else 'finding')+' kind-'+escape(f['kind'],quote=True)
    out=[f'<article id="{fid}" class="{cls}"><p>{kind_tag(f["kind"])}{escape(f["message"])}</p>']
    gate=inline_rule(f)
    if gate:out.append('<p class="gate">Gate: '+escape(gate)+'</p>')
    out.append('<details><summary>Evidence and uncertainty</summary>')
    if context:out.append('<p>'+escape(context)+'</p>')
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
    out=['<section id="report-dictionary"><h2>Dictionary</h2><p>Inferred readings are lexical and uncalibrated; meanings are human declarations or unknown.</p><p>Column details start collapsed. Expand a column to inspect its statistics and scaled plots. Exact plotted values remain available.</p>'+('<p>'+escape(bins_note(d))+'</p>' if bins_note(d) else ''),
         bars([(c['name'],c['missing']) for c in d['columns'][:20]],'Missing cells by column (first 20)')]
    masks=d.get('missingness_patterns') if 'missingness_patterns' not in omitted(d) else None
    if masks:
        out += [svg_chart(masks['chart']),'<p>'+escape(masks['basis'])+' '+str(masks['omitted_patterns'])+' patterns / '+str(masks['omitted_rows'])+' rows omitted; '+str(masks['omitted_columns'])+' columns beyond the display limit.</p>']
        out += ['<details><summary>Exact pattern table — counts and shares</summary>',html_table({'caption':'Exact row masks — share of all rows','headers':['Pattern / missing columns','Count','Share'],'numeric':[1,2],
                            'rows':[['P'+str(i+1)+': '+(', '.join(p['missing']) or 'Complete rows'),formatted(p['count']),formatted(p['share'],True)] for i,p in enumerate(masks['patterns'])]}),'</details>']
    if 'samples' not in omitted(d):out += [samples_html(d)]
    for c in d['columns']:
        meaning=c['meaning']['value']+' (human)' if c['meaning'] else 'Unknown meaning'
        basis='human override; inferred '+c['inference']['type'] if c['override'] else 'inferred, not a domain fact'
        out += ['<details class="column-entry"><summary><h3>'+escape(c['name'])+'</h3> <span>'+escape(c['effective_type'])+' · '+formatted(c['missing'])+'/'+formatted(c['count'])+' missing · '+formatted(c['distinct'])+' distinct'+(' · '+datetime_note(c,d) if datetime_note(c,d) else '')+'</span></summary><p>'+escape(meaning)+' ('+escape(basis)+')</p>',
                '<p>Examples: '+escape(', '.join(formatted_examples(c)))+'</p><div class="column-grid"><div class="column-statistics">']
        gate=d.get('quality',{}).get('skew_gates',{}).get(c['name'])
        if gate:out.insert(len(out)-1,'<p>'+escape(skew_text(gate))+'</p>')
        if categorical_hint(c):out.append('<p>'+escape(categorical_hint(c))+'</p>')
        tables=column_tables(c)
        primary=[t for t in tables if t['caption'].startswith(('Column overview','Univariate statistics','Percentiles','Most common nonmissing'))]
        extra=[t for t in tables if t not in primary]
        out += [html_table(t) for t in primary[:1]]
        out += ['</div><div class="column-plots">']
        if top_n_reason(c):out += ['<p>'+escape(top_n_reason(c))+'</p>']
        out += [svg_chart(ch) for ch in display_charts(c)]
        out += ['</div></div>']
        extra=primary[1:]+extra
        if extra:out += ['<details><summary>Additional statistics</summary>',''.join(html_table(t) for t in extra),'</details>']
        out += ['<details class="raw-evidence"><summary>Raw evidence</summary>'+readable_html(c)+'</details></details>']
    out += ['</section><section id="report-provenance"><h2>Provenance</h2><p>Source and context are recorded; expand for technical detail.</p><details><summary>Provenance internals</summary>',readable_html({'source':d['source'],'context':d['context'],'schema':d['schema'],'dependencies':d['dependencies'],'identity_basis':d.get('dataset',{}).get('basis',{})}),
            '<h3>Working record (human declarations)</h3>',readable_html(d['working_record']),'</details></section>']
    return ''.join(out)


def render_html(result: ProfilingResult):
    if result.document['kind'] == 'panel':
        from .panel_view import html
        return html(result)
    d=json.loads(canonical_json(result.document))
    identity=d.get('dataset',{})
    title=identity.get('title',{}).get('text',Path(d.get('source',{}).get('origin','Fathom')).stem)
    out=['<h1'+(' class="inferred-reading"' if identity.get('title',{}).get('status')=='inferred' else '')+'>'+escape(title)+'</h1>']
    if identity:out += ['<p'+(' class="inferred-reading"' if identity['description']['status']=='inferred' else '')+'>'+escape(identity['description']['text'])+'</p><p><small>Title: '+escape(identity['title']['status'])+' · description: '+escape(identity['description']['status'])+'</small></p>']
    if d['kind']=='comparison':
        for title,value in [('Contexts',d['contexts']),('Context differences',d['context_differences']),('Measured deltas',d['deltas']),('Limitations',d['limitations'])]:
            out += ['<section><h2>'+title+'</h2>',''.join(html_table(t) for t in structured_tables(title,value)),'</section>']
    else:
        items=[('key-findings','Key findings',len(key_findings(d))),('report-dataset','Dataset',None),('report-dictionary','Dictionary',len(d['columns'])),('findings','Findings',len(d['findings'])),('report-relations','Relations',len(d['bivariate']))]
        if d.get('time_series',{}).get('series'):items.append(('temporal-structure','Temporal',len(d['time_series']['series'])))
        if d.get('target_analysis'):items.append(('report-target','Target',len(d['target_analysis'].get('ranked',[]))))
        items.extend([('report-exclusions','Exclusions',len(d['selection'].get('excluded',[]))),('report-provenance','Provenance',None)])
        out += [navigation(items),headlines_html(d),dictionary_and_provenance_html(d)]
        out += ['<section id="report-dataset" class="opening"><h2>Dataset summary</h2><table><thead><tr><th>Measure</th><th>Snapshot</th><th>Evidence</th></tr></thead><tbody>']
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
            out.append(f'<h3 class="kind-heading kind-{kind}">'+title+'</h3>')
            for message,items in summaries:
                if not items or items[0]['kind']!=kind: continue
                links=''.join('<p><a href="#'+escape(f['id'],quote=True)+'">Original item</a>: '+escape(f['message'])+'</p>'+readable_html({'evidence':f['evidence'],'generator':f['generator'],'uncertainty':f['uncertainty'],'provenance':f['provenance']}) for f in items)
                out.append(f'<div class="summary-view"><p class="kind-{kind}">'+kind_tag(kind)+escape(message)+'</p><details><summary>Evidence, uncertainty and original items</summary>'+links+'</details></div>')
            fs=[f for f in d['findings'] if f['kind']==kind]
            out.extend(finding_html(f,repeated_ids) for f in fs)
            if not fs: out.append('<p>None recorded.</p>')
        out += ['</div></section>',temporal_html(d)]
        out += ['<section id="report-relations"><h2>Relations</h2><p>'+escape(d['selection'].get('ranking_rule','Legacy input-order selection; no relevance ranking recorded.'))+'</p>',
                '<p>Selected '+str(len(d['bivariate']))+' relationship(s); budget '+str(d['selection']['budget'])+'.</p>']
        ta=d.get('target_analysis')
        out += ['<p>'+escape(ta['reason']+' '+ta['grouping_policy']+' '+ta['warning'] if ta else 'Target detail unavailable in legacy artifact; rerun profiling to compute it.')+'</p>']
        out += ['<div id="report-target" class="target-tables"><h3>Target</h3><p>Wide target tables scroll horizontally on narrow screens.</p>']+[html_table(t) for t in target_tables(d)]+['</div>']
        if ta:out += [svg_chart(ch) for ch in ta['charts']]
        if ta:out += ['<details><summary>Selected pair statistics and method details</summary>']
        for pair in d['bivariate']:
            out += ['<article><h3>'+escape(pair['left'])+' × '+escape(pair['right'])+'</h3><p>'+escape(pair['method'])+' · '+escape(pair['semantics'])+'</p>',
                    ''.join(html_table(t) for t in structured_tables('Relationship statistics',pair['statistics'])),'<p>'+escape(pair['uncertainty'])+'</p></article>']
        if ta:out += ['</details>']
        out += ['<details id="report-exclusions"><summary>Ranking and exclusions</summary>',readable_html(d['selection']),'</details>']
        if 'quality' in d:
            out += ['<details><summary>Quality rules and screening coverage</summary>',readable_html(d['quality']),'</details>']
        out += ['</section>']
    if d.get('annotations'):
        out += ['<section><h2>Labelled annotations</h2>',readable_html(d['annotations']),'</section>']
    css=theme_css()+KIND_CSS+TEMPORAL_CSS+'''body{font:16px/1.55 system-ui,sans-serif;background:var(--surface);color:var(--ink);max-width:1120px;padding:32px;margin:auto}h1{font-size:44px;margin-bottom:8px}h2{border-bottom:2px solid var(--rule);padding-bottom:7px;margin-top:40px}h3{margin-top:24px}section{margin-bottom:30px}.opening{background:var(--panel);padding:24px;border:1px solid var(--border);border-radius:8px}table{border-collapse:collapse;width:100%;background:var(--panel)}td,th{padding:10px;text-align:left;border-bottom:1px solid var(--border);vertical-align:top}td{overflow-wrap:anywhere}article{background:var(--panel);border-left:3px solid var(--soft-border);padding:8px 16px;margin:10px 0}article>p{margin:7px 0}details{margin:8px 0}summary{cursor:pointer;color:var(--link);font-weight:600}details[open]{padding-bottom:10px}a{color:var(--link)}small{color:var(--muted)}dt{font-weight:600;margin-top:8px}dd{margin-left:20px;overflow-wrap:anywhere}ul{padding-left:24px}.sample-scroll{overflow-x:auto}.sample-scroll td{min-width:90px;max-width:260px;white-space:pre-wrap}svg{width:100%;max-width:800px}svg text{font:13px system-ui,sans-serif}label{cursor:pointer;font-weight:600;margin-left:8px}.summary-view{background:var(--tint);padding:12px;margin-top:12px}.repetitive{display:none}.repetitive:target{display:block}#full-view:checked ~ .summary-view{display:none}#full-view:checked ~ .full-view .summary-view{display:none}#full-view:checked ~ .full-view .repetitive{display:block}@media(max-width:700px){body{padding:12px}td,th{padding:6px;font-size:14px}.opening{padding:12px}}@media print{body{background:var(--panel);padding:0}details{break-inside:avoid}.repetitive{display:block}}'''
    css += '.column-entry{box-sizing:border-box;width:100%;border:1px solid var(--border);border-radius:6px;padding:20px;margin:24px 0}.column-entry h3{margin-top:0;overflow-wrap:anywhere}.review-table{table-layout:fixed;margin:12px 0 20px}.review-table td,.review-table th{padding:6px 10px}caption{text-align:left;font-weight:600;padding:8px 0}.num{text-align:right;font-variant-numeric:tabular-nums}.table-scroll{overflow-x:auto;max-width:100%}.chart{margin:20px 0;max-width:100%;overflow-x:auto}.chart svg{width:720px;max-width:none;display:block}.chart svg text{font:15px system-ui,sans-serif}.chart-title{font-weight:600}figcaption{font-size:14px;margin:8px 0;color:var(--muted)}p{overflow-wrap:anywhere}'
    css += '.target-chart .review-table{max-width:none;min-width:680px;table-layout:auto}.target-chart .review-table .num{white-space:nowrap}.target-tables td{white-space:pre-line}.target-tables .review-table{max-width:none;min-width:640px;table-layout:auto}.column-entry{padding:12px 16px;margin:10px 0}.column-entry>summary{display:list-item}.column-entry>summary h3{display:inline;margin:0 16px 0 0;font-size:18px}.column-entry>summary span{font-size:14px;font-weight:400;color:var(--muted)}.column-grid{display:grid;grid-template-columns:minmax(230px,.75fr) minmax(0,1.25fr);gap:24px;align-items:start}.column-statistics{min-width:0;max-width:360px;position:sticky;top:12px;max-height:65vh;overflow-y:auto}.column-plots{min-width:0}.review-table{max-width:420px}.chart{max-width:760px}.chart svg{width:100%;max-width:100%;height:auto}.chart svg text{font:18px system-ui,sans-serif}.chart h4{font-size:16px;margin:8px 0}.axis-captions p{margin:3px 0;font-size:14px;overflow-wrap:anywhere}.box-summary{max-width:320px}.chart{overflow:visible;margin:10px 0 20px}.column-entry .table-scroll{max-width:100%}@media(max-width:800px){.column-grid{grid-template-columns:minmax(0,1fr)}.column-entry{padding:10px}.column-statistics{max-width:100%;position:static;max-height:none;overflow:visible}}@media(max-width:500px){.chart svg text{font-size:22px}}'
    return style_html('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fathom — '+escape(d['kind'])+'</title><style>'+css+STYLE_CSS+'</style></head><body>'+'\n'.join(out)+NAV_SCRIPT+'</body></html>\n', columns=[c['name'] for c in d.get('columns',[])])


def dictionary_and_provenance_markdown(d):
    lines=['## Dictionary','','Inferred readings are lexical and uncalibrated; meanings are human declarations or unknown.','']
    if bins_note(d):lines += [md_text(bins_note(d)),'']
    if 'samples' not in omitted(d):lines += [samples_markdown(d)]
    if d.get('missingness_patterns') and 'missingness_patterns' not in omitted(d):lines += [svg_chart(d['missingness_patterns']['chart'])]
    for c in d['columns']:
        meaning=c['meaning']['value']+' (human)' if c['meaning'] else 'Unknown meaning'
        lines += ['### '+markdown_text(c['name'],literal=True),'',md_text(meaning+'; effective '+c['effective_type']+(' (human override)' if c['override'] else ' (inferred)')+('; '+datetime_note(c,d) if datetime_note(c,d) else '')),'','Examples: '+markdown_text(', '.join(formatted_examples(c)),literal=True),'',md_text(categorical_hint(c)),'',charts_markdown(c),'',
                  md_text(skew_text(d.get('quality',{}).get('skew_gates',{}).get(c['name'])),verdict=True,columns=[c['name']]) if c['effective_type']=='numeric' else '', '<details class="raw-evidence"><summary>Raw evidence</summary>','',readable_md(c),'</details>','']
    lines += ['## Provenance','','Source and context are recorded; technical details are collapsed.','','<details><summary>Provenance internals</summary>','',readable_md({'source':d['source'],'context':d['context'],'schema':d['schema'],'dependencies':d['dependencies'],'identity_basis':d.get('dataset',{}).get('basis',{})}),
              '### Working record (human declarations)','',readable_md(d['working_record']),'</details>','']
    return lines


def render_markdown(result: ProfilingResult):
    if result.document['kind'] == 'panel':
        from .panel_view import markdown
        return markdown(result)
    d=json.loads(canonical_json(result.document))
    identity=d.get('dataset',{})
    lines=['# '+md_text(identity.get('title',{}).get('text','Fathom — '+d['kind']),inferred=identity.get('title',{}).get('status')=='inferred'),'']
    if identity:lines += [markdown_text(identity['description']['text'],inferred=identity['description']['status']=='inferred'),'', 'Title: '+identity['title']['status']+'; description: '+identity['description']['status']+'.','']
    if d['kind']=='comparison':
        for title,value in [('Contexts',d['contexts']),('Context differences',d['context_differences']),('Measured deltas',d['deltas']),('Limitations',d['limitations'])]:
            lines += ['## '+title,'','\n'.join(markdown_table(t) for t in structured_tables(title,value)),'']
    else:
        items=key_findings(d)
        lines += ['## Key findings','']+[(('- ' if len(items)>=3 else '')+markdown_text(i['message'],columns=[c['name'] for c in d['columns']],verdict=True)+'\n') for i in items]+['']
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
                if items and items[0]['kind']==kind: lines += [md_text(message,verdict=True,inferred=kind in {'hypothesis','interpretation'}),'']
            fs=[f for f in d['findings'] if f['kind']==kind and not repetitive(f,repeated_ids)]
            for f in fs: lines += markdown_finding(f)
            if not fs: lines += ['No additional items recorded.','']
        if repeated:
            lines += ['<details><summary>Full repetitive per-column findings</summary>','']
            for f in repeated: lines += markdown_finding(f)
            lines += ['</details>','']
        lines += temporal_markdown(d)
        lines += ['## Relations','',md_text(d['selection'].get('ranking_rule','Legacy input-order selection; no relevance ranking recorded.')),'',
                  f"Selected {len(d['bivariate'])} relationship(s); budget {d['selection']['budget']}.",'']
        ta=d.get('target_analysis')
        lines += [md_text(ta['reason']+' '+ta['grouping_policy']+' '+ta['warning'] if ta else 'Target detail unavailable in legacy artifact.'),'']
        lines += [markdown_table(t) for t in target_tables(d)]
        if ta:lines += [svg_chart(ch) for ch in ta['charts']]
        for pair in d['bivariate']:
            lines += ['### '+md_text(pair['left'])+' × '+md_text(pair['right']),'',md_text(pair['method']+' · '+pair['semantics']),'','\n'.join(markdown_table(t) for t in structured_tables('Relationship statistics',pair['statistics'])),md_text(pair['uncertainty']),'']
        lines += ['<details id="report-exclusions"><summary>Ranking and exclusions</summary>','',readable_md(d['selection']),'</details>','']
        if 'quality' in d:
            lines += ['<details><summary>Quality rules and screening coverage</summary>','',readable_md(d['quality']),'</details>','']
    if d.get('annotations'): lines += ['## Labelled annotations','',readable_md(d['annotations'])]
    return '\n'.join(lines).rstrip()+'\n'


def markdown_finding(f):
    return [f'<a id="{escape(f["id"],quote=True)}"></a>',md_text(f['message'],columns=f.get('columns',[]),verdict=True,inferred=f['kind'] in {'hypothesis','interpretation'}),'',md_text('Gate: '+inline_rule(f),verdict=True,columns=f.get('columns',[])) if inline_rule(f) else '',
            '<details><summary>Evidence and uncertainty</summary>','',readable_md({'evidence':f['evidence'],'generator':f['generator'],'uncertainty':f['uncertainty'],'provenance':f['provenance']}),'</details>','']
