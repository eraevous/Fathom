"""Conservative nested presentation of existing quantities; no verdict computation."""
from html import escape
import re
from .presentation import formatted

_OP=re.compile(r'>=|<=|==|!=|=|≥|≤|<|>|\b(?:vs|versus)\b')
_LITERAL=re.compile(r'`[^`]*`|"[^"\n]*"|\x27[^\x27\n]*\x27')


def masked_text(text,columns=()):
    for name in sorted(set(columns),key=lambda x:(-len(x),x)):
        if name:text=re.sub(r'(?<!\w)'+re.escape(name)+r'(?!\w)',lambda m:' '*len(m.group()),text)
    return _LITERAL.sub(lambda m:' '*len(m.group()),text)


def comparison_count(text,columns=()):return len(_OP.findall(masked_text(text,columns)))


def finding_tree(f,document=None):
    """Use saved typed fields only; unstructured prose is never tokenized."""
    fallback={'text':f['message'],'children':[]}
    evidence=next((e.get('value') for e in f.get('evidence',[]) if isinstance(e.get('value'),dict)),{})
    names=f.get('columns',[])
    if f.get('kind')!='observation':return fallback
    if f.get('rule')=='selected_relation' and len(names)==2:
        pair=next((p for p in (document or {}).get('bivariate',[]) if [p['left'],p['right']]==names),{})
        measures=[(label,evidence[key]) for key,label in [('pearson_r','Pearson r'),('eta','Correlation ratio eta'),('cramers_v',"Cramer's V")] if isinstance(evidence.get(key),(int,float))]
        if not measures or not isinstance(evidence.get('n'),int):return fallback
        basis=' ('+pair['semantics']+')' if pair.get('semantics') else ''
        return {'text':'selected: '+names[0]+' × '+names[1]+basis,
                'children':[label+': '+format(value,'.3f') for label,value in measures]+['complete cases: '+formatted(evidence['n']),'descriptive, not causal']}
    if f.get('rule')=='target_group_contrast' and 'contrasts' in evidence and len(names)==2:
        status='marked' if evidence['contrasts'] else 'not marked'
        text=status+': '+names[1]+' differs in '+names[0]+' = '+repr(evidence.get('value'))
        children=[]
        for contrast in evidence['contrasts']:
            kind=contrast['measure'];share=kind.startswith('rate:') or kind=='missing share'
            group_count=formatted(evidence.get('n'))+' rows ('+formatted(evidence.get('valid'))+' valid)'
            rest_count=formatted(evidence.get('rest_n'))+' rows ('+formatted(evidence.get('rest_valid'))+' valid)'
            children.extend(['group: '+group_count+', '+kind+' '+formatted(contrast['group'],share),
                             'rest: '+rest_count+', '+kind+' '+formatted(contrast['rest'],share)])
        from .verdicts import gate_text
        children.extend('gate: '+gate_text(g) for g in evidence.get('gates',[]))
        if evidence.get('small'):children.append('Caution: too small to read reliably (valid n < 5)')
        if not evidence['contrasts']:children.extend(['Group rows: '+formatted(evidence.get('n')),'Rest rows: '+formatted(evidence.get('rest_n'))])
        children.append('Group missing: '+formatted(evidence.get('missing')))
        return {'text':text,'children':children}
    return fallback


def html_tree(tree,columns=(),styled=True):
    from .report_style import html_text
    children=tree['children']
    text=lambda s:html_text(s,columns=columns,verdict=True) if styled else escape(s)
    return text(tree['text'])+('<ul class="quantity-list">'+''.join('<li class="finding-line">'+text(s)+'</li>' for s in children)+'</ul>' if children else '')


def markdown_tree(tree,columns=()):
    from .report_style import markdown_text
    head=markdown_text(tree['text'],columns=columns,verdict=True)
    if not tree['children']:return head
    return ('- '+head)+('\n'+''.join('  - '+markdown_text(s,columns=columns,verdict=True)+'\n' for s in tree['children']) if tree['children'] else '')


def evidence_html(value):
    """Technical quantities stay nested and attributable, behind native disclosure."""
    if isinstance(value,dict):
        return '<ul class="evidence-quantities">'+''.join('<li><code>'+escape(str(k))+'</code>: '+evidence_html(v)+'</li>' for k,v in sorted(value.items(),key=lambda item:str(item[0])))+'</ul>' if value else '<code>{}</code>'
    if isinstance(value,list):return '<ul>'+''.join('<li>'+evidence_html(v)+'</li>' for v in value)+'</ul>' if value else '<code>[]</code>'
    return escape(str(value))


def evidence_markdown(value,depth=0):
    from .report_style import markdown_text
    pad='  '*depth
    if isinstance(value,dict):
        return ''.join(pad+'- '+markdown_text(str(k),literal=True)+':\n'+evidence_markdown(v,depth+1) for k,v in sorted(value.items(),key=lambda item:str(item[0]))) or pad+'- {}\n'
    if isinstance(value,list):return ''.join(evidence_markdown(v,depth) for v in value) or pad+'- []\n'
    lines=[str(value)]
    return ''.join(pad+'- '+markdown_text(line,verdict=True)+'\n' for line in lines)
