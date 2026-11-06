"""Conservative nested presentation of existing quantities; no verdict computation."""
from html import escape
import re
from .presentation import formatted

_OP=re.compile(r'>=|<=|==|!=|=|≥|≤|<|>|\b(?:vs|versus)\b')
_LITERAL=re.compile(r'`[^`]*`|"[^"\n]*"|\x27[^\x27\n]*\x27')
_NUM=re.compile(r'(?<!\w)[+-]?\d+(?:[.,]\d+)*(?:e[+-]?\d+)?',re.I)


def masked_text(text,columns=()):
    for name in sorted(set(columns),key=lambda x:(-len(x),x)):
        if name:text=re.sub(r'(?<!\w)'+re.escape(name)+r'(?!\w)',lambda m:' '*len(m.group()),text)
    return _LITERAL.sub(lambda m:' '*len(m.group()),text)


def comparison_count(text,columns=()):return len(_OP.findall(masked_text(text,columns)))


def quantity_lines(text,columns=()):
    """Retain source clauses; line boundaries replace punctuation, never quantities."""
    lines=[]
    # Splitting semicolons/commas/paired conjunctions is a presentation boundary only.
    masked=masked_text(text,columns)
    separators=list(re.finditer(r';\s*|\n+|,\s+(?=[\w|])|\s+(?:vs|versus)\s+|\s+and\s+(?=\d)',masked))
    parts=[];pos=0
    for sep in separators:parts.append(text[pos:sep.start()]);pos=sep.end()
    parts.append(text[pos:])
    for part in parts:
        part=part.strip()
        if not part:continue
        while comparison_count(part,columns)>1:
            ops=list(_OP.finditer(masked_text(part,columns)));second=ops[1]
            prefix=part[:second.start()];field=re.search(r'[\w|.−-]+\s*$',prefix)
            cut=field.start() if field and field.start()>0 else second.start()
            if cut<=0:break
            lines.append(part[:cut].strip());part=part[cut:].strip()
        if part:lines.append(part)
    return lines


def finding_tree(f):
    message=f['message'];evidence=next((e.get('value') for e in f.get('evidence',[]) if isinstance(e.get('value'),dict)),{})
    if f.get('rule')=='target_group_contrast' and f.get('kind')=='observation' and 'contrasts' in evidence:
        names=f.get('columns',[]);label=names[0] if names else 'group';measure=names[1] if len(names)>1 else 'value'
        status='marked' if evidence['contrasts'] else 'not marked'
        text=status+': '+repr(evidence.get('value'))+' in '+label+' — '+measure+' contrast with rest'
        children=[]
        for contrast in evidence['contrasts']:
            kind=contrast['measure'];share=kind.startswith('rate:') or kind=='missing share'
            children.extend(['group: '+kind+' '+formatted(contrast['group'],share)+' (n = '+str(evidence.get('n' if kind=='missing share' else 'valid','unknown'))+')',
                             'rest: '+kind+' '+formatted(contrast['rest'],share)+' (n = '+str(evidence.get('rest_n' if kind=='missing share' else 'rest_valid','unknown'))+')'])
        from .verdicts import gate_text
        children.extend('gate: '+gate_text(g) for g in evidence.get('gates',[]))
        if evidence.get('small'):children.append('Caution: too small to read reliably (valid n < 5)')
        children.extend(['Group rows: '+str(evidence.get('n','unknown')),'Rest rows: '+str(evidence.get('rest_n','unknown')),'Group missing: '+str(evidence.get('missing','unknown'))])
        return {'text':text,'children':[line for s in children for line in quantity_lines(s,names)]}
    names=f.get('columns',[])
    lines=quantity_lines(message,names)
    numeric=len(_NUM.findall(masked_text(message,names)))>=2
    if len(lines)>1 and (numeric or comparison_count(message,names)>1):
        prefix=message.split(':',1)[0]
        parent=prefix if ':' in message and not _NUM.search(prefix) and comparison_count(prefix,names)<=1 else f.get('kind','finding').capitalize()+' — '+(', '.join(f.get('columns',[])) or f.get('rule',f.get('id','quantities')).replace('_',' '))
        return {'text':parent,'children':lines}
    return {'text':message,'children':[]}


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
    if isinstance(value,str) and comparison_count(value)>1:return '<ul>'+''.join('<li class="finding-line">'+escape(s)+'</li>' for s in quantity_lines(value))+'</ul>'
    return escape(str(value))


def evidence_markdown(value,depth=0):
    from .report_style import markdown_text
    pad='  '*depth
    if isinstance(value,dict):
        return ''.join(pad+'- '+markdown_text(str(k),literal=True)+':\n'+evidence_markdown(v,depth+1) for k,v in sorted(value.items(),key=lambda item:str(item[0]))) or pad+'- {}\n'
    if isinstance(value,list):return ''.join(evidence_markdown(v,depth) for v in value) or pad+'- []\n'
    lines=quantity_lines(str(value)) if isinstance(value,str) and comparison_count(value)>1 else [str(value)]
    return ''.join(pad+'- '+markdown_text(line,verdict=True)+'\n' for line in lines)
