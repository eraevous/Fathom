"""Distribution-of-distributions views from stored metrics, never raw observations."""
from copy import deepcopy
from html import escape
from .presentation import formatted
from .palette import LIGHT as C

ORIENTATIONS={'columns_as_rows','metrics_as_rows'}
UNAVAILABLE='Not stored'


def report_options(raw=None):
    from .config import mapping
    if raw is None:raw={}
    if not isinstance(raw,dict):raise ValueError('config must be a mapping')
    r=mapping(raw.get('report',{}),'report',{'summary_orientation'})
    o=r.get('summary_orientation','columns_as_rows')
    if not isinstance(o,str) or o not in ORIENTATIONS:raise ValueError('report.summary_orientation must be columns_as_rows or metrics_as_rows')
    return {'summary_orientation':o}


def ratio(a,b):return a/b if isinstance(a,(int,float)) and isinstance(b,(int,float)) and b else None


def summary_tables(d,report=None):
    orientation=report_options({'report':report or {}})['summary_orientation'];tables={}
    for i,c in enumerate(d.get('columns',[])):
        typ=c['effective_type'];s=c.get('statistics',{});u=c.get('univariate',{}).get('statistics',{})
        numeric=typ in {'numeric','latitude','longitude'};temporal=typ=='temporal'
        missing=ratio(c['missing'],c['count']);q=u.get('percentiles',{});unit=c.get('univariate',{}).get('units') or {}
        unit=unit.get('value') if isinstance(unit,dict) else str(unit)
        if numeric:
            heads=['Column','n','Missing %','Distinct','Mean','Median','SD','IQR','Skew','Zero %','Min','Max','Units','Distribution']
            iqr=q['75']-q['25'] if q.get('75') is not None and q.get('25') is not None else None
            vals=[c['name'],s.get('valid',u.get('finite')),missing,c['distinct'],s.get('mean'),s.get('median',q.get('50')),s.get('population_std'),iqr,u.get('skewness'),u.get('zeros',{}).get('share'),s.get('min'),s.get('max'),unit or 'Unknown','']
            mark={'kind':'box','min':s.get('min'),'max':s.get('max'),'q1':q.get('25'),'q3':q.get('75'),'median':s.get('median',q.get('50'))}
        elif temporal:
            heads=['Column','Span','Parse coverage','Declared period','Gaps','Distribution']
            periods=[]
            for entry in d.get('time_series',{}).get('series',[]):
                if entry.get('declaration',{}).get('time')==c['name'] or any(g.get('time')==c['name'] for g in entry.get('groups',[])):
                    for g in entry.get('groups',[]):
                        for grain in g.get('granularities',[]):
                            if grain['granularity'] not in periods:periods.append(grain['granularity'])
            if not periods and s.get('precision')=='year':periods=['year (declared YEAR precision)']
            span=(str(u['earliest'])+' to '+str(u['latest'])+' ('+formatted(u['span_days'])+' days)') if u.get('earliest') else None
            coverage=ratio(u.get('valid'),c['count']-c['missing'])
            vals=[c['name'],span,coverage,', '.join(periods) or 'Not declared',len(u['large_gaps'])+u.get('omitted_gaps',0) if 'large_gaps' in u else None,'']
            mark={'kind':'share','share':coverage}
        else:
            heads=['Column','n','Missing %','Distinct','Top value share','Entropy (bits)','Length range','Distribution']
            n=u.get('raw_lexemes',c['count']-c['missing']);common=u.get('most_common',c.get('frequencies',[]));top=ratio(common[0]['count'],n) if common else None
            length=u.get('length',{});vals=[c['name'],n,missing,c['distinct'],top,u.get('entropy_bits'),f"{length['min']}–{length['max']}" if length.get('min') is not None else None,'']
            mark={'kind':'share','share':top}
        if typ not in tables:tables[typ]={'type':typ,'caption':typ.capitalize()+' column metrics','headers':heads,'rows':[],'orientation':'columns_as_rows','links':{},'marks':{}}
        t=tables[typ];t['rows'].append([UNAVAILABLE if v is None else v for v in vals]);t['links'][c['name']]='dictionary-column-'+str(i);t['marks'][c['name']]=mark
    return [transpose(t) if orientation=='metrics_as_rows' else t for t in tables.values()]


def transpose(table):
    out=deepcopy(table);grid=[table['headers'],*table['rows']]
    flipped=[list(row) for row in zip(*grid)]
    out['headers']=flipped[0];out['rows']=flipped[1:]
    out['orientation']='metrics_as_rows' if table['orientation']=='columns_as_rows' else 'columns_as_rows'
    out['headers'][0]='Metric' if out['orientation']=='metrics_as_rows' else 'Column'
    return out


def display(value,metric):
    if value=='':return ''
    if value==UNAVAILABLE:return value
    if isinstance(value,(int,float)):return formatted(value,metric in {'Missing %','Zero %','Top value share','Parse coverage'})
    return str(value)


def mark_svg(mark):
    desc='Distribution mark unavailable';shapes=''
    if mark['kind']=='share' and isinstance(mark.get('share'),(int,float)):
        share=mark['share'];desc='Stored share '+formatted(share,True)
        shapes=f'<line x1="2" y1="10" x2="94" y2="10" stroke="{C["accent_faint"]}"/><rect x="2" y="5" width="{92*share:.6f}" height="10" fill="{C["accent"]}"/>'
    elif mark['kind']=='box' and all(isinstance(mark.get(k),(int,float)) for k in ['min','max','q1','q3','median']):
        lo,hi=mark['min'],mark['max'];scale=max(abs(lo),abs(hi),1);span=hi/scale-lo/scale
        def x(v):return 2+92*((v/scale-lo/scale)/span if span else .5)
        desc='Stored min '+formatted(lo)+', median '+formatted(mark['median'])+', max '+formatted(hi)
        shapes=f'<line x1="2" y1="10" x2="94" y2="10" stroke="{C["accent"]}"/><rect x="{x(mark["q1"]):.6f}" y="5" width="{max(1,x(mark["q3"])-x(mark["q1"])):.6f}" height="10" fill="{C["accent_faint"]}"/><line x1="{x(mark["median"]):.6f}" y1="3" x2="{x(mark["median"]):.6f}" y2="17" stroke="{C["ink"]}"/>'
    if not shapes:return '<span>'+UNAVAILABLE+'</span>'
    return '<svg class="summary-mark" role="img" aria-label="'+escape(desc,quote=True)+'" viewBox="0 0 96 20" width="96" height="20">'+shapes+'</svg>'


def summary_html(d,report=None):
    tables=summary_tables(d,report)
    if not tables:return ''
    out=['<section id="distribution-summaries"><h2>Distribution summaries</h2><p>Stored metrics only. n is valid/finite (text: nonmissing); missing % uses all rows. Unknown units and unavailable statistics stay explicit. Parse coverage is not calendar completeness; gaps follow the stored univariate rule, not a declared schedule. Distribution marks repeat stored values.</p>']
    for i,t in enumerate(tables):
        tid='summary-table-'+str(i);pressed=t['orientation']=='metrics_as_rows'
        out.append('<button hidden type="button" class="transpose" data-transpose="'+tid+'" aria-controls="'+tid+'" aria-pressed="'+str(pressed).lower()+'">Transpose '+escape(t['type'])+' table</button><div class="table-scroll"><table class="review-table distribution-table" id="'+tid+'" data-orientation="'+t['orientation']+'"><caption>'+escape(t['caption'])+'</caption><thead><tr>')
        for j,h in enumerate(t['headers']):
            content=('<a href="#'+t['links'][h]+'"><code>'+escape(h)+'</code></a>') if j and h in t['links'] and pressed else escape(h)
            out.append('<th scope="col">'+content+'</th>')
        out.append('</tr></thead><tbody>')
        for row in t['rows']:
            out.append('<tr>')
            for j,v in enumerate(row):
                metric=row[0] if pressed else t['headers'][j];name=t['headers'][j] if pressed else row[0]
                content=mark_svg(t['marks'][name]) if metric=='Distribution' and j else '<a href="#'+t['links'][v]+'"><code>'+escape(v)+'</code></a>' if not pressed and j==0 else escape(display(v,metric))
                out.append(('<th scope="row">' if j==0 else '<td class="num">')+content+('</th>' if j==0 else '</td>'))
            out.append('</tr>')
        out.append('</tbody></table></div>')
    return ''.join(out)+'</section>'


def summary_markdown(d,report=None):
    out=['## Distribution summaries','','Stored metrics only; n is valid/finite/nonmissing. Missing % uses all rows. Parse coverage is not calendar completeness. Unknown/unavailable stays explicit.','']
    for t in summary_tables(d,report):
        grid=formatted_grid(t,marks=False)
        esc=lambda s:str(s).replace('|','&#124;').replace('\n',' ')
        out += [t['caption'],'','| '+' | '.join(map(esc,grid[0]))+' |','| '+' | '.join('---' for _ in grid[0])+' |']
        out += ['| '+' | '.join(map(esc,row))+' |' for row in grid[1:]];out.append('')
    return '\n'.join(out)+'\n'


def formatted_grid(t,marks=False):
    grid=[t['headers'][:]];pressed=t['orientation']=='metrics_as_rows'
    for row in t['rows']:
        if pressed and row[0]=='Distribution' and not marks:continue
        vals=[]
        for j,v in enumerate(row):
            metric=row[0] if pressed else t['headers'][j]
            if not pressed and metric=='Distribution' and not marks:continue
            vals.append(display(v,metric))
        grid.append(vals)
    if not pressed and not marks:grid[0]=grid[0][:-1]
    return grid


def summary_panels(d,report=None,max_columns=6,max_rows=14):
    """Page a fixed-format view, repeating row labels and preserving orientation."""
    panels=[]
    for t in summary_tables(d,report):
        grid=formatted_grid(t);head=grid[0]
        for start in range(1,len(head),max_columns-1):
            indices=[0,*range(start,min(start+max_columns-1,len(head)))]
            for row in range(1,len(grid),max_rows):
                panels.append({'caption':t['caption']+' — '+t['orientation']+(' (continued)' if start>1 or row>1 else ''),'headers':[head[i] for i in indices],'rows':[[r[i] for i in indices] for r in grid[row:row+max_rows]]})
    return panels


SUMMARY_CSS='''.distribution-table{max-width:none!important;min-width:720px;table-layout:auto!important}.distribution-table td{white-space:nowrap}.distribution-table th{white-space:nowrap}.summary-mark{width:96px!important;height:20px!important;min-width:96px}.transpose[hidden]{display:none}.transpose{font:inherit;color:var(--ink);background:var(--panel);border:1px solid var(--accent);padding:6px 10px;border-radius:4px;cursor:pointer}.transpose:focus-visible{outline:3px solid var(--accent);outline-offset:3px}@media print{.transpose{display:none!important}}'''
TRANSPOSE_SCRIPT='''<script id="fathom-transpose">document.querySelectorAll('[data-transpose]').forEach(b=>{const t=document.getElementById(b.dataset.transpose);b.hidden=false;b.addEventListener('click',()=>{const rows=Array.from(t.rows),head=document.createElement('thead'),body=document.createElement('tbody'),caption=t.caption.cloneNode(true);for(let j=0;j<rows[0].cells.length;j++){const row=document.createElement('tr');for(let i=0;i<rows.length;i++){const old=rows[i].cells[j],cell=document.createElement(j===0||i===0?'th':'td');cell.className=j===0||i===0?'':old.className;if(j===0)cell.scope='col';else if(i===0)cell.scope='row';old.childNodes.forEach(n=>cell.appendChild(n.cloneNode(true)));row.appendChild(cell);}(j===0?head:body).appendChild(row);}const flipped=t.dataset.orientation!=='metrics_as_rows';head.rows[0].cells[0].textContent=flipped?'Metric':'Column';t.replaceChildren(caption,head,body);t.dataset.orientation=flipped?'metrics_as_rows':'columns_as_rows';b.setAttribute('aria-pressed',String(flipped));});});</script>'''
