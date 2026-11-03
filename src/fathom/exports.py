"""Optional, offline, artifact-only serializers with deterministic packaging."""

from datetime import datetime
import hashlib
import io
from importlib.metadata import version
from pathlib import Path
import re
import zipfile
from xml.sax.saxutils import escape

from .renderers import KINDS, repetition_groups, sample_cell, scalar, summary_rows
from .presentation import formatted, column_tables, structured_tables


def finding_topics(d):
    groups=repetition_groups(d) if d['kind']=='profile' else []
    repeated={f['id'] for _,items in groups for f in items}
    for kind,title in KINDS:
        messages=[message for message,items in groups if items and items[0]['kind']==kind]
        messages += [f['message'] for f in d.get('findings',[]) if f['kind']==kind and f['id'] not in repeated]
        if messages:yield title,messages


def identity(d):
    dataset=d.get('dataset',{})
    return (dataset.get('title',{}).get('text','Fathom — '+d['kind']),
            dataset.get('description',{}).get('text','Saved-artifact report'),
            'Title: '+dataset.get('title',{}).get('status','unavailable')+'; description: '+dataset.get('description',{}).get('status','unavailable'))


def chart_topics(d):
    return ([d['missingness_patterns']['chart']] if d.get('missingness_patterns') else [])+[ch for col in d.get('columns',[]) for ch in col.get('univariate',{}).get('charts',[])]


def pdf_bytes(d):
    from reportlab import rl_config
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_RIGHT
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable, KeepTogether
    font='FathomVera'
    if font not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(font,str(Path(rl_config.__file__).parent/'fonts'/'Vera.ttf')))
    supported=pdfmetrics.getFont(font).face.charToGlyph
    replacements=0
    def text(value):
        nonlocal replacements
        value=str(value)
        replacements+=sum(ord(c) not in supported and c not in '\n\r\t' for c in value)
        return ''.join(c if ord(c) in supported or c in '\n\r\t' else '?' for c in value)
    styles=getSampleStyleSheet()
    for style in styles.byName.values():style.fontName=font
    styles['BodyText'].fontSize=8;styles['BodyText'].leading=11;styles['BodyText'].wordWrap='CJK'
    def p(value,style='BodyText'):return Paragraph(escape(text(value)).replace('\n','<br/>'),styles[style])
    story=[]
    def heading(value):story.extend([Spacer(1,10),p(value,'Heading2')])
    right=styles['BodyText'].clone('Numeric');right.alignment=TA_RIGHT
    def table(rows,widths,numeric=()):
        t=Table([[Paragraph(escape(text(cell)),right) if i in numeric else p(cell) for i,cell in enumerate(row)] for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9f2ee')),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#b9d3cf')),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4)]))
        story.append(t)
    title,description,basis=identity(d)
    story.extend([p(title,'Title'),p(description),p(basis),p('Unsupported characters are replaced with ?. Exact source text remains in HTML/Markdown and JSON.')])

    class Chart(Flowable):
        def __init__(self,ch):super().__init__();self.ch=ch;self.width=480;self.height=230 if ch['kind']!='bar' else max(180,90+len(ch.get('data',[]))*12)
        def draw(self):
            c=self.canv;ch=self.ch;c.setFont(font,8)
            c.drawCentredString(255,5,text(ch['x_label'])[:100]);c.saveState();c.translate(10,self.height/2);c.rotate(90);c.drawCentredString(0,0,text(ch['y_label'])[:80]);c.restoreState()
            c.setFillColor(colors.HexColor('#216e73'));data=ch.get('data',[])
            if ch['kind']=='box':
                b=ch['box'];scale=max(abs(b['min']),abs(b['max']),1);lo=b['min']/scale;span=b['max']/scale-lo
                def x(v):return 55+390*((v/scale-lo)/span if span else .5)
                c.line(x(b['min']),110,x(b['max']),110);c.rect(x(b['q1']),90,max(1,x(b['q3'])-x(b['q1'])),40,fill=0);c.line(x(b['median']),90,x(b['median']),130)
                for i,k in enumerate(('min','q1','median','q3','max')):c.drawString(40,65-i*10,text(k+': '+formatted(b[k])))
            elif ch['kind']=='ecdf':
                points=ch['points'];lo,hi=points[0]['x'],points[-1]['x'];scale=max(abs(lo),abs(hi),1);span=hi/scale-lo/scale
                def x(v):return 55+390*((v/scale-lo/scale)/span if span else .5)
                path=c.beginPath();path.moveTo(x(lo),45)
                previous=0
                for point in points:
                    path.lineTo(x(point['x']),45+135*previous);path.lineTo(x(point['x']),45+135*point['cumulative']);previous=point['cumulative']
                c.drawPath(path);c.drawString(20,45,'0%');c.drawString(15,180,'100%');c.drawString(55,30,formatted(lo));c.drawRightString(450,30,formatted(hi))
            elif data:
                maximum=max(x['count'] for x in data) or 1
                if ch['kind']=='bar':
                    for i,item in enumerate(data):
                        y=self.height-40-i*12;label=text(item['label']);label=label if len(label)<=29 else label[:28]+'…'
                        c.drawRightString(180,y,label);end=190+230*item['count']/maximum;c.rect(190,y-2,end-190,8,fill=1,stroke=0);c.drawString(end+5,y,formatted(item['count']))
                else:
                    width=390/len(data)
                    for i,item in enumerate(data):c.rect(55+i*width,45,max(.5,width-2),135*item['count']/maximum,fill=1,stroke=0)
                    first=formatted(data[0]['low']) if ch['kind']=='histogram' else data[0]['label'];last=formatted(data[-1]['high']) if ch['kind']=='histogram' else data[-1]['label']
                    c.drawRightString(48,45,'0');c.drawRightString(48,180,formatted(maximum));c.drawString(55,30,text(first));c.drawRightString(450,30,text(last))
            if ch.get('omitted_periods'):c.drawString(30,18,str(ch['omitted_periods'])+' middle periods omitted; see saved profile.')

    def pdf_chart(ch):
        story.append(KeepTogether([p(ch['title'],'Heading3'),Chart(ch)]))
        if ch.get('omitted_points'):story.append(p(f"Approximate ECDF display: {ch['omitted_points']} distinct points omitted."))
        if 'coverage' in ch:story.append(p('Top10 coverage: '+formatted(ch['coverage'],True)+'; other is the remainder.'))
        if ch['kind']=='bar' and any(len(str(x['label']))>29 for x in ch.get('data',[])):story.append(p('Long chart labels shortened with …; exact labels remain in the core report/artifact.'))
    if d['kind']=='profile':
        heading('Dictionary')
        if d.get('missingness_patterns'):pdf_chart(d['missingness_patterns']['chart'])
        for col in d['columns']:
            heading(col['name'])
            story.append(p((col['meaning']['value']+' (human)' if col['meaning'] else 'Unknown meaning')+' / '+col['effective_type']+(' (human override)' if col['override'] else ' (inferred)')))
            for t in column_tables(col):
                if not t['caption'].startswith(('Column overview','Univariate statistics','Percentiles','Most common nonmissing')):continue
                story.append(p(t['caption'],'Heading3'))
                widths=[245,245] if len(t['headers'])==2 else [290,100,100]
                table([t['headers'],*t['rows']],widths,t['numeric'])
            for ch in col.get('univariate',{}).get('charts',[]):pdf_chart(ch)
        samples=d.get('samples')
        if samples:
            story.append(p(samples['note']+f" Seed: {samples['seed']}; requested: {samples['size']}."))
            for key,name in [('first','First rows'),('last','Last rows'),('random','Random rows')]:
                heading(name)
                for start in range(0,len(samples['columns']),4):
                    names=samples['columns'][start:start+4]
                    rows=[['Input row',*names]]+[[r['position'],*[sample_cell(x) for x in r['values'][start:start+4]]] for r in samples[key]]
                    table(rows,[42]+[448/len(names)]*len(names))
        else:story.append(p('Sample rows unavailable in this saved artifact.'))
        heading('Provenance')
        table([['Field','Value'],['Connector',d['source']['connector']],['Source',d['source']['origin']]]+[[k,formatted(v)] for k,v in sorted(d['context'].items()) if not isinstance(v,(dict,list))],[180,310])
        story.append(p('Full provenance and raw evidence remain in the core report and saved artifact.'))
        heading('Dataset summary')
        table([['Measure','Snapshot']]+[[name,value] for name,value,_ in summary_rows(d)],[230,260])
        story.append(p('Usefulness: '+(d['purpose'].get('question') or d['purpose'].get('fallback','Reference, understanding, QA and validation.'))))
        story.append(p('The table does not establish domain meaning, causation or fitness for use. Suggested actions require review.'))
        heading('Findings')
    else:
        for name,key in [('Contexts','contexts'),('Context differences','context_differences'),('Measured deltas','deltas'),('Limitations','limitations')]:
            heading(name)
            for t in structured_tables(name,d[key]):
                story.append(p(t['caption']));table([t['headers'],*t['rows']],[490/len(t['headers'])]*len(t['headers']),t['numeric'])
    for name,messages in finding_topics(d):
        story.append(p(name,'Heading3'))
        for message in messages:story.append(p(message))
    if d['kind']=='profile':
        heading('Relations')
        story.append(p(d['selection'].get('ranking_rule','Ranking not recorded.')))
        for pair in d['bivariate']:
            story.append(p(f"{pair['left']} × {pair['right']}: {pair['method']}; {pair['uncertainty']}"))
            for t in structured_tables('Relationship statistics',pair['statistics']):
                story.append(p(t['caption']));table([t['headers'],*t['rows']],[490/len(t['headers'])]*len(t['headers']),t['numeric'])
    output=io.BytesIO()
    SimpleDocTemplate(output,pagesize=(612,792),leftMargin=56,rightMargin=56,topMargin=40,bottomMargin=40,title=text(title),author='Fathom',invariant=1,pageCompression=0).build(story)
    return output.getvalue(),{'unsupported_glyph_replacements':replacements}


def normalized_zip(data):
    output=io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(data)) as src,zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as dest:
        for name in sorted(src.namelist()):
            value=src.read(name)
            if name.endswith('.xlsx'):value=normalized_zip(value)
            elif name=='docProps/core.xml':
                value=re.sub(rb'(<dcterms:(?:created|modified)[^>]*>)[^<]*(</dcterms:(?:created|modified)>)',rb'\g<1>2000-01-01T00:00:00Z\g<2>',value)
            info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.create_system=0;info.external_attr=0
            dest.writestr(info,value)
    return output.getvalue()


def pptx_bytes(d):
    from pptx import Presentation
    from pptx.chart.data import CategoryChartData, XyChartData
    from pptx.enum.chart import XL_CHART_TYPE, XL_DATA_LABEL_POSITION, XL_TICK_MARK
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.util import Inches, Pt
    deck=Presentation();deck.slide_width=Inches(13.333);deck.slide_height=Inches(7.5)
    title,description,basis=identity(d)
    props=deck.core_properties;props.title=title;props.author='Fathom';props.last_modified_by='Fathom';props.created=datetime(2000,1,1);props.modified=datetime(2000,1,1);props.revision=1
    def slide(name,lines=()):
        s=deck.slides.add_slide(deck.slide_layouts[5]);s.shapes.title.text=name
        for paragraph in s.shapes.title.text_frame.paragraphs:paragraph.font.size=Pt(24)
        box=s.shapes.add_textbox(Inches(.6),Inches(1.5),Inches(12),Inches(5.5));tf=box.text_frame;tf.word_wrap=True
        for i,line in enumerate(lines):
            p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.text=str(line);p.font.size=Pt(17)
        return s
    def topics(name,lines):
        # Bound text per slide; continuation retains the same single topic.
        chunks=[];current=[];length=0
        for line in lines:
            for start in range(0,max(1,len(line)),280):
                part=line[start:start+280]
                if current and (len(current)>=6 or length+len(part)>850):chunks.append(current);current=[];length=0
                current.append(part);length+=len(part)
        if current or not chunks:chunks.append(current)
        for i,chunk in enumerate(chunks):slide(name+(f' ({i+1}/{len(chunks)})' if len(chunks)>1 else ''),chunk)
    topics(title,[description,basis,'Rule-based observations; suggested actions need human review.'])
    if d['kind']=='profile':topics('Dataset summary',[name+': '+value for name,value,_ in summary_rows(d)])
    else:
        for name,key in [('Contexts','contexts'),('Context differences','context_differences'),('Measured deltas','deltas'),('Limitations','limitations')]:
            lines=[]
            for t in structured_tables(name,d[key]):
                lines.append(t['caption'])
                lines += ['; '.join(h+': '+str(v) for h,v in zip(t['headers'],row)) for row in t['rows']]
            topics(name,lines)
    for name,messages in finding_topics(d):topics(name,messages)
    for ch in chart_topics(d):
        s=slide(ch['title']);data=ch.get('data',[])
        if ch['kind']=='box':
            b=ch['box'];scale=max(abs(b['min']),abs(b['max']),1);lo=b['min']/scale;span=b['max']/scale-lo
            def x(v):return Inches(1+11*((v/scale-lo)/span if span else .5))
            for a,z,y,h in [('min','max',3.5,.03),('q1','q3',3,.9),('median','median',3,.9)]:
                s.shapes.add_shape(MSO_SHAPE.RECTANGLE,x(b[a]),Inches(y),max(Inches(.02),x(b[z])-x(b[a])),Inches(h))
            s.shapes.add_textbox(Inches(1),Inches(5),Inches(11),Inches(1)).text_frame.text='X: '+ch['x_label']+'; Y: '+ch['y_label']+'\n'+'; '.join(k+': '+formatted(b[k]) for k in ('min','q1','median','q3','max'))
        elif data or ch['kind']=='ecdf':
            if ch['kind']=='ecdf':
                values=XyChartData();series=values.add_series('Cumulative share');previous=0
                for point in ch['points']:
                    series.add_data_point(point['x'],previous*100)
                    series.add_data_point(point['x'],point['cumulative']*100);previous=point['cumulative']
                chart_type=XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS
            else:
                categories=[formatted(v['low'])+' – '+formatted(v['high']) if ch['kind']=='histogram' else str(v['label']) for v in data]
                # Native office engines otherwise expand long categories off-slide.
                shortened=[v if len(v)<=42 else v[:41]+'…' for v in categories]
                values=CategoryChartData();values.categories=shortened;values.add_series('Values (count)',[v['count'] for v in data])
                chart_type=XL_CHART_TYPE.BAR_CLUSTERED if ch['kind']=='bar' else XL_CHART_TYPE.COLUMN_CLUSTERED
            chart=s.shapes.add_chart(chart_type,Inches(.7),Inches(1.6),Inches(12),Inches(4.8),values).chart
            chart.has_legend=False;chart.has_title=False
            chart.category_axis.has_title=True;chart.category_axis.axis_title.text_frame.text=ch['y_label'] if ch['kind']=='bar' else ch['x_label']
            chart.value_axis.has_title=True;chart.value_axis.axis_title.text_frame.text=ch['x_label'] if ch['kind']=='bar' else ch['y_label']
            chart.category_axis.tick_labels.font.size=Pt(12);chart.value_axis.tick_labels.font.size=Pt(12)
            chart.value_axis.tick_labels.number_format='#,##0.###'
            if ch['kind']=='ecdf':chart.category_axis.tick_labels.number_format='#,##0.###'
            if ch['kind']=='ecdf':chart.value_axis.minimum_scale=0;chart.value_axis.maximum_scale=100
            else:
                chart.value_axis.minimum_scale=0
                chart.plots[0].has_data_labels=True;labels=chart.plots[0].data_labels;labels.position=XL_DATA_LABEL_POSITION.OUTSIDE_END;labels.font.size=Pt(11);labels.number_format='#,##0;-#,##0;'
            notes=[]
            if ch['kind']!='ecdf' and shortened!=categories:
                notes.append('Long labels shortened with …; full labels in slide notes and artifact.')
                s.notes_slide.notes_text_frame.text='\n'.join(categories)
            if ch.get('omitted_periods'):notes.append(str(ch['omitted_periods'])+' middle bins omitted; full counts in saved profile.')
            if ch.get('omitted_points'):notes.append('Approximate ECDF display; '+str(ch['omitted_points'])+' distinct points omitted.')
            if 'coverage' in ch:notes.append('Top10 covers '+formatted(ch['coverage'],True)+' of raw values; other is remainder.')
            if ch.get('scale')=='log10':notes.append('Additional log10 view of all positive finite values; linear view retained.')
            if notes:
                box=s.shapes.add_textbox(Inches(.7),Inches(6.6),Inches(12),Inches(.65));box.text_frame.text=' '.join(notes)
                for paragraph in box.text_frame.paragraphs:paragraph.font.size=Pt(12)
    output=io.BytesIO();deck.save(output)
    return normalized_zip(output.getvalue()),{'slides':len(deck.slides)}


def export_bundle(result,formats):
    serializers={'pdf':pdf_bytes,'pptx':pptx_bytes};files={}
    status={'artifact_sha256':hashlib.sha256(result.to_json().encode()).hexdigest(),'formats':{}}
    for fmt in sorted(set(formats)):
        if fmt not in serializers:raise ValueError('Unsupported export format: '+fmt)
        try:
            data,details=serializers[fmt](result.document)
            files['report.'+fmt]=data
            status['formats'][fmt]={'status':'written','serializer':{'package':'reportlab' if fmt=='pdf' else 'python-pptx','version':version('reportlab' if fmt=='pdf' else 'python-pptx')},**details}
        except ImportError:
            status['formats'][fmt]={'status':'unavailable','reason':f'Install fathom-guide[{fmt}] to enable this local export.'}
    return files,status
