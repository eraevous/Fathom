"""Small local SVG views of saved univariate chart specifications."""

from html import escape


def svg_chart(chart):
    title,xlab,ylab=[escape(chart[k]) for k in ('title','x_label','y_label')]
    data=chart.get('data',[]);kind=chart['kind']
    height=max(190,100+len(data)*28) if kind in {'bar','time'} else 300
    out=[f'<svg role="img" aria-label="{escape(chart["title"],quote=True)}" viewBox="0 0 800 {height}"><title>{title}</title><text x="35" y="25" class="chart-title">{title}</text>',
         f'<text x="440" y="{height-10}" text-anchor="middle">{xlab}</text><text transform="translate(14 {height/2}) rotate(-90)" text-anchor="middle">{ylab}</text>']
    if kind=='box':
        b=chart['box'];scale=max(abs(b['min']),abs(b['max']),1);lo,hi=b['min']/scale,b['max']/scale
        def px(x):return 70+650*((x/scale-lo)/(hi-lo) if hi!=lo else .5)
        a,z,q1,med,q3=[px(b[k]) for k in ('min','max','q1','median','q3')]
        out += [f'<line x1="{a}" y1="120" x2="{z}" y2="120" stroke="#193e42"/><rect x="{q1}" y="85" width="{max(1,q3-q1)}" height="70" fill="#c3ded8" stroke="#216e73"/><line x1="{med}" y1="85" x2="{med}" y2="155" stroke="#193e42"/>']
        for key in ('min','q1','median','q3','max'):
            out.append(f'<text x="{px(b[key])}" y="{185 if key in {"min","median","max"} else 210}" text-anchor="middle">{escape(key)}: {b[key]:.5g}</text>')
    elif kind=='histogram':
        maxcount=max((d['count'] for d in data),default=1) or 1;width=650/max(len(data),1)
        out += [f'<text x="40" y="60">{maxcount}</text><text x="40" y="240">0</text>']
        for i,d in enumerate(data):
            h=d['count']/maxcount*175;x=70+i*width
            out.append(f'<rect x="{x}" y="{235-h}" width="{max(1,width-3)}" height="{h}" fill="#216e73"><title>{escape(d["label"])}: {d["count"]} rows</title></rect>')
        if data:out += [f'<text x="70" y="255">{data[0]["low"]:.5g}</text><text x="720" y="255" text-anchor="end">{data[-1]["high"]:.5g}</text>']
    else:
        maximum=max((d['count'] for d in data),default=1) or 1
        for i,d in enumerate(data):
            y=55+i*28;raw=str(d['label']);name=raw if len(raw)<=28 else raw[:25]+'…'
            out += [f'<text x="35" y="{y+14}">{escape(name)}</text><rect x="280" y="{y}" width="{d["count"]/maximum*400}" height="19" fill="#216e73"/><text x="705" y="{y+14}">{d["count"]}</text>']
    if chart.get('omitted_periods'):out.append(f'<text x="35" y="{height-35}">{chart["omitted_periods"]} middle periods omitted from chart; counts retained in profile.</text>')
    return ''.join(out)+'</svg>'
