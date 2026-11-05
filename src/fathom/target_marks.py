"""Shared static mark geometry for artifact-only SVG/PDF/slide target plots."""

import math
from .charts import linear_ticks
from .presentation import tick_label
from .palette import CATEGORICAL, LIGHT as C

PALETTE=CATEGORICAL


def plot_marks(ch):
    """Return width,height and simple vector marks; original values stay in artifact."""
    kind=ch['kind'];marks=[];width=560;left,right,top,bottom=75,510,25,235
    def line(x1,y1,x2,y2,color=C['grid']):marks.append(('line',x1,y1,x2,y2,color))
    def text(x,y,value,anchor='start',size=18):marks.append(('text',x,y,str(value),anchor,size))
    def rect(x,y,w,h,color):marks.append(('rect',x,y,w,h,color))
    def axis(values,lo,hi,scale,start,end,horizontal=True):
        transformed=lambda v:math.log10(v) if scale=='log10' else v
        a,b=transformed(lo),transformed(hi);norm=max(abs(a),abs(b),1);span=b/norm-a/norm
        def pos(v):return start+(end-start)*((transformed(v)/norm-a/norm)/span if span else .5)
        ticks=linear_ticks(a,b)
        if horizontal and any(len(tick_label(10**t if scale=='log10' else t))>7 for t in ticks):ticks=linear_ticks(a,b,3)
        for t in ticks:
            value=10**t if scale=='log10' else t;p=start+(end-start)*((t/norm-a/norm)/span if span else .5)
            if horizontal:line(p,top,p,bottom);text(p,bottom+23,tick_label(value),'middle')
            else:line(left,p,right,p);text(left-8,p+5,tick_label(value),'end')
        return pos
    if kind=='scatter':
        points=ch['points'];xs=[p['x'] for p in points];ys=[p['y'] for p in points]
        xp=axis(xs,min(xs),max(xs),ch['x_scale'],left,right);yp=axis(ys,min(ys),max(ys),ch['y_scale'],bottom,top,False)
        for p in points:marks.append(('circle',xp(p['x']),yp(p['y']),3.2,C['accent']))
        return width,275,marks
    if kind=='group_box':
        rows=ch['data'];left=195;bottom=35+len(rows)*48;top=15
        boxes=[r['box'] for r in rows if r.get('box')]
        if boxes:
            lo,hi=ch.get('x_domain',(min(b['min'] for b in boxes),max(b['max'] for b in boxes)))
            xp=axis([],lo,hi,ch.get('x_scale','linear'),left,right)
        else:xp=lambda v:(left+right)/2
        for i,row in enumerate(rows):
            y=35+i*48;label=row['label'];text(left-12,y-3,label[:11]+('…' if len(label)>11 else ''),'end',15)
            sample=(f"n={row['n']}; excl={row['excluded_nonpositive']}"+('; small' if row['n']<5 else '')) if 'excluded_nonpositive' in row else 'n=? (legacy)'
            text(left-12,y+16,sample,'end',14)
            b=row.get('box')
            if b:
                line(xp(b['min']),y,xp(b['max']),y,C['accent']);rect(xp(b['q1']),y-9,max(1,xp(b['q3'])-xp(b['q1'])),18,C['soft_border']);line(xp(b['median']),y-10,xp(b['median']),y+10,C['ink'])
            else:text(left,y+5,'No positive values',size=14)
        return width,bottom+35,marks
    # Rates: one stacked bar per bin/group, explicit n including empty bins.
    rows=ch['data'];levels=ch['levels'];left=170;bottom=25+len(rows)*52;top=15
    for value in (0,.25,.5,.75,1):
        x=left+(right-left)*value;line(x,top,x,bottom);text(x,bottom+23,f'{value:.0%}','middle')
    for i,row in enumerate(rows):
        y=35+i*52;label=row['label'];text(left-10,y-1,label[:20]+('…' if len(label)>20 else ''),'end',13);text(left-10,y+17,f"n={row['n']}"+('; small' if row['n']<5 else ''),'end',13)
        x=left
        for j,level in enumerate(levels):
            w=row['rates'][level]*(right-left);rect(x,y-12,w,25,PALETTE[j]);x+=w
        if not row['n']:text(left+10,y+6,'Empty bin',size=14)
    y=bottom+53
    if ch.get('show_legend',True):
        for j,level in enumerate(levels):rect(left,y-12,12,12,PALETTE[j]);text(left+20,y,level[:42]+('…' if len(level)>42 else ''),size=14);y+=22
    return width,y+10,marks


def coverage_note(ch):
    box_note=(' Box n is plotted; excl counts excluded nonpositive values per box.' if all('excluded_nonpositive' in r for r in ch['data']) else ' Legacy per-box plotted/excluded counts unavailable; reprofile for corrected box counts.') if ch['kind']=='group_box' else ''
    return f"Descriptive, not causal. {ch['n']:,} complete of {ch['total_rows']:,} rows; plotted {ch.get('plotted',ch['n']):,}. Nonpositive cases excluded for log: {ch.get('omitted_nonpositive',0):,}; sampled points omitted: {ch.get('omitted_points',0):,}. Small groups/bins (n<5) are too small to read reliably. Full labels and values remain in tables/artifact.{box_note}"


def chart_values(ch):
    """Text equivalent of plotted values; float strings preserve chart precision."""
    kind=ch['kind']
    if kind=='scatter':
        return {'caption':'Plotted scatter coordinates — original units','headers':[ch['x_label'],ch['y_label']],
                'rows':[[str(p['x']),str(p['y'])] for p in ch['points']],'numeric':[0,1]}
    if kind=='group_box':
        return {'caption':'Plotted five-number summaries — original units','headers':['Group','Plotted n','Excluded nonpositive','Min','Q1','Median','Q3','Max'],
                'rows':[[r['label'],str(r['n']) if 'excluded_nonpositive' in r else f"Unavailable (legacy recorded n={r['n']})",str(r.get('excluded_nonpositive','Unavailable in legacy artifact')),*[str(r['box'][k]) if r.get('box') else 'Unavailable' for k in ('min','q1','median','q3','max')]] for r in ch['data']],'numeric':list(range(1,8))}
    return {'caption':'Plotted target category rates by predictor group/bin','headers':['Predictor group/bin','Complete n','Target category','Rate (fraction)'],
            'rows':[[row['label'],str(row['n']),level,str(row['rates'][level])] for row in ch['data'] for level in ch['levels']],'numeric':[1,3]}
