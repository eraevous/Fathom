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
    return [ch for col in d.get('columns',[]) for ch in col.get('univariate',{}).get('charts',[])]


def pdf_bytes(d):
    from reportlab import rl_config
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable, PageBreak
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
    def table(rows,widths):
        t=Table([[p(cell) for cell in row] for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9f2ee')),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#b9d3cf')),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4)]))
        story.append(t)
    title,description,basis=identity(d)
    story.extend([p(title,'Title'),p(description),p(basis),p('Unsupported characters are replaced with ?. Exact source text remains in HTML/Markdown and JSON.')])

    class Chart(Flowable):
        def __init__(self,ch):super().__init__();self.ch=ch;self.width=480;self.height=230 if ch['kind']!='bar' else max(180,90+len(ch.get('data',[]))*12)
        def draw(self):
            c=self.canv;ch=self.ch;c.setFont(font,8);c.drawString(4,self.height-15,text(ch['title'])[:110])
            c.drawCentredString(255,5,text(ch['x_label'])[:100]);c.saveState();c.translate(10,self.height/2);c.rotate(90);c.drawCentredString(0,0,text(ch['y_label'])[:80]);c.restoreState()
            c.setFillColor(colors.HexColor('#216e73'));data=ch.get('data',[])
            if ch['kind']=='box':
                b=ch['box'];scale=max(abs(b['min']),abs(b['max']),1);lo=b['min']/scale;span=b['max']/scale-lo
                def x(v):return 55+390*((v/scale-lo)/span if span else .5)
                c.line(x(b['min']),110,x(b['max']),110);c.rect(x(b['q1']),90,max(1,x(b['q3'])-x(b['q1'])),40,fill=0);c.line(x(b['median']),90,x(b['median']),130)
                for i,k in enumerate(('min','q1','median','q3','max')):c.drawString(40,65-i*10,text(k+': '+scalar(b[k])))
            elif data:
                maximum=max(x['count'] for x in data) or 1
                if ch['kind']=='bar':
                    for i,item in enumerate(data):
                        y=self.height-40-i*12;c.drawString(35,y,text(item['label'])[:27]);c.rect(190,y-2,230*item['count']/maximum,8,fill=1,stroke=0);c.drawString(430,y,str(item['count']))
                else:
                    width=390/len(data)
                    for i,item in enumerate(data):c.rect(55+i*width,45,max(.5,width-2),135*item['count']/maximum,fill=1,stroke=0)
                    c.drawString(25,45,'0');c.drawString(25,180,str(maximum));c.drawString(55,30,text(data[0]['label'])[:30]);c.drawRightString(450,30,text(data[-1]['label'])[:30])
            if ch.get('omitted_periods'):c.drawString(30,18,str(ch['omitted_periods'])+' middle periods omitted; see saved profile.')

    if d['kind']=='profile':
        heading('Dictionary')
        table([['Column','Meaning / effective type','Missing / distinct']]+[[c['name'],(c['meaning']['value']+' (human)' if c['meaning'] else 'Unknown meaning')+' / '+c['effective_type']+(' (human override)' if c['override'] else ' (inferred)'),f"{c['missing']}/{c['count']} missing; {c['distinct']} distinct"] for c in d['columns']],[140,240,110])
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
        story.append(p('Source: '+str(d['source'])+'; context: '+str(d['context'])))
        heading('Dataset summary')
        table([['Measure','Snapshot']]+[[name,value] for name,value,_ in summary_rows(d)],[230,260])
        story.append(p('Usefulness: '+(d['purpose'].get('question') or d['purpose'].get('fallback','Reference, understanding, QA and validation.'))))
        story.append(p('The table does not establish domain meaning, causation or fitness for use. Suggested actions require review.'))
        heading('Findings')
    else:
        for name,key in [('Contexts','contexts'),('Context differences','context_differences'),('Measured deltas','deltas'),('Limitations','limitations')]:heading(name);story.append(p(str(d[key])))
    for name,messages in finding_topics(d):
        story.append(p(name,'Heading3'))
        for message in messages:story.append(p(message))
    if d['kind']=='profile':
        heading('Relations')
        story.append(p(d['selection'].get('ranking_rule','Ranking not recorded.')))
        for pair in d['bivariate']:story.append(p(f"{pair['left']} × {pair['right']}: {pair['method']}; {pair['statistics']}; {pair['uncertainty']}"))
        for ch in chart_topics(d):story.extend([PageBreak(),Chart(ch)])
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
    from pptx.chart.data import CategoryChartData
    from pptx.enum.chart import XL_CHART_TYPE
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.util import Inches, Pt
    deck=Presentation();deck.slide_width=Inches(13.333);deck.slide_height=Inches(7.5)
    title,description,basis=identity(d)
    props=deck.core_properties;props.title=title;props.author='Fathom';props.last_modified_by='Fathom';props.created=datetime(2000,1,1);props.modified=datetime(2000,1,1);props.revision=1
    def slide(name,lines=()):
        s=deck.slides.add_slide(deck.slide_layouts[5]);s.shapes.title.text=name
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
        for name,key in [('Contexts','contexts'),('Context differences','context_differences'),('Measured deltas','deltas'),('Limitations','limitations')]:topics(name,[str(d[key])])
    for name,messages in finding_topics(d):topics(name,messages)
    for ch in chart_topics(d):
        s=slide(ch['title']);data=ch.get('data',[])
        if ch['kind']=='box':
            b=ch['box'];scale=max(abs(b['min']),abs(b['max']),1);lo=b['min']/scale;span=b['max']/scale-lo
            def x(v):return Inches(1+11*((v/scale-lo)/span if span else .5))
            for a,z,y,h in [('min','max',3.5,.03),('q1','q3',3,.9),('median','median',3,.9)]:
                s.shapes.add_shape(MSO_SHAPE.RECTANGLE,x(b[a]),Inches(y),max(Inches(.02),x(b[z])-x(b[a])),Inches(h))
            s.shapes.add_textbox(Inches(1),Inches(5),Inches(11),Inches(1)).text_frame.text='X: '+ch['x_label']+'; Y: '+ch['y_label']+'\n'+'; '.join(k+': '+scalar(v) for k,v in b.items())
        elif data:
            values=CategoryChartData();values.categories=[str(v['label']) for v in data];values.add_series('Values (count)',[v['count'] for v in data])
            chart=s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED if ch['kind']=='bar' else XL_CHART_TYPE.COLUMN_CLUSTERED,Inches(.7),Inches(1.6),Inches(12),Inches(5.3),values).chart
            chart.has_legend=False;chart.has_title=True;chart.chart_title.text_frame.text=ch['title']
            chart.category_axis.has_title=True;chart.category_axis.axis_title.text_frame.text=ch['y_label'] if ch['kind']=='bar' else ch['x_label']
            chart.value_axis.has_title=True;chart.value_axis.axis_title.text_frame.text=ch['x_label'] if ch['kind']=='bar' else ch['y_label']
            if ch.get('omitted_periods'):s.notes_slide.notes_text_frame.text=str(ch['omitted_periods'])+' middle periods omitted; full counts in saved profile.'
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
