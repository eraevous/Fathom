"""Shared presentation roles. These heuristics never compute analytical verdicts.

See docs/report-style.md. Literal identifiers win over prose tokens; callers opt
into verdict/inference contexts. Scripts, raw evidence, code and SVG stay literal.
"""
from html import escape
from html.parser import HTMLParser
import re

MAX_BOLD_WORDS = 8
VERDICTS = ('not strongly skewed', 'strongly skewed', 'insufficient evidence',
            'not estimable', 'not marked', 'marked', 'insufficient', 'not constant', 'constant',
            'undefined', 'computed', 'present', 'absent', 'smooth', 'erratic', 'intermittent', 'lumpy')
_STATE = re.compile(r'(?<![\w-])(?:'+'|'.join(VERDICTS)+r')(?![\w-])',re.I)
_INFERRED = re.compile(r'\(inferred\)|\binferred(?:, not a domain fact| [\w-]+)?|\bunknown meaning\b|\bmeaning (?:is )?unknown\b',re.I)
_LITERAL = re.compile(r'`[^`\n]+`|\b(?:rule:[\w:.-]+|[A-Z]{2,}(?:-[A-Z0-9]+)+(?:@\d+)?|[a-f0-9]{12,64})\b|["\u201c][^"\u201d\n]+["\u201d]')
_NUMBER = re.compile(r'(?:(?:gap|r|eta|rho|mean|median|ACF|family gate)\s*(?:=\s*)?|\bis\s+)([-+]?\d[\d,.]*(?:e[-+]?\d+)?)',re.I)


def runs(text, columns=(), verdict=False, inferred=False, literal=False):
    """Ordered (text, role) runs; literal data never acquires a semantic verdict."""
    text=str(text)
    if not text:return []
    if literal:return [(text,'literal')]
    spans=[]
    def add(a,b,kind):
        if a<b and not any(a<y and b>x for x,y,_ in spans):spans.append((a,b,kind))
    for m in _LITERAL.finditer(text):add(*m.span(),'literal')
    for m in re.finditer(r"(?<!\w)'[^'\n]+'(?!\w)",text):add(*m.span(),'literal')
    for name in sorted(set(columns),key=lambda v:(-len(v),v)):
        if name:
            for m in re.finditer(r'(?<!\w)'+re.escape(name)+r'(?!\w)',text):add(*m.span(),'literal')
    if verdict:
        for m in _STATE.finditer(text):
            if m.group().lower()=='constant' and re.match(r' columns?\b',text[m.end():],re.I):continue
            add(*m.span(),'verdict')
        for m in _NUMBER.finditer(text):add(*m.span(1),'verdict')
    if not inferred:
        for m in _INFERRED.finditer(text):add(*m.span(),'inferred')
    out=[];pos=0
    for a,b,role in sorted(spans):
        if a>pos:out.append((text[pos:a],'inferred' if inferred else 'plain'))
        out.append((text[a:b],role));pos=b
    if pos<len(text):out.append((text[pos:],'inferred' if inferred else 'plain'))
    return out


def html_text(text, **context):
    tags={'verdict':'strong','inferred':'em','literal':'code'}
    return ''.join('<'+tags[role]+'>'+escape(part,quote=False)+'</'+tags[role]+'>' if role in tags else escape(part,quote=False) for part,role in runs(text,**context))


def markdown_text(text, **context):
    def quoted(part):return re.sub(r'([\\`*_{}\[\]()#|])',r'\\\1',escape(part,quote=False)).replace('\n',' ')
    def code(part):
        if any(c in part for c in '<>&'):return '<code>'+escape(part,quote=False)+'</code>'
        # Longer fence preserves literal backticks without creating markup.
        fence='`'*(max((len(x) for x in re.findall(r'`+',part)),default=0)+1)
        return fence+' '+part.replace('\n',' ')+' '+fence if '`' in part else '`'+part+'`'
    return ''.join(('**'+quoted(part)+'**' if role=='verdict' else '*'+quoted(part)+'*' if role=='inferred' else code(part) if role=='literal' else quoted(part)) for part,role in runs(text,**context))


STYLE_CSS = '''
/* Shared report semantics; colors inherit spec008's palette. */
a{text-decoration:underline;text-underline-offset:.16em}code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:.92em;overflow-wrap:anywhere}
#key-findings p{margin:10px 0}summary{font-weight:400}strong{font-weight:700}em{font-style:italic}.chart-title{font-size:1rem;margin:8px 0}.finding>p{max-width:90ch}
.report-nav{background:var(--panel);border:1px solid var(--border);border-radius:6px;padding:10px 14px;margin:16px 0 24px}
.report-nav button{font:inherit;color:var(--ink);background:var(--tint);border:1px solid var(--border);border-radius:4px;padding:6px 10px;cursor:pointer}
.report-nav button[hidden]{display:none}.report-nav ul{display:flex;flex-wrap:wrap;gap:6px 20px;list-style:none;margin:8px 0;padding:0}
.report-nav li{margin:0}.report-nav [hidden]{display:none}.report-nav .nav-count{font-size:.85em;color:var(--muted);font-variant-numeric:tabular-nums}
.report-nav a:focus-visible,.report-nav button:focus-visible{outline:3px solid var(--accent);outline-offset:3px}
@media(max-width:600px){.report-nav ul{display:block}.report-nav li{padding:6px 0}}
@media print{.report-nav{display:none!important}}
'''
NAV_SCRIPT = '''<script id="fathom-navigation">(()=>{const n=document.querySelector('.report-nav');if(!n)return;const b=n.querySelector('button'),l=n.querySelector('ul');b.hidden=false;const toggle=(open)=>{l.hidden=!open;b.setAttribute('aria-expanded',String(open));};toggle(!matchMedia('(max-width:600px)').matches);b.addEventListener('click',()=>toggle(b.getAttribute('aria-expanded')!=='true'));})();</script>'''


def navigation(items):
    """Static list first: a failed/disabled script can never hide destinations."""
    return ('<nav class="report-nav" aria-label="Report sections"><button hidden type="button" aria-expanded="true" aria-controls="report-sections">Report sections</button><ul id="report-sections">'+
            ''.join('<li><a href="#'+escape(ref,quote=True)+'">'+escape(label)+(f' <span class="nav-count" data-nav-count="{count}">({count:,})</span>' if count is not None else '')+'</a></li>' for ref,label,count in items)+'</ul></nav>')


class _Style(HTMLParser):
    """Apply the common roles to rendered prose, preserving embedded code verbatim."""
    def __init__(self,columns):
        super().__init__(convert_charrefs=True);self.columns=columns;self.out=[];self.stack=[]
    def handle_decl(self,data):self.out.append('<!'+data+'>')
    def handle_comment(self,data):self.out.append('<!--'+data+'-->')
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);raw=self.get_starttag_text()
        if tag in {'b','strong'}:raw='<span>'
        if tag in {'h4','h5','h6'}:raw='<p class="chart-title">'
        self.out.append(raw)
        if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:self.stack.append((tag,a))
    def handle_startendtag(self,tag,attrs):self.out.append(self.get_starttag_text())
    def handle_endtag(self,tag):
        self.out.append('</span>' if tag in {'b','strong'} else '</p>' if tag in {'h4','h5','h6'} else '</'+tag+'>')
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i][0]==tag:self.stack=self.stack[:i];break
    def handle_data(self,text):
        tags={tag for tag,_ in self.stack}
        if tags & {'script','style'}:self.out.append(text);return
        if tags & {'svg','code','pre','textarea','option','title'}:
            self.out.append(escape(text,quote=False));return
        attrs=[a for _,a in self.stack];classes=' '.join(a.get('class','') for a in attrs)
        ids={a.get('id') for a in attrs}
        if 'raw-evidence' in classes.split():self.out.append(escape(text,quote=False));return
        if 'literal-data' in classes.split():self.out.append(html_text(text,literal=True));return
        if text.startswith('Examples: '):self.out.append('Examples: '+html_text(text[10:],literal=True));return
        if 'sample-scroll' in classes.split() and 'td' in tags:self.out.append(html_text(text,literal=True));return
        verdict=('finding' in classes.split() or 'key-findings' in ids or 'gate' in classes.split() or 'series-entry' in classes.split() or bool(_STATE.fullmatch(text.strip())) or '→' in text)
        inferred=('inferred-reading' in classes.split() or ('details' not in tags and ('kind-hypothesis' in classes.split() or 'kind-interpretation' in classes.split())))
        # Existing em context already carries the inferred role; avoid nesting it.
        self.out.append(html_text(text,columns=self.columns,verdict=verdict,inferred=inferred) if 'em' not in tags else escape(text,quote=False))


def style_html(page, columns=()):
    p=_Style(columns);p.feed(page);p.close();return ''.join(p.out)
