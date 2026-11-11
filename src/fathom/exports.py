"""Optional, offline, artifact-only serializers with deterministic packaging."""

from datetime import datetime
import hashlib
import io
from importlib.metadata import version
from pathlib import Path
import re
import zipfile
from html import escape as html_escape

from .renderers import KINDS, omitted, omitted_notes, repetition_groups, sample_cell, scalar, summary_rows
from .presentation import formatted, column_tables, structured_tables, formatted_examples, display_charts, top_n_reason, original_tick
from .target import target_tables
from .palette import LIGHT as C,KIND_COLOURS
from .report_style import runs
from .summary_view import summary_panels,report_options
from .identifier_view import identifier_columns,identifier_tables
from .finding_view import finding_tree


def escape(value):
    """XML text escaping without saxutils' eager urllib.request import."""
    return html_escape(value, quote=False)


def finding_topics(d):
    groups=repetition_groups(d) if d['kind']=='profile' else []
    repeated={f['id'] for _,items in groups for f in items}
    for kind,title in KINDS:
        messages=[message for message,items in groups if items and items[0]['kind']==kind]
        messages += [finding_tree(f,d)['text']+''.join('\n  - '+line for line in finding_tree(f,d)['children']) for f in d.get('findings',[]) if f['kind']==kind and f['id'] not in repeated]
        if messages:yield title,messages


def identity(d):
    dataset=d.get('dataset',{})
    return (dataset.get('title',{}).get('text','Fathom — '+d['kind']),
            dataset.get('description',{}).get('text','Saved-artifact report'),
            'Title: '+dataset.get('title',{}).get('status','unavailable')+'; description: '+dataset.get('description',{}).get('status','unavailable'))


def chart_topics(d):
    return d.get('target_analysis',{}).get('charts',[])+([d['missingness_patterns']['chart']] if d.get('missingness_patterns') else [])+[ch for col in d.get('columns',[]) for ch in display_charts(col)]


def summary_chart_topics(d):
    """Presentation budget only: cover columns before taking extra chart variants."""
    selected=list(d.get('target_analysis',{}).get('charts',[])[:5])
    if d.get('missingness_patterns') and d['overview']['missing_cells']:
        selected.append(d['missingness_patterns']['chart'])
    action_columns={name for f in d.get('findings',[]) if f['kind']=='action' for name in f.get('columns',[])}
    columns=sorted(enumerate(d.get('columns',[])),key=lambda x:(x[1]['name'] not in action_columns,x[0]))
    for _,col in columns:
        if col.get('univariate',{}).get('role')=='identifier':continue
        charts=display_charts(col)
        if not charts:continue
        priority=lambda ch:0 if ch.get('scale')=='log10' else {'time':1,'histogram':2,'bar':3,'ecdf':4,'box':5}.get(ch['kind'],6)
        selected.append(min(charts,key=priority))
        if len(selected)>=7:break
    return selected


def summary_topics(d):
    if d['kind']=='profile':
        yield 'Dataset summary',[name+': '+value for name,value,_ in summary_rows(d)]+omitted_notes(d)
        messages=dict(finding_topics(d))
        for title in ('Suggested actions','Observations','Open questions'):
            if title=='Observations' and d.get('target_analysis',{}).get('ranked'):
                ta=d['target_analysis'];yield 'Target ranking (descriptive, not causal)',[r['column']+': '+r['measure']+' '+formatted(r['value'])+'; n='+str(r['n'])+('; selected' if r['selected'] else '; beyond detail budget') for r in ta['ranked'][:5]]+['Full ranking, exclusions and group summaries in the report.'];continue
            items=messages.get(title,[])
            yield title,[x[:210]+('… [see full report]' if len(x)>210 else '') for x in items[:5]]+[f'Showing {min(5,len(items))} of {len(items)} items; all evidence and uncertainty remain in the full report.']
    else:
        for name,key in [('Contexts','contexts'),('Context differences','context_differences'),('Measured deltas','deltas'),('Limitations','limitations')]:
            lines=[]
            for t in structured_tables(name,d[key]):
                lines.extend(t['caption']+': '+'; '.join(h+': '+str(v) for h,v in zip(t['headers'],row)) for row in t['rows'])
            yield name,[x[:210]+('… [full report]' if len(x)>210 else '') for x in lines[:5]]+[f'Showing {min(5,len(lines))} of {len(lines)} measures; full detail in saved artifact/full deck.']


def pdf_bytes(d,report=None):
    from reportlab import rl_config
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_RIGHT
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable, KeepTogether, ListFlowable
    font='FathomVera'
    if font not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(font,str(Path(rl_config.__file__).parent/'fonts'/'Vera.ttf')))
    for suffix,filename in [('Bold','VeraBd.ttf'),('Oblique','VeraIt.ttf'),('BoldOblique','VeraBI.ttf')]:
        if font+'-'+suffix not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont(font+'-'+suffix,str(Path(rl_config.__file__).parent/'fonts'/filename)))
    pdfmetrics.registerFontFamily(font,normal=font,bold=font+'-Bold',italic=font+'-Oblique',boldItalic=font+'-BoldOblique')
    supported=pdfmetrics.getFont(font).face.charToGlyph
    replacements=0
    def text(value):
        nonlocal replacements
        value=str(value)
        replacements+=sum(ord(c) not in supported and c not in '\n\r\t' for c in value)
        return ''.join(c if ord(c) in supported or c in '\n\r\t' else '?' for c in value)
    styles=getSampleStyleSheet()
    for style in styles.byName.values():style.fontName=font;style.textColor=colors.HexColor(C['ink'])
    styles['BodyText'].fontSize=8;styles['BodyText'].leading=11;styles['BodyText'].wordWrap='CJK'
    columns=[c['name'] for c in d.get('columns',[])]
    def p(value,style='BodyText'):
        # Vera has no right-arrow glyph; spell out the generated gate connector.
        if str(value).startswith('gate: '):value=str(value).replace(' → ',' leads to ')
        if str(value).startswith('Examples: '):return Paragraph('Examples: <font name="Courier">'+escape(text(str(value)[10:]))+'</font>',styles[style])
        markup=[]
        inferred=(str(value)==identity(d)[1] and d.get('dataset',{}).get('description',{}).get('status')=='inferred') or (style=='Title' and d.get('dataset',{}).get('title',{}).get('status')=='inferred')
        for part,role in runs(text(value),columns=columns,verdict=style=='BodyText',inferred=inferred):
            safe=escape(part).replace('\n','<br/>')
            markup.append('<b>'+safe+'</b>' if role=='verdict' else '<i>'+safe+'</i>' if role=='inferred' else '<font name="Courier">'+safe+'</font>' if role=='literal' else safe)
        return Paragraph(''.join(markup),styles[style])
    story=[]
    def heading(value):story.extend([Spacer(1,10),p(value,'Heading2')])
    right=styles['BodyText'].clone('Numeric');right.alignment=TA_RIGHT
    def table(rows,widths,numeric=()):
        t=Table([[Paragraph(escape(text(cell)),right) if i in numeric else p(cell) for i,cell in enumerate(row)] for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor(C['tint'])),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor(C['soft_border'])),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4)]))
        story.append(t)
    title,description,basis=identity(d)
    story.extend([p(title,'Title'),p(description),p(basis),p('Unsupported characters are replaced with ?. Exact source text remains in HTML/Markdown and JSON.')])

    if d['kind']=='profile' and identifier_columns(d):
        heading('Identifiers')
        story.append(p('Identifier role columns are excluded from distribution summaries and target ranking. Numeric label gaps are not missing records.'))
        for _,col in identifier_columns(d):
            story.append(p(col['name']+' — '+col['univariate'].get('role_basis','unknown'),'Heading3'))
            for t in identifier_tables(col):table([t['headers'],*t['rows']],[490/len(t['headers'])]*len(t['headers']),t['numeric'])
    if d['kind']=='profile':
        heading('Distribution summaries')
        story.append(p('Stored metrics only; n valid/finite/nonmissing; missing share uses all rows. Top value share uses nonmissing values; text entropy/length use stored raw lexemes including blanks. Parse coverage is not calendar completeness. Unavailable statistics are not reconstructed.'))
        for panel in summary_panels(d,report,max_columns=5):
            story.append(p(panel['caption'],'Heading3'))
            widths=[105]+[385/(len(panel['headers'])-1)]*(len(panel['headers'])-1)
            table([panel['headers'],*panel['rows']],widths)

    class Chart(Flowable):
        def __init__(self,ch):
            super().__init__();self.ch=ch;self.width=480
            if ch['kind'] in {'scatter','group_box','rates'}:
                from .target_marks import plot_marks
                self.height=min(600,plot_marks(ch)[1]*480/560+50)
            else:self.height=140 if ch['kind']=='box' else 250 if ch['kind']!='bar' else max(200,110+len(ch.get('data',[]))*12)
        def draw(self):
            c=self.canv;ch=self.ch;c.setFont(font,8);c.setFillColor(colors.HexColor(C['ink']));c.setStrokeColor(colors.HexColor(C['accent']))
            from .charts import axis_ticks, linear_ticks, count_ticks
            from .presentation import tick_label
            def wrapped(value,y):
                import textwrap
                for line in textwrap.wrap(text(value),100):c.drawString(10,y,line);y-=10
            if ch['kind']!='box':wrapped('Y: '+ch['y_label'],self.height-10)
            wrapped('X: '+ch['x_label'],20)
            if ch['kind'] in {'scatter','group_box','rates'}:
                from .target_marks import plot_marks
                w,h,marks=plot_marks(ch);factor=min(480/w,(self.height-50)/h)
                for kind,*v in marks:
                    if kind=='line':c.setStrokeColor(colors.HexColor(v[4]));c.line(v[0]*factor,self.height-30-v[1]*factor,v[2]*factor,self.height-30-v[3]*factor)
                    elif kind=='rect':c.setFillColor(colors.HexColor(v[4]));c.rect(v[0]*factor,self.height-30-(v[1]+v[3])*factor,v[2]*factor,v[3]*factor,fill=1,stroke=0)
                    elif kind=='circle':c.setFillColor(colors.HexColor(v[3]));c.circle(v[0]*factor,self.height-30-v[1]*factor,v[2]*factor,fill=1,stroke=0)
                    else:
                        c.setFillColor(colors.HexColor(C['ink']));c.setFont(font,v[4]*factor)
                        draw={'start':c.drawString,'middle':c.drawCentredString,'end':c.drawRightString}[v[3]];draw(v[0]*factor,self.height-30-v[1]*factor,text(v[2]))
                return
            c.setFillColor(colors.HexColor(C['accent']));data=ch.get('data',[])
            if ch['kind']=='box':
                b=ch['box'];scale=max(abs(b['min']),abs(b['max']),1);lo=b['min']/scale;span=b['max']/scale-lo
                def x(v):return 55+390*((v/scale-lo)/span if span else .5)
                c.line(x(b['min']),100,x(b['max']),100);c.rect(x(b['q1']),93,max(1,x(b['q3'])-x(b['q1'])),14,fill=0);c.line(x(b['median']),93,x(b['median']),107)
                for i,k in enumerate(('min','q1','median','q3','max')):c.drawString(40,65-i*8,text(k+': '+formatted(b[k])))
                for value in linear_ticks(b['min'],b['max']):c.drawCentredString(x(value),120,tick_label(value))
            elif ch['kind']=='ecdf':
                points=ch['points'];lo,hi=points[0]['x'],points[-1]['x'];scale=max(abs(lo),abs(hi),1);span=hi/scale-lo/scale
                def x(v):return 55+390*((v/scale-lo/scale)/span if span else .5)
                path=c.beginPath();path.moveTo(x(lo),45)
                previous=0
                for point in points:
                    path.lineTo(x(point['x']),45+135*previous);path.lineTo(x(point['x']),45+135*point['cumulative']);previous=point['cumulative']
                c.drawPath(path)
                for value in linear_ticks(lo,hi):c.drawCentredString(x(value),35,original_tick(ch,value))
                for value in linear_ticks(0,1):c.drawRightString(48,45+135*value,formatted(value,True))
            elif data:
                maximum=max(x['count'] for x in data) or 1
                if ch['kind']=='bar':
                    for value in count_ticks(maximum):c.drawCentredString(190+230*value/maximum,35,tick_label(value))
                    for i,item in enumerate(data):
                        y=self.height-40-i*12;label=text(item['label']);label=label if len(label)<=29 else label[:28]+'…'
                        c.drawRightString(180,y,label);end=190+230*item['count']/maximum;c.rect(190,y-2,end-190,8,fill=1,stroke=0);c.drawString(end+5,y,formatted(item['count']))
                else:
                    width=390/len(data)
                    for i,item in enumerate(data):c.rect(55+i*width,45,max(.5,width-2),135*item['count']/maximum,fill=1,stroke=0)
                    first=formatted(data[0]['low']) if ch['kind']=='histogram' else data[0]['label'];last=formatted(data[-1]['high']) if ch['kind']=='histogram' else data[-1]['label']
                    for value in count_ticks(maximum):c.drawRightString(48,45+135*value/maximum,tick_label(value))
                    if ch['kind']=='histogram':
                        lo,hi=data[0]['low'],data[-1]['high'];scale=max(abs(lo),abs(hi),1);span=hi/scale-lo/scale
                        for value in axis_ticks(ch,lo,hi):c.drawCentredString(55+390*((value/scale-lo/scale)/span if span else .5),35,original_tick(ch,value))
                    else:
                        for i in sorted(set(round(j*(len(data)-1)/4) for j in range(5))):c.drawCentredString(55+390*((i+.5)/len(data)),35,text(data[i]['label']))
            if ch.get('omitted_periods'):c.drawString(30,18,str(ch['omitted_periods'])+' middle periods omitted; see saved profile.')

    def pdf_chart(ch):
        story.append(KeepTogether([p(ch['title'],'Heading3'),Chart(ch)]))
        if ch['kind'] in {'scatter','group_box','rates'}:
            from .target_marks import coverage_note
            story.append(p(coverage_note(ch)))
        if ch.get('omitted_points') and ch['kind']=='ecdf':story.append(p(f"Approximate ECDF display: {ch['omitted_points']} distinct points omitted."))
        if 'coverage' in ch:story.append(p('Top10 coverage: '+formatted(ch['coverage'],True)+'; other is the remainder.'))
        if ch.get('coverage_counts'):
            s=ch['coverage_counts'];story.append(p(f"Positive log view: {s['positive']:,} positives; zeros excluded: {s['zeros']:,}; negatives excluded: {s['negatives']:,}; invalid excluded: {s['invalid']:,}."))
        if ch.get('whole_number_bins'):
            from .charts import whole_note
            story.append(p(whole_note(ch)))
        if ch['kind']=='bar' and any(len(str(x['label']))>29 for x in ch.get('data',[])):story.append(p('Long chart labels shortened with …; exact labels remain in the core report/artifact.'))
    if d['kind']=='profile':
        heading('Dictionary')
        if d.get('missingness_patterns'):pdf_chart(d['missingness_patterns']['chart'])
        for col in d['columns']:
            heading(col['name'])
            story.append(p((col['meaning']['value']+' (human)' if col['meaning'] else 'Unknown meaning')+' / '+col['effective_type']+(' (human override)' if col['override'] else ' (inferred)')))
            story.append(p('Examples: '+', '.join(formatted_examples(col))))
            if top_n_reason(col):story.append(p(top_n_reason(col)))
            for t in column_tables(col):
                if not t['caption'].startswith(('Column overview','Univariate statistics','Percentiles','Most common nonmissing')):continue
                story.append(p(t['caption'],'Heading3'))
                widths=[245,245] if len(t['headers'])==2 else [290,100,100]
                table([t['headers'],*t['rows']],widths,t['numeric'])
            for ch in display_charts(col):pdf_chart(ch)
        samples=d.get('samples')
        if samples:
            story.append(p(samples['note']+f" Seed: {samples['seed']}; requested: {samples['size']}."))
            for key,name in [('first','First rows'),('last','Last rows'),('random','Random rows')]:
                heading(name)
                for start in range(0,len(samples['columns']),4):
                    names=samples['columns'][start:start+4]
                    rows=[['Input row',*names]]+[[r['position'],*[sample_cell(x) for x in r['values'][start:start+4]]] for r in samples[key]]
                    table(rows,[42]+[448/len(names)]*len(names))
        else:story.append(p(next((n for n in omitted_notes(d) if 'sections.samples' in n),'Sample rows unavailable in this saved artifact.')))
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
        for message in messages:
            parts=message.split('\n  - ')
            if len(parts)>1:
                for start in range(1,len(parts),8):
                    story.append(KeepTogether([p(parts[0]+(' (continued)' if start>1 else '')),ListFlowable([p(line) for line in parts[start:start+8]],bulletType='bullet',leftIndent=16,bulletFontName=font,bulletFontSize=8)]))
            else:story.append(p(parts[0]))
    if d['kind']=='profile':
        heading('Relations')
        story.append(p(d['selection'].get('ranking_rule','Ranking not recorded.')))
        ta=d.get('target_analysis');story.append(p(ta['reason']+' '+ta['grouping_policy']+' '+ta['warning'] if ta else 'Target analysis unavailable in legacy artifact.'))
        for t in target_tables(d):
            story.append(p(t['caption'],'Heading3'));table([t['headers'],*t['rows']],[90,35,40,55,170,100] if len(t['headers'])==6 else [490/len(t['headers'])]*len(t['headers']),t['numeric'])
        if ta:
            for ch in ta['charts']:pdf_chart(ch)
        for pair in d['bivariate']:
            story.append(p(f"{pair['left']} × {pair['right']}: {pair['method']}; {pair['uncertainty']}"))
            for t in structured_tables('Relationship statistics',pair['statistics']):
                story.append(p(t['caption']));table([t['headers'],*t['rows']],[490/len(t['headers'])]*len(t['headers']),t['numeric'])
    output=io.BytesIO()
    def page_background(canvas,doc):
        canvas.saveState();canvas.setFillColor(colors.HexColor(C['panel']));canvas.rect(0,0,612,792,stroke=0,fill=1);canvas.restoreState()
    SimpleDocTemplate(output,pagesize=(612,792),leftMargin=56,rightMargin=56,topMargin=40,bottomMargin=40,title=text(title),author='Fathom',invariant=1,pageCompression=0).build(story,onFirstPage=page_background,onLaterPages=page_background)
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


def target_slide_views(chart):
    """Bound tall target panels for an8pt floor; preserve all groups/levels in full views."""
    if chart['kind'] not in {'group_box','rates'}:return [chart]
    from .target_marks import plot_marks
    if plot_marks(chart)[1]<=650:return [chart]
    rows=chart['data'];views=[];separate_legend=chart['kind']=='rates' and len(chart['levels'])>5
    domain=None
    if chart['kind']=='group_box':
        boxes=[r['box'] for r in rows if r.get('box')]
        if boxes:domain=(min(b['min'] for b in boxes),max(b['max'] for b in boxes))
    for start in range(0,len(rows),8):
        end=min(start+8,len(rows));view={**chart,'data':rows[start:end],
            'title':chart['title']+f' — groups {start+1}–{end}/{len(rows)}',
            'show_legend':not separate_legend,'scope_note':f'Panel shows groups {start+1}–{end} of {len(rows)}; coverage counts describe the whole relationship.'}
        if domain:view['x_domain']=domain
        views.append(view)
    if separate_legend:
        for start in range(0,len(chart['levels']),10):
            end=min(start+10,len(chart['levels']))
            views.append({**chart,'kind':'target_legend','data':[],
                'legend_indices':list(range(start,end)),
                'title':chart['title']+f' — legend {start+1}–{end}/{len(chart["levels"])}'})
    return views


def pptx_bytes(d,full=False,report=None):
    from pptx import Presentation
    from pptx.chart.data import CategoryChartData, XyChartData
    from pptx.enum.chart import XL_CHART_TYPE, XL_DATA_LABEL_POSITION, XL_TICK_MARK
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.util import Inches, Pt
    from pptx.enum.text import PP_ALIGN
    from pptx.dml.color import RGBColor
    deck=Presentation();deck.slide_width=Inches(13.333);deck.slide_height=Inches(7.5)
    title,description,basis=identity(d)
    props=deck.core_properties;props.title=title;props.author='Fathom';props.last_modified_by='Fathom';props.created=datetime(2000,1,1);props.modified=datetime(2000,1,1);props.revision=1
    def paint(shape):
        shape.fill.solid();shape.fill.fore_color.rgb=RGBColor.from_string(C['accent'][1:]);shape.line.fill.background();return shape
    def slide(name,lines=(),enumeration=False):
        s=deck.slides.add_slide(deck.slide_layouts[5]);s.shapes.title.text=name
        s.background.fill.solid();s.background.fill.fore_color.rgb=RGBColor.from_string(C['panel'][1:])
        for paragraph in s.shapes.title.text_frame.paragraphs:
            paragraph.font.size=Pt(24);paragraph.font.color.rgb=RGBColor.from_string(C['ink'][1:])
            if name==title and d.get('dataset',{}).get('title',{}).get('status')=='inferred':paragraph.font.italic=True
        box=s.shapes.add_textbox(Inches(.6),Inches(1.5),Inches(12),Inches(5.5));tf=box.text_frame;tf.word_wrap=True
        expanded=[(part.removeprefix('  - '),1 if part.startswith('  - ') else 0) for line in lines for part in str(line).split('\n') if part]
        for i,(line,depth) in enumerate(expanded):
            p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.font.size=Pt(15 if depth else 17);p.font.color.rgb=RGBColor.from_string(C['ink'][1:]);p.level=depth
            if enumeration or depth:
                from pptx.oxml.xmlchemy import OxmlElement
                pr=p._p.get_or_add_pPr();pr.set('marL',str(228600+depth*228600));pr.set('indent','-114300')
                bullet=OxmlElement('a:buChar');bullet.set('char','•');pr.insert_element_before(bullet,'a:tabLst','a:defRPr','a:extLst')
            inferred=str(line)==description and d.get('dataset',{}).get('description',{}).get('status')=='inferred'
            for part,role in runs(line,columns=[c['name'] for c in d.get('columns',[])],verdict=True,inferred=inferred):
                run=p.add_run();run.text=part;run.font.bold=role=='verdict';run.font.italic=role=='inferred';run.font.color.rgb=RGBColor.from_string(C['ink'][1:])
                if role=='literal':run.font.name='Courier New'
        return s
    def topics(name,lines):
        # Keep a complete small finding together; repeat context for a long continuation.
        chunks=[];current=[];length=0
        for message in lines:
            parts=[part for part in message.split('\n') if part];size=sum(map(len,parts))
            if len(parts)<=10 and size<=950:
                if current and (len(current)+len(parts)>10 or length+size>950):chunks.append(current);current=[];length=0
                current.extend(parts);length+=size
            else:
                if current:chunks.append(current);current=[];length=0
                parent=parts[0] if parts else name
                for part in parts:
                    if current and (len(current)>=10 or length+len(part)>950):chunks.append(current);current=[parent+' (continued)'];length=len(parent)+12
                    current.append(part);length+=len(part)
                if current:chunks.append(current);current=[];length=0
        if current or not chunks:chunks.append(current)
        for i,chunk in enumerate(chunks):slide(name+(f' ({i+1}/{len(chunks)})' if len(chunks)>1 else ''),chunk,enumeration=len(lines)>=3)
    available=chart_topics(d);requested=available if full else summary_chart_topics(d)
    all_panels=summary_panels(d,report,max_columns=6,max_rows=10) if d['kind']=='profile' else []
    if full:panels=all_panels
    else:
        panels=[];seen=set()
        for panel in all_panels:
            typ=panel['caption'].split(' column metrics')[0]
            if typ not in seen and len(panels)<5:panels.append(panel);seen.add(typ)
        for panel in all_panels:
            if len(panels)>=5:break
            if panel not in panels:panels.append(panel)
    chosen=[];remaining=7-len(panels)
    for ch in requested:
        cost=len(target_slide_views(ch))
        if full or cost<=remaining:
            chosen.append(ch);remaining-=cost
    views=[view for ch in chosen for view in target_slide_views(ch)]
    if not full:
        slide(title,[description,basis,f'Summary deck: {len(chosen)} of {len(available)} charts; bounded findings. Multi-panel charts share the7chart-slide budget. Use --deck full for all topics.','Rule-based observations; suggested actions need human review.',f'Summary tables: {len(panels)} of {len(all_panels)} panels; configured orientation. Use --deck full for omitted panels.'])
        for name,lines in summary_topics(d):slide(name,lines,enumeration=len(lines)>=3)
    else:
        topics(title,[description,basis,'Full deck: all available topics and charts. Rule-based observations require review.'])
    for panel in panels:
        s=slide(panel['caption']);grid=[panel['headers'],*panel['rows']]
        shape=s.shapes.add_table(len(grid),len(grid[0]),Inches(.6),Inches(1.6),Inches(12),Inches(min(5.1,.42*len(grid))));table=shape.table
        table.columns[0].width=Inches(2.2)
        for col in list(table.columns)[1:]:col.width=Inches(9.8/(len(grid[0])-1))
        for ri,row in enumerate(grid):
            for ci,value in enumerate(row):
                cell=table.cell(ri,ci);cell.text=str(value);cell.fill.solid();cell.fill.fore_color.rgb=RGBColor.from_string(C['tint' if ri==0 else 'panel'][1:])
                for para in cell.text_frame.paragraphs:para.font.size=Pt(13);para.font.color.rgb=RGBColor.from_string(C['ink'][1:])
    if d['kind']=='profile' and identifier_columns(d):
        for _,col in identifier_columns(d):
            if full:
                for t in identifier_tables(col):topics('Identifier: '+col['name'],[t['caption']]+['; '.join(str(v) for v in r) for r in t['rows']])
    if full and d['kind']=='profile':topics('Dataset summary',[name+': '+value for name,value,_ in summary_rows(d)])
    elif full:
        for name,key in [('Contexts','contexts'),('Context differences','context_differences'),('Measured deltas','deltas'),('Limitations','limitations')]:
            lines=[]
            for t in structured_tables(name,d[key]):
                lines.append(t['caption'])
                lines += ['; '.join(h+': '+str(v) for h,v in zip(t['headers'],row)) for row in t['rows']]
            topics(name,lines)
    if full:
        for name,messages in finding_topics(d):topics(name,messages)
    for ch in views:
        s=slide(ch['title']);data=ch.get('data',[])
        if ch['kind']=='target_legend':
            from .palette import CATEGORICAL as PALETTE
            from pptx.dml.color import RGBColor
            for i,index in enumerate(ch['legend_indices']):
                shape=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(.9),Inches(1.75+i*.36),Inches(.16),Inches(.16))
                shape.fill.solid();shape.fill.fore_color.rgb=RGBColor.from_string(PALETTE[index].removeprefix('#'));shape.line.fill.background()
                for style in shape._element.xpath('./p:style'):shape._element.remove(style)
                label=s.shapes.add_textbox(Inches(1.2),Inches(1.7+i*.36),Inches(11.3),Inches(.3));label.text_frame.text=ch['levels'][index]
                label.text_frame.margin_top=0;label.text_frame.margin_bottom=0
                for para in label.text_frame.paragraphs:para.font.size=Pt(14)
            note=s.shapes.add_textbox(Inches(.7),Inches(6.3),Inches(12),Inches(.5));note.text_frame.text='Target category colors are shared across every group panel; full labels are retained here.'
            for para in note.text_frame.paragraphs:para.font.size=Pt(12)
        elif ch['kind'] in {'scatter','group_box','rates'}:
            from .target_marks import plot_marks,coverage_note
            from pptx.dml.color import RGBColor
            w,h,marks=plot_marks(ch);factor=min(11.8/w,4.7/h);offset=(13.333-w*factor)/2
            for kind,*v in marks:
                if kind=='text':
                    size=max(8,min(13,v[4]*factor*72))
                    width=min(1.3,max(.3,len(v[2])*size*.65/72+.1)) if v[3]=='middle' else 1.6 if v[3]=='end' else 6
                    left=offset+v[0]*factor-(width/2 if v[3]=='middle' else width if v[3]=='end' else 0)
                    box=s.shapes.add_textbox(Inches(left),Inches(1.5+v[1]*factor)-Pt(size),Inches(width),Pt(size*1.15))
                    box.text_frame.text=v[2];box.text_frame.word_wrap=False
                    box.text_frame.margin_top=0;box.text_frame.margin_bottom=0;box.text_frame.margin_left=0;box.text_frame.margin_right=0
                    for para in box.text_frame.paragraphs:para.font.size=Pt(size);para.alignment=PP_ALIGN.CENTER if v[3]=='middle' else PP_ALIGN.RIGHT if v[3]=='end' else PP_ALIGN.LEFT
                    continue
                if kind=='line':
                    x,y,x2,y2,color=v;ww=max(.008,abs(x2-x)*factor);hh=max(.008,abs(y2-y)*factor)
                    shape=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(offset+min(x,x2)*factor),Inches(1.5+min(y,y2)*factor),Inches(ww),Inches(hh))
                elif kind=='rect':
                    x,y,ww,hh,color=v;shape=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(offset+x*factor),Inches(1.5+y*factor),Inches(max(.001,ww*factor)),Inches(hh*factor))
                else:
                    x,y,r,color=v;shape=s.shapes.add_shape(MSO_SHAPE.OVAL,Inches(offset+(x-r)*factor),Inches(1.5+(y-r)*factor),Inches(2*r*factor),Inches(2*r*factor))
                shape.fill.solid();shape.fill.fore_color.rgb=RGBColor.from_string(color.removeprefix('#'));shape.line.fill.background()
                for style in shape._element.xpath('./p:style'):shape._element.remove(style)
            box=s.shapes.add_textbox(Inches(.6),Inches(6.2),Inches(12),Inches(1));box.text_frame.word_wrap=True;box.text_frame.text='X: '+ch['x_label']+'; Y: '+ch['y_label']+'\n'+coverage_note(ch)+(' '+ch['scope_note'] if ch.get('scope_note') else '')
            for para in box.text_frame.paragraphs:para.font.size=Pt(11)
        elif ch['kind']=='box':
            b=ch['box'];scale=max(abs(b['min']),abs(b['max']),1);lo=b['min']/scale;span=b['max']/scale-lo
            def x(v):return Inches(1+11*((v/scale-lo)/span if span else .5))
            for a,z,y,h in [('min','max',3.4,.02),('q1','q3',3.3,.2),('median','median',3.3,.2)]:
                paint(s.shapes.add_shape(MSO_SHAPE.RECTANGLE,x(b[a]),Inches(y),max(Inches(.02),x(b[z])-x(b[a])),Inches(h)))
            from .charts import linear_ticks
            from .presentation import tick_label
            for value in linear_ticks(b['min'],b['max']):
                paint(s.shapes.add_shape(MSO_SHAPE.RECTANGLE,x(value),Inches(4.2),Inches(.01),Inches(.1)))
                label=s.shapes.add_textbox(x(value)-Inches(.5),Inches(4.35),Inches(1),Inches(.35))
                label.text_frame.text=tick_label(value)
                for paragraph in label.text_frame.paragraphs:
                    paragraph.font.size=Pt(12);paragraph.alignment=PP_ALIGN.CENTER
            s.shapes.add_textbox(Inches(1),Inches(5),Inches(11),Inches(1)).text_frame.text='X: '+ch['x_label']+'\n'+'; '.join(k+': '+formatted(b[k]) for k in ('min','q1','median','q3','max'))
        elif data or ch['kind']=='ecdf':
            if ch['kind']=='ecdf':
                values=XyChartData();series=values.add_series('Cumulative share');previous=0
                for point in ch['points']:
                    series.add_data_point(10**point['x'] if ch.get('scale')=='log10' else point['x'],previous*100)
                    series.add_data_point(10**point['x'] if ch.get('scale')=='log10' else point['x'],point['cumulative']*100);previous=point['cumulative']
                chart_type=XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS
            else:
                categories=[original_tick(ch,v['low'])+' – '+original_tick(ch,v['high']) if ch['kind']=='histogram' and not ch.get('whole_number_bins') else str(v['label']) for v in data]
                # Native office engines otherwise expand long categories off-slide.
                shortened=[v if len(v)<=42 else v[:41]+'…' for v in categories]
                if ch.get('tail'):
                    # Sparse whole-number tail (spec 028): native charts have no inset, so tail values sit at
                    # the matching end of the category axis, labelled; counts stay exact.
                    low=[v for v in ch['tail'] if v['side']=='low'];high=[v for v in ch['tail'] if v['side']=='high']
                    shortened=[v['label']+' (tail)' for v in low]+shortened+[v['label']+' (tail)' for v in high];data=low+list(data)+high
                values=CategoryChartData();values.categories=shortened;values.add_series('Values (count)',[v['count'] for v in data])
                chart_type=XL_CHART_TYPE.BAR_CLUSTERED if ch['kind']=='bar' else XL_CHART_TYPE.COLUMN_CLUSTERED
            chart=s.shapes.add_chart(chart_type,Inches(.7),Inches(1.6),Inches(12),Inches(4.8),values).chart
            chart.has_legend=False;chart.has_title=False
            for series in chart.series:
                series.format.fill.solid();series.format.fill.fore_color.rgb=RGBColor.from_string(C['accent'][1:]);series.format.line.color.rgb=RGBColor.from_string(C['accent'][1:])
            chart.category_axis.has_title=True;chart.category_axis.axis_title.text_frame.text=ch['y_label'] if ch['kind']=='bar' else ch['x_label']
            chart.value_axis.has_title=True;chart.value_axis.axis_title.text_frame.text=ch['x_label'] if ch['kind']=='bar' else ch['y_label']
            chart.category_axis.tick_labels.font.size=Pt(12);chart.value_axis.tick_labels.font.size=Pt(12)
            chart.category_axis.tick_labels.font.color.rgb=RGBColor.from_string(C['ink'][1:]);chart.value_axis.tick_labels.font.color.rgb=RGBColor.from_string(C['ink'][1:])
            for axis in [chart.category_axis,chart.value_axis]:
                axis.format.line.color.rgb=RGBColor.from_string(C['accent_faint'][1:])
                if axis.has_major_gridlines:axis.major_gridlines.format.line.color.rgb=RGBColor.from_string(C['accent_faint'][1:])
                for para in axis.axis_title.text_frame.paragraphs:para.font.color.rgb=RGBColor.from_string(C['ink'][1:])
            chart.value_axis.tick_labels.number_format='#,##0.###'
            if ch['kind']=='ecdf':
                import math
                raw=[10**p['x'] if ch.get('scale')=='log10' else p['x'] for p in ch['points']]
                fmt='[>=1000000000]0.##,,,"B";[>=1000000]0.##,,"M";#,##0.###' if max(raw)>=1e9 else '[>=1000000]0.##,,"M";[>=1000]0.##,"K";0.###'
                chart.category_axis.tick_labels.number_format='0.##E+0' if any(0<abs(x)<.001 for x in raw) else fmt
            if ch['kind']=='ecdf':
                chart.value_axis.minimum_scale=0;chart.value_axis.maximum_scale=100
                if ch.get('scale')=='log10':
                    from pptx.oxml.xmlchemy import OxmlElement
                    log=OxmlElement('c:logBase');log.set('val','10');chart.category_axis._element.scaling.insert(0,log)
            else:
                chart.value_axis.minimum_scale=0
                chart.plots[0].has_data_labels=True;labels=chart.plots[0].data_labels;labels.position=XL_DATA_LABEL_POSITION.OUTSIDE_END;labels.font.size=Pt(11);labels.font.color.rgb=RGBColor.from_string(C['ink'][1:]);labels.number_format='#,##0;-#,##0;'
            notes=[]
            if ch['kind']!='ecdf' and shortened!=categories:
                notes.append('Long labels shortened with …; full labels in slide notes and artifact.')
                s.notes_slide.notes_text_frame.text='\n'.join(categories)
            if ch.get('omitted_periods'):notes.append(str(ch['omitted_periods'])+' middle bins omitted; full counts in saved profile.')
            if ch.get('omitted_points'):notes.append('Approximate ECDF display; '+str(ch['omitted_points'])+' distinct points omitted.')
            if 'coverage' in ch:notes.append('Top10 covers '+formatted(ch['coverage'],True)+' of raw values; other is remainder.')
            if ch.get('scale')=='log10':
                counts=ch.get('coverage_counts')
                notes.append((f"Positive: {counts['positive']}; zeros excluded: {counts['zeros']}; negatives excluded: {counts['negatives']}; invalid: {counts['invalid']}. " if counts else 'Legacy coverage unavailable. ')+'Positive-only log10; linear view retained.')
            if notes:
                box=s.shapes.add_textbox(Inches(.7),Inches(6.6),Inches(12),Inches(.65));box.text_frame.text=' '.join(notes)
                for paragraph in box.text_frame.paragraphs:paragraph.font.size=Pt(12)
    for slide_item in deck.slides:
        for shape in slide_item.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    para.font.color.rgb=RGBColor.from_string(C['ink'][1:])
                    for run in para.runs:run.font.color.rgb=RGBColor.from_string(C['ink'][1:])
    output=io.BytesIO();deck.save(output)
    return normalized_zip(output.getvalue()),{'slides':len(deck.slides),'mode':'full' if full else 'summary','included_charts':len(chosen),'omitted_charts':len(available)-len(chosen),'chart_slides':len(views),'included_summary_panels':len(panels),'omitted_summary_panels':len(all_panels)-len(panels),'summary_orientation':report_options({'report':report or {}})['summary_orientation']}


def export_bundle(result,formats,deck='summary',report=None):
    if deck not in {'summary','full'}:raise ValueError('deck must be summary or full')
    serializers={'pdf':pdf_bytes,'pptx':pptx_bytes};files={}
    status={'artifact_sha256':hashlib.sha256(result.to_json().encode()).hexdigest(),'formats':{}}
    for fmt in sorted(set(formats)):
        if fmt not in serializers:raise ValueError('Unsupported export format: '+fmt)
        # Omitted optional sections (spec012) are dropped from the view, never from the artifact.
        view={k:v for k,v in result.document.items() if k not in omitted(result.document)}
        try:
            data,details=pptx_bytes(view,full=deck=='full',report=report) if fmt=='pptx' else serializers[fmt](view,report=report)
            files['report.'+fmt]=data
            status['formats'][fmt]={'status':'written','serializer':{'package':'reportlab' if fmt=='pdf' else 'python-pptx','version':version('reportlab' if fmt=='pdf' else 'python-pptx')},**details}
        except ImportError:
            status['formats'][fmt]={'status':'unavailable','reason':f'Install fathom-guide[{fmt}] to enable this local export.'}
    return files,status
