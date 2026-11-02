"""Static local SVG views with adjacent labels and truthful numerical axes."""

from html import escape
import textwrap

from .presentation import formatted


def svg_chart(chart):
    def e(value):return escape(str(value))
    kind=chart['kind'];data=chart.get('data',[]);width=720
    title_lines=textwrap.wrap(chart['title'],75) or ['']
    top=30+len(title_lines)*20
    labels=[textwrap.wrap(str(d['label']) or '[empty]',27) for d in data]
    row_heights=[max(32,len(lines)*17+10) for lines in labels]
    height=max(220,top+sum(row_heights)+65) if kind=='bar' else top+280
    out=[f'<svg role="img" aria-label="{escape(chart["title"],quote=True)}" viewBox="0 0 {width} {height}"><title>{e(chart["title"])}</title>']
    for i,line in enumerate(title_lines):out.append(f'<text x="36" y="{25+i*20}" class="chart-title">{e(line)}</text>')
    out += [f'<text x="430" y="{height-12}" text-anchor="middle">{e(chart["x_label"])}</text><text transform="translate(17 {height/2}) rotate(-90)" text-anchor="middle">{e(chart["y_label"])}</text>']
    if kind=='bar':
        maximum=max((d['count'] for d in data),default=1) or 1;y=top
        for item,lines,h in zip(data,labels,row_heights):
            center=y+h/2;barwidth=item['count']/maximum*360
            for i,line in enumerate(lines):out.append(f'<text x="236" y="{center-(len(lines)-1)*8+i*17+4}" text-anchor="end">{e(line)}</text>')
            out += [f'<rect x="246" y="{center-9}" width="{barwidth}" height="18" fill="#216e73"><title>{e(item["label"])}: {item["count"]}</title></rect>',f'<text x="{254+barwidth}" y="{center+5}">{formatted(item["count"])}</text>'];y+=h
    elif kind=='box':
        b=chart['box'];scale=max(abs(b['min']),abs(b['max']),1);lo=b['min']/scale;span=b['max']/scale-lo
        def px(x):return 80+550*((x/scale-lo)/span if span else .5)
        y=top+85;a,z,q1,med,q3=[px(b[k]) for k in ('min','max','q1','median','q3')]
        out += [f'<line x1="{a}" y1="{y}" x2="{z}" y2="{y}" stroke="#193e42"/><rect x="{q1}" y="{y-25}" width="{max(1,q3-q1)}" height="50" fill="#c3ded8" stroke="#216e73"/><line x1="{med}" y1="{y-25}" x2="{med}" y2="{y+25}" stroke="#193e42"/>']
        # A fixed summary row avoids overlapping labels when quartiles coincide.
        for i,key in enumerate(('min','q1','median','q3','max')):out.append(f'<text x="{75+i*127}" y="{y+75}">{key}: {e(formatted(b[key]))}</text>')
    elif kind=='ecdf':
        points=chart['points'];lo,hi=points[0]['x'],points[-1]['x'];scale=max(abs(lo),abs(hi),1);span=hi/scale-lo/scale
        def px(x):return 80+550*((x/scale-lo/scale)/span if span else .5)
        bottom=top+190;path=f'M {px(lo)} {bottom}'
        for p in points:path+=f' H {px(p["x"])} V {bottom-p["cumulative"]*165}'
        out += [f'<path d="{path}" fill="none" stroke="#216e73" stroke-width="2"/>',f'<text x="35" y="{bottom}">0%</text><text x="30" y="{bottom-160}">100%</text>',f'<text x="80" y="{bottom+22}">{e(formatted(lo))}</text><text x="630" y="{bottom+22}" text-anchor="end">{e(formatted(hi))}</text>']
    elif data:
        maxcount=max(d['count'] for d in data) or 1;barwidth=550/len(data);bottom=top+190
        out += [f'<text x="35" y="{top+20}">{formatted(maxcount)}</text><text x="45" y="{bottom}">0</text>']
        for i,d in enumerate(data):
            h=d['count']/maxcount*165;x=80+i*barwidth
            out.append(f'<rect x="{x}" y="{bottom-h}" width="{max(.5,barwidth-2)}" height="{h}" fill="#216e73"><title>{e(d["label"])}: {d["count"]}</title></rect>')
        out += [f'<text x="80" y="{bottom+22}">{e(formatted(data[0]["low"]) if kind=="histogram" else data[0]["label"])}</text>',f'<text x="630" y="{bottom+22}" text-anchor="end">{e(formatted(data[-1]["high"]) if kind=="histogram" else data[-1]["label"])}</text>']
    out.append('</svg>')
    notes=[]
    if 'coverage' in chart:notes.append('Top10 covers '+formatted(chart['coverage'],True)+f" of {chart['denominator']:,} raw values; remainder is shown separately.")
    if chart.get('omitted_periods'):notes.append(f"{chart['omitted_periods']:,} middle calendar bins omitted; full date counts remain in profile.")
    if chart.get('omitted_points'):notes.append(f"ECDF display approximated with {len(chart['points'])} rank knots; {chart['omitted_points']:,} distinct points omitted.")
    if chart.get('scale')=='log10':notes.append('Additional transformed view: all finite values positive; population skew at least2. Linear view retained.')
    # A table supplies exact plotted values as a text alternative, without raw JSON.
    from .presentation import html_table
    rows=[[d['label'],formatted(d['count'])] for d in data]
    if kind=='ecdf':rows=[[formatted(p['x']),formatted(p['cumulative'],True)] for p in chart['points']]
    if kind=='box':rows=[[k,formatted(chart['box'][k])] for k in ('min','q1','median','q3','max')]
    table=html_table({'caption':'Plotted values','headers':['Value','Cumulative share' if kind=='ecdf' else 'Count' if kind!='box' else 'Measurement'],'rows':rows,'numeric':[1]})
    return '<figure class="chart">'+''.join(out)+''.join('<figcaption>'+e(n)+'</figcaption>' for n in notes)+'<details><summary>Chart values</summary>'+table+'</details></figure>'
