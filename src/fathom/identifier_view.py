"""Readable identifier summaries and truthful in-report evidence links."""
from html import escape
from .identifiers import is_identifier
from .presentation import formatted as base_formatted,html_table,markdown_table


def formatted(value):
    return format(value,',') if type(value) is int else base_formatted(value)


IDENTIFIER_CSS=""".identifier-entry>summary h3{display:inline;margin:0;font-size:1rem}.identifier-entry .review-table{max-width:620px}.identifier-entry .num{text-align:right}.identifier-entry{margin:12px 0}.identifier-entry code{overflow-wrap:anywhere}"""


def identifier_columns(d):return [(i,c) for i,c in enumerate(d.get('columns',[])) if is_identifier(c)]


def identifier_tables(c):
    s=c.get('identifier')
    if not s:return [{'caption':'Identifier summary','headers':['State','Reason'],'numeric':[],'rows':[['Unavailable','Legacy artifact: re-profile to measure key counts and formats']]}]
    unique='unknown' if s['unique_per_row'] is None else 'yes (row-key candidate; meaning unconfirmed)' if s['unique_per_row'] else 'no'
    tables=[{'caption':'Key counts — raw labels','headers':['Measure','Value'],'numeric':[1],'rows':[[k,formatted(v)] for k,v in [('Rows',s['rows']),('Populated',s['nonmissing']),('Missing',s['missing']),('Distinct labels',s['distinct']),('Unique per row',unique),('Distinct repeated labels',s['duplicate_values']),('Rows beyond first occurrence',s['duplicate_rows']),('Rows in repeated labels',s['rows_in_repeated_values']),('Length minimum',s['length']['min']),('Length maximum',s['length']['max']),('Distinct character patterns',s['pattern_count']),('Leading zeros',s['leading_zeros']['count'])]]}]
    if s['duplicates']:tables.append({'caption':'Duplicate examples — '+s['position_basis'],'headers':['Value','Count','Positions'],'numeric':[1],'rows':[[x['value'],formatted(x['count']),', '.join(map(str,x['positions']))+(f" (+{x['omitted_positions']} omitted)" if x['omitted_positions'] else '')] for x in s['duplicates']]})
    tables.append({'caption':'Observed character patterns (variation is not invalidity)','headers':['Pattern','Rows'],'numeric':[1],'rows':[[x['pattern'],formatted(x['count'])] for x in s['patterns']]})
    n=s['numeric'];rows=[['Status',n['status']],['Basis',n['basis']]]
    if n['status']=='computed':rows.extend([['Input-row order',n['order']],['Unobserved integer labels',formatted(n['missing_integer_labels'])],['Gap ranges',formatted(n['gap_range_count'])],['Gap meaning',n['gap_basis']],['Distinct numeric readings',formatted(n['numeric_distinct'])],['Distinct raw keys',formatted(n['raw_distinct'])]])
    else:rows.append(['Reason',n['reason']])
    tables.append({'caption':'Numeric identifier reading — not missing records','headers':['Measure','Value'],'numeric':[],'rows':rows})
    if n.get('gaps'):tables.append({'caption':'Unobserved integer-label ranges; not missing records','headers':['From','To','Count'],'numeric':[0,1,2],'rows':[[g['from'],g['to'],formatted(g['count'])] for g in n['gaps']]})
    return tables


def related_links(d,index,column):
    links=[]
    for group in d.get('row_structure',{}).get('repeated_keys',[]):
        if column['name']==group['column'] or column['name'] in group.get('same_grouping',[]):
            ref=next((f['id'] for f in d.get('findings',[]) if f.get('rule')=='repeated_key' and f.get('evidence',[{}])[0].get('value',{}).get('column')==group['column']),None)
            if ref:links.append((ref,'Repeated-key structure: '+group['column']))
    for i,entry in enumerate(d.get('time_series',{}).get('series',[])):
        if entry.get('by')==column['name']:links.extend((f'ts-{i}-{j}','Declared grouping: '+str(g['group'])) for j,g in enumerate(entry['groups']))
    return links


def identifiers_html(d):
    columns=identifier_columns(d)
    if not columns:return ''
    out=['<section id="report-identifiers"><h2>Identifiers</h2><p>Raw key labels are preserved. Uniqueness may indicate a row key; repetitions may indicate entities or collisions. Confirm meaning. Numeric gaps are unobserved labels, not missing records. Identifier roles are excluded from distribution summaries and target ranking.</p>']
    for i,c in columns:
        s=c.get('identifier');basis=c.get('univariate',{}).get('role_basis','unknown')
        out.append(f'<details class="identifier-entry" id="identifier-{i}-detail"><summary><h3><a href="#dictionary-column-{i}"><code>'+escape(c['name'])+'</code></a> — '+escape(basis)+'</h3>'+(' · '+formatted(s['missing'])+' missing · '+formatted(s['duplicate_rows'])+' rows beyond first · '+formatted(s['distinct'])+' distinct' if s else ' · legacy summary unavailable')+'</summary>')
        if not basis.startswith('human'):out.append('<p><em>Identifier-like role inferred; confirm whether this is a row or entity key.</em></p>')
        out.extend(html_table(t) for t in identifier_tables(c))
        if s:out.append('<p>Leading-zero examples: <code>'+escape(', '.join(s['leading_zeros']['examples']))+'</code>. Omitted: '+str(s['omitted_duplicate_values'])+' duplicate labels, '+str(s['omitted_patterns'])+' patterns, '+str(s['numeric'].get('omitted_gap_ranges',0))+' gap ranges. '+escape(s['pattern_basis'])+'</p>')
        links=related_links(d,i,c)
        out.append('<p>'+(' · '.join('<a href="#'+escape(ref,quote=True)+'">'+escape(label)+'</a>' for ref,label in links) if links else 'No matching repeated-key structure or declared grouping in this artifact.')+'</p><p>Panel series are not declared in this profile; panel reports link their own declared series IDs.</p></details>')
    return ''.join(out)+'</section>'


def identifiers_markdown(d):
    columns=identifier_columns(d)
    if not columns:return ''
    from .report_style import markdown_text
    out=['## Identifiers','','Identifier role columns are excluded from distribution summaries and target ranking. Uniqueness/repetition does not establish row/entity meaning; numeric label gaps are not missing records.','']
    for i,c in columns:
        out+=['### '+markdown_text(c['name'],literal=True)+' — '+markdown_text(c.get('univariate',{}).get('role_basis','unknown')),'']
        out.extend(markdown_table(t) for t in identifier_tables(c));s=c.get('identifier')
        if s:out.append('Leading zeros: '+str(s['leading_zeros']['count'])+'; examples '+', '.join(markdown_text(x,literal=True) for x in s['leading_zeros']['examples']))
        out.extend('['+markdown_text(label)+'](#'+ref+')' for ref,label in related_links(d,i,c))
        out.append('Panel series are not declared in this profile; use the actual panel report for series links.')
    return '\n'.join(out)+'\n'


def panel_identifiers_html(d):
    items=d.get('identifiers',[])
    if not items:return ''
    out=['<section id="report-identifiers"><h2>Identifiers</h2><p>Declared panel series-key components; counts describe the whole input, not training-model parameters. A component can repeat within a composite series key. Gaps are unobserved labels, not missing records.</p>']
    for item in items:
        out.append('<details class="identifier-entry"><summary><code>'+escape(item['column'])+'</code> — declared series ID component</summary>')
        out.extend(html_table(t) for t in identifier_tables({'identifier':item['profile']}))
        out.append('<p>Panel series entries: '+', '.join('<a href="#panel-series-'+str(i)+'">'+escape(' · '.join(map(str,r['series'])))+'</a>' for i,r in enumerate(d['rows'][:10]))+(f" (+{len(d['rows'])-10} further entries)" if len(d['rows'])>10 else '')+'</p></details>')
    return ''.join(out)+'</section>'


def panel_identifiers_markdown(d):
    items=d.get('identifiers',[])
    if not items:return ''
    from .report_style import markdown_text
    out=['## Identifiers','','Declared panel series-key components; whole input counts, not training-model parameters. Individual components may repeat in a composite key. Numeric label gaps are not missing records.','']
    for item in items:
        out+=['### '+markdown_text(item['column'],literal=True),'']+[markdown_table(t) for t in identifier_tables({'identifier':item['profile']})]
        out += ['Panel series entries: '+', '.join('[entry '+str(i+1)+'](#panel-series-'+str(i)+')' for i in range(min(10,len(d['rows']))))]
    return '\n'.join(out)+'\n'
