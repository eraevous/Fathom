"""Scalable static charts; captions and summaries wrap independently of marks."""

from html import escape
import math
import textwrap

from .presentation import formatted, html_table, tick_label, original_tick
from .palette import LIGHT as C


def linear_ticks(lo,hi,count=5):
    if lo==hi:return [lo]
    scale=max(abs(lo),abs(hi),1)
    return [(lo/scale+(hi/scale-lo/scale)*i/(count-1))*scale for i in range(count)]


def whole_ticks(lo,hi,count=5):
    """Whole-number axis ticks inside [lo, hi] for whole-number histograms (spec 028).

    Their geometry runs on half-integers (bars are centred on the values they hold),
    so plain linear ticks would print values like 2.5 that the data cannot take."""
    first,last=math.ceil(lo),math.floor(hi)
    if last-first<count:return list(range(first,last+1))
    return sorted(set(round(v) for v in linear_ticks(first,last,count)))


def axis_ticks(chart,lo,hi):
    return whole_ticks(lo,hi) if chart.get('whole_number_bins') else linear_ticks(lo,hi)


def whole_note(chart):
    """Plain disclosure of the whole-number bin layout; None for other charts."""
    rule=chart.get('whole_number_bins')
    if not rule:return None
    width=rule['width']
    return 'Whole-number values: '+('one bar per value.' if width==1 else f'each bar holds {width:,} consecutive whole values; labels are inclusive.')


def count_ticks(maximum):
    """Count axes use distinct whole-number tick positions."""
    return sorted(set(round(value) for value in linear_ticks(0,maximum)))


def svg_chart(chart):
    if chart['kind'] in {'scatter','group_box','rates'}:
        from .target_marks import plot_marks,coverage_note,chart_values
        w,h,marks=plot_marks(chart);out=[]
        for mark in marks:
            kind,*v=mark
            if kind=='line':out.append(f'<line x1="{v[0]}" y1="{v[1]}" x2="{v[2]}" y2="{v[3]}" stroke="{v[4]}"/>')
            elif kind=='rect':out.append(f'<rect x="{v[0]}" y="{v[1]}" width="{v[2]}" height="{v[3]}" fill="{v[4]}"/>')
            elif kind=='circle':out.append(f'<circle cx="{v[0]}" cy="{v[1]}" r="{v[2]}" fill="{v[3]}" />')
            else:out.append(f'<text x="{v[0]}" y="{v[1]}" text-anchor="{v[3]}" style="font-size:{v[4]}px">{escape(v[2])}</text>')
        return '<figure class="chart target-chart"><p class="chart-title">'+escape(chart['title'])+'</p>'+f'<svg role="img" data-kind="{chart["kind"]}" aria-label="{escape(chart["title"],quote=True)}" viewBox="0 0 {w} {h}">'+''.join(out)+'</svg><div class="axis-captions"><p>X: '+escape(chart['x_label'])+'</p><p>Y: '+escape(chart['y_label'])+'</p></div><figcaption>'+escape(coverage_note(chart))+'</figcaption><details><summary>Chart values</summary>'+html_table(chart_values(chart))+'</details></figure>'
    def e(v):return escape(str(v))
    kind=chart['kind'];data=chart.get('data',[]);width=560
    labels=[]
    for d in data:
        lines=textwrap.wrap(str(d['label']) or '[empty]',14)
        labels.append(lines[:2]+[lines[2][:12]+'…'] if len(lines)>3 else lines)
    heights=[max(38,len(x)*22+10) for x in labels]
    height=50+sum(heights) if kind=='bar' else 110 if kind=='box' else 270
    out=[f'<svg role="img" aria-label="{escape(chart["title"],quote=True)}" viewBox="0 0 {width} {height}"><title>{e(chart["title"])}</title>']
    def text(x,y,value,anchor='start',cls=''):
        out.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}"'+(f' class="{cls}"' if cls else '')+'>'+e(value)+'</text>')
    def grid(x1,y1,x2,y2):out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{C["accent_faint"]}"/>')
    if kind=='bar':
        maximum=max((d['count'] for d in data),default=1) or 1
        for value in count_ticks(maximum):
            x=175+305*value/maximum;grid(x,15,x,height-30);text(x,height-7,tick_label(value),'middle','tick-label')
        y=20
        for d,lines,h in zip(data,labels,heights):
            center=y+h/2;end=175+305*d['count']/maximum
            for i,line in enumerate(lines):text(165,center-(len(lines)-1)*10+i*22+6,line,'end')
            out += [f'<rect x="175" y="{center-10}" width="{end-175}" height="20" fill="{C["accent"]}"><title>{e(d["label"])}: {d["count"]}</title></rect>']
            text(end+8,center+6,tick_label(d['count']));y+=h
    elif kind in {'box','ecdf'} or data:
        left,right,bottom,top=65,515,80 if kind=='box' else 220,20
        if kind=='box':lo,hi=chart['box']['min'],chart['box']['max']
        elif kind=='ecdf':lo,hi=chart['points'][0]['x'],chart['points'][-1]['x']
        elif kind=='histogram':lo,hi=data[0]['low'],data[-1]['high']
        else:lo,hi=0,max(1,len(data)-1)
        scale=max(abs(lo),abs(hi),1);span=hi/scale-lo/scale
        def px(v):return left+(right-left)*((v/scale-lo/scale)/span if span else .5)
        ticks=axis_ticks(chart,lo,hi)
        if kind=='time':
            indices=sorted(set(round(i*(len(data)-1)/4) for i in range(5)))
            for i in indices:
                label=data[i]['label'];label=label[5:] if len(label)==10 else label
                text(left+(right-left)*((i+.5)/len(data)),255,label,'middle','tick-label')
        else:
            for value in ticks:
                x=px(value);grid(x,top,x,bottom);text(x,102 if kind=='box' else 255,original_tick(chart,value),'middle','tick-label')
        if kind=='box':
            b=chart['box'];y=48
            out += [f'<line x1="{px(lo)}" y1="{y}" x2="{px(hi)}" y2="{y}" stroke="{C["ink"]}"/><rect x="{px(b["q1"])}" y="38" width="{max(1,px(b["q3"])-px(b["q1"]))}" height="20" fill="{C["accent_faint"]}" stroke="{C["accent"]}"/><line x1="{px(b["median"])}" y1="38" x2="{px(b["median"])}" y2="58" stroke="{C["ink"]}"/>']
        else:
            maximum=1 if kind=='ecdf' else max((d['count'] for d in data),default=1) or 1
            for value in (linear_ticks(0,1) if kind=='ecdf' else count_ticks(maximum)):
                y=bottom-value/maximum*(bottom-top);grid(left,y,right,y)
                text(left-8,y+6,f'{value:.0%}' if kind=='ecdf' else tick_label(value),'end','tick-label')
            if kind=='ecdf':
                path=f'M {px(lo)} {bottom}'
                for point in chart['points']:path+=f' H {px(point["x"])} V {bottom-point["cumulative"]*(bottom-top)}'
                out.append(f'<path d="{path}" fill="none" stroke="{C["accent"]}" stroke-width="2"/>')
            else:
                barwidth=(right-left)/len(data)
                for i,d in enumerate(data):
                    h=d['count']/maximum*(bottom-top)
                    out.append(f'<rect x="{left+i*barwidth}" y="{bottom-h}" width="{max(.5,barwidth-2)}" height="{h}" fill="{C["accent"]}"><title>{e(d["label"])}: {d["count"]}</title></rect>')
    out.append('</svg>')
    notes=[]
    if kind=='time' and data:notes.append('Calendar range: '+data[0]['label']+' to '+data[-1]['label']+('. Day ticks omit the year; exact dates remain in chart values.' if chart.get('period')=='day' else '. Exact calendar-period labels and values remain in chart values.'))
    if whole_note(chart):notes.append(whole_note(chart))
    if 'coverage' in chart:notes.append('Top10 covers '+formatted(chart['coverage'],True)+f" of {chart['denominator']:,} raw values; remainder is shown separately.")
    if chart.get('omitted_periods'):notes.append(f"{chart['omitted_periods']:,} middle calendar bins omitted; full counts remain in profile.")
    if chart.get('omitted_points'):notes.append(f"Approximate ECDF display: {chart['omitted_points']:,} distinct points omitted.")
    if chart.get('scale')=='log10':
        counts=chart.get('coverage_counts')
        notes.append((f"Positive values: {counts['positive']:,}. Zeros excluded: {counts['zeros']:,}. Negatives excluded: {counts['negatives']:,}. Invalid excluded: {counts['invalid']:,}." if counts else 'Legacy log coverage counts unavailable.')+' Positive-only denominator; original-unit ticks on log scale; linear view retained.')
    rows=[[d['label'],formatted(d['count'])] for d in data]
    if kind=='ecdf':rows=[[original_tick(chart,p['x']),formatted(p['cumulative'],True)] for p in chart['points']]
    if kind=='box':rows=[[k.upper() if k in {'q1','q3'} else k.capitalize(),formatted(chart['box'][k])] for k in ('min','q1','median','q3','max')]
    table=html_table({'caption':'Five-number summary' if kind=='box' else 'Plotted values','headers':['Value','Cumulative share' if kind=='ecdf' else 'Measurement' if kind=='box' else 'Count'],'rows':rows,'numeric':[1]})
    summary='<div class="box-summary">'+table+'</div>' if kind=='box' else '<details><summary>Chart values</summary>'+table+'</details>'
    return '<figure class="chart"><p class="chart-title">'+e(chart['title'])+'</p>'+''.join(out)+'<div class="axis-captions"><p>X: '+e(chart['x_label'])+'</p>'+('' if kind=='box' else '<p>Y: '+e(chart['y_label'])+'</p>')+'</div>'+''.join('<figcaption>'+e(n)+'</figcaption>' for n in notes)+summary+'</figure>'
