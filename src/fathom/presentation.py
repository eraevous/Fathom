"""Readable tables derived from saved measurements; raw evidence stays separate."""

from html import escape
import re


def formatted(value, share=False):
    if value is None:return 'Unavailable'
    if isinstance(value,bool):return 'Yes' if value else 'No'
    if isinstance(value,(float,int)):
        if share:return f'{value:.1%}'
        if value==0:return '0'
        if abs(value)>=1e12 or abs(value)<.001:return f'{value:.3g}'
        return f'{value:,.3f}'.rstrip('0').rstrip('.') if isinstance(value,float) else f'{value:,}'
    return str(value)


def structured_tables(caption,value):
    """Tabulate saved context/relationship measures without nested key/value UI."""
    if isinstance(value,dict):
        flat={k:v for k,v in value.items() if not isinstance(v,(dict,list,tuple))}
        tables=[metric_table(caption,flat)] if flat else []
        for k in sorted(value):
            if isinstance(value[k],(dict,list,tuple)):tables+=structured_tables(caption+' / '+title(k),value[k])
        return tables
    if isinstance(value,(list,tuple)):
        if value and all(isinstance(v,dict) and all(not isinstance(x,(dict,list,tuple)) for x in v.values()) for v in value):
            keys=sorted({k for v in value for k in v});numeric=[i for i,k in enumerate(keys) if all(v.get(k) is None or isinstance(v.get(k),(int,float)) for v in value)]
            return [{'caption':caption,'headers':[title(k) for k in keys],'numeric':numeric,'rows':[[formatted(v.get(k),k in {'share','rate','spread'}) for k in keys] for v in value]}]
        tables=[]
        for i,v in enumerate(value):tables+=structured_tables(caption+' / '+str(i+1),v)
        return tables
    return [metric_table(caption,{'value':value})]


def title(key):return str(key).replace('_',' ').capitalize()


def metric_table(caption,values,units=None):
    rows=[]
    for key in sorted(values,key=lambda k:(0,float(k)) if str(k).isdigit() else (1,str(k))):
        value=values[key]
        if isinstance(value,(dict,list)):continue
        rows.append([title(key),formatted(value, key=='share' or key.endswith('_share'))])
    return {'caption':caption+(' — '+units if units else ''),'headers':['Measure','Value'],'rows':rows,'numeric':[1]}


def frequency_table(caption,items,denominator):
    return {'caption':caption+(f' — share of {denominator:,} values' if denominator is not None else ' — share denominator unavailable'),
            'headers':['Value','Count','Share'],'numeric':[1,2],
            'rows':[[str(x['value']) if x['value']!='' else '[empty string]',formatted(x['count']),formatted(x['count']/denominator,True) if denominator else 'Unavailable'] for x in items]}


def column_tables(col):
    u=col.get('univariate',{});s=u.get('statistics',{});unit=u.get('units')
    unit=(unit['value']+' (human)') if unit else 'units unknown'
    tables=[metric_table('Column overview',{'rows':col['count'],'missing':col['missing'],'distinct':col['distinct'],**col['statistics']},unit if col['effective_type'] in {'numeric','latitude','longitude'} else None)]
    scalar_keys=('finite','integers','non_integers','skewness','excess_kurtosis','entropy_bits','rare_level_count','earliest','latest','span_days','valid','invalid','two_digit_years','ambiguous_dates','placeholder_dates','after_reference','beyond_fixed_year_2100','lag1_count_autocorrelation')
    values={k:s[k] for k in scalar_keys if k in s}
    if values:tables.append(metric_table('Univariate statistics',values))
    for key in ('zeros','negatives','percentiles','candidate_blanks','length','casing','top_n_coverage','weekday_counts','month_counts','quarter_counts','year_counts'):
        if isinstance(s.get(key),dict):tables.append(metric_table(title(key),s[key],unit if key=='percentiles' else None))
    tables.append(frequency_table('Most common nonmissing values',col['frequencies'],col['count']-col['missing']))
    for key in ('least_common','rare_levels','special_characters','common_substrings'):
        if key in s:
            denominator=s.get('special_character_total') if key=='special_characters' else s.get('substring_total') if key=='common_substrings' else s.get('raw_lexemes',s.get('finite',col['count']-col['missing']))
            tables.append(frequency_table(title(key),s[key],denominator))
    if col.get('special'):
        special=col['special'];tables.append(metric_table('Local syntax/range checks',{k:special[k] for k in ('valid','invalid','placeholders','test_values')}))
        if special['domains']:tables.append(frequency_table('Most common valid domains',special['domains'],special['valid']))
    return [t for t in tables if t['rows']]


def html_table(table):
    out=['<div class="table-scroll"><table class="review-table"><caption>'+escape(table['caption'])+'</caption><thead><tr>']
    for i,h in enumerate(table['headers']):out.append('<th scope="col"'+(' class="num"' if i in table['numeric'] else '')+'>'+escape(h)+'</th>')
    out.append('</tr></thead><tbody>')
    for row in table['rows']:
        out.append('<tr>'+''.join('<td'+(' class="num"' if i in table['numeric'] else '')+'>'+escape(str(v))+'</td>' for i,v in enumerate(row))+'</tr>')
    return ''.join(out)+'</tbody></table></div>'


def markdown_table(table):
    def cell(v):return re.sub(r'([\\`*_{}\[\]()#!])',r'\\\1',escape(str(v),quote=False).replace('|','&#124;').replace('\n',' '))
    lines=['**'+cell(table['caption'])+'**','', '| '+' | '.join(map(cell,table['headers']))+' |','| '+' | '.join('---:' if i in table['numeric'] else '---' for i in range(len(table['headers'])))+' |']
    return '\n'.join(lines+['| '+' | '.join(map(cell,row))+' |' for row in table['rows']])+'\n'
