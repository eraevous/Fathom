"""Actual offline browser/export review; run after documented profiles/conversions."""
import hashlib
import json
from pathlib import Path

import fitz
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright


def capture():
    out=Path(__file__).parent;manifest={};dom={}
    for old in out.glob('*.png'):old.unlink()
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
        for stage,name in [('before','movies'),('after','movies'),('after','college'),('after','planted'),('after','late')]:
            root=Path(f'reports/s7-{stage}-{name}')
            for width in (1280,390):
                page=browser.new_page(viewport={'width':width,'height':900},device_scale_factor=1);page.context.set_offline(True);page.set_content((root/'report.html').read_text())
                dom[f'{stage}-{name}-{width}']={'width':page.evaluate('document.documentElement.scrollWidth'),'height':page.evaluate('document.documentElement.scrollHeight')}
                def snap(topic,locator):
                    if not locator.count():return
                    element=locator.first;element.scroll_into_view_if_needed();page.evaluate('(y)=>scrollTo(0,y)',element.bounding_box()['y']+page.evaluate('scrollY'))
                    file=f'{stage}-{name}-{topic}-{width}.png';page.screenshot(path=str(out/file));manifest[file]={'format':'HTML','width':width,'topic':topic}
                snap('ranking',page.get_by_role('heading',name='Relations',exact=True))
                if stage=='after':
                    snap('scatter',page.locator('figure.target-chart').filter(has=page.locator('svg[data-kind="scatter"]')).first)
                    snap('rates',page.locator('figure.target-chart').filter(has=page.locator('svg[data-kind="rates"]')).first)
                    if name in ('movies','college','planted'):
                        snap('group',page.locator('figure.target-chart').filter(has=page.locator('svg[data-kind="group_box"]')).first)
                    if name=='movies':
                        entry=page.locator('details.column-entry').filter(has=page.locator('h3',has_text='Worldwide Gross')).first;entry.evaluate('(x)=>x.open=true')
                        for topic,term in [('log','Positive log distribution'),('log-ecdf','Positive log ECDF'),('box','Five-number view')]:
                            snap(topic,entry.locator('figure.chart').filter(has=page.locator(f'svg[aria-label^="{term}"]')))
                        if width==1280:
                            chart=entry.locator('figure.chart').last;chart.scroll_into_view_if_needed();page.evaluate('(y)=>scrollTo(0,y)',chart.bounding_box()['y']+page.evaluate('scrollY')-100)
                            stats=entry.locator('.column-statistics').bounding_box();assert stats['y']>=0;dom['sticky-check']={'statistics_y':stats['y'],'height':stats['height']}
                            file='after-movies-sticky-1280.png';page.screenshot(path=str(out/file));manifest[file]={'format':'HTML','width':1280,'topic':'statistics stay visible beside last plot'}
                page.close()
        browser.close()
    for name in ('movies','college','planted','late'):
        root=Path(f'reports/s7-after-{name}')
        for kind,path in [('pdf',root/'report.pdf'),('pptx',root/'slides/report.pdf')]:
            if not path.exists():continue
            doc=fitz.open(path)
            topics={'target':next((i for i,p in enumerate(doc) if 'Target:' in p.get_text()),0)}
            if name=='movies' and kind=='pdf':
                topics['log-ecdf']=next(i for i,p in enumerate(doc) if 'Positive log ECDF of Worldwide Gross' in p.get_text())
                topics['box']=next(i for i,p in enumerate(doc) if 'Five-number view of Worldwide Gross' in p.get_text())
            for topic,index in topics.items():
                for width in (1280,390):
                    page=doc[index];pix=page.get_pixmap(matrix=fitz.Matrix(width/page.rect.width,width/page.rect.width),alpha=False)
                    file=f'after-{name}-{kind}-{topic}-{width}.png';pix.save(out/file);manifest[file]={'format':kind,'width':pix.width,'page':index+1,'pages':len(doc),'renderer':'actual ReportLab PDF' if kind=='pdf' else 'actual LibreOffice Impress/PyMuPDF'}
            thumbs=[]
            for page in doc:
                pix=page.get_pixmap(matrix=fitz.Matrix(150/page.rect.width,150/page.rect.width),alpha=False);thumbs.append(Image.frombytes('RGB',[pix.width,pix.height],pix.samples))
            cellh=max(im.height for im in thumbs)+20;sheet=Image.new('RGB',(900,cellh*((len(thumbs)+4)//5)),'#e5e7eb');draw=ImageDraw.Draw(sheet)
            for i,im in enumerate(thumbs):x=(i%5)*180;y=(i//5)*cellh;sheet.paste(im,(x+10,y+20));draw.text((x+10,y+3),f'{kind} {i+1}',fill='black')
            sheet.save(out/f'after-{name}-{kind}-contact.png',optimize=True)
    # Native Office log ECDF and slim box from optional full deck.
    path=Path('reports/s7-full-movies/slides/report.pdf')
    if path.exists():
        doc=fitz.open(path)
        for topic,title in [('log-ecdf','Positive log ECDF of Worldwide Gross'),('box','Five-number view of Worldwide Gross')]:
            index=next(i for i,p in enumerate(doc) if title in p.get_text())
            for width in (1280,390):
                page=doc[index];pix=page.get_pixmap(matrix=fitz.Matrix(width/page.rect.width,width/page.rect.width),alpha=False);file=f'after-movies-pptx-{topic}-{width}.png';pix.save(out/file);manifest[file]={'format':'PPTX full','width':width,'page':index+1,'pages':len(doc),'renderer':'LibreOffice Impress/PyMuPDF'}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n');(out/'dom.json').write_text(json.dumps(dom,indent=2,sort_keys=True)+'\n')
    (out/'image-hashes.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('*.png'))},indent=2)+'\n');print(json.dumps(dom))

if __name__=='__main__':capture()
