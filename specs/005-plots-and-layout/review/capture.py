"""Review-only tools: actual HTML, PDF and office-rendered PPTX screenshots.

Run from repo root: python specs/005-plots-and-layout/review/capture.py before
and after. Expects reports/layout-{stage}/report.{html,pdf,pptx} plus
slides/report.pdf produced by LibreOffice Impress from that PPTX. Does not alter
application output; commits only bounded representative screenshots/manifest.
"""

import argparse
import json
from pathlib import Path

import fitz
from PIL import Image
from playwright.sync_api import sync_playwright


def capture(stage):
    root=Path('reports/layout-'+stage);out=Path(__file__).parent;manifest={}
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
        for width in (1280,390):
            page=browser.new_page(viewport={'width':width,'height':900},device_scale_factor=1)
            page.set_content((root/'report.html').read_text(),wait_until='load')
            if stage=='before':
                entry=page.locator('tr').filter(has=page.locator('td:first-child')).filter(has_text='positive_amount').first
                # Expand the old narrow evidence cell to show its layout problem.
                entry.locator('details').first.evaluate('(d)=>d.open=true')
            else:entry=page.locator('.column-entry').filter(has=page.locator('h3',has_text='positive_amount')).first
            entry.scroll_into_view_if_needed();page.evaluate('(y)=>scrollTo(0,y)',entry.bounding_box()['y']+page.evaluate('scrollY'))
            name=f'{stage}-html-{width}.png';page.screenshot(path=str(out/name));manifest[name]={'kind':'actual Chromium viewport','width':width,'height':900,'document_width':page.evaluate('document.documentElement.scrollWidth'),'topic':'positive_amount column entry'}
            if stage=='after':
                for topic,locator in [('category',page.locator('.column-entry').filter(has=page.locator('h3',has_text='segment')).locator('.chart').first),('missingness',page.locator('.chart').nth(1)),('ecdf',entry.locator('.chart').filter(has=page.locator('svg[aria-label^="Empirical"]'))),('calendar',page.locator('.column-entry').filter(has=page.locator('h3',has_text='release_date')).locator('.chart').first)]:
                    locator.scroll_into_view_if_needed();page.evaluate('(y)=>scrollTo(0,y)',locator.bounding_box()['y']+page.evaluate('scrollY'))
                    name=f'{stage}-{topic}-{width}.png';page.screenshot(path=str(out/name));manifest[name]={'kind':'actual Chromium viewport','width':width,'height':900,'topic':topic}
            page.close()
        browser.close()
    for kind,path in [('pdf',root/'report.pdf'),('pptx',root/'slides/report.pdf')]:
        doc=fitz.open(path)
        index=next((i for i,p in enumerate(doc) if 'Distribution of positive_amount' in p.get_text()),0)
        # Review every page at a reduced contact-sheet size; representative page
        # remains full-width in each requested screenshot.
        thumbs=[]
        for i,page in enumerate(doc):
            pix=page.get_pixmap(matrix=fitz.Matrix(220/page.rect.width,220/page.rect.width),alpha=False)
            thumbs.append(Image.frombytes('RGB',[pix.width,pix.height],pix.samples))
        cellw=240;cellh=max(im.height for im in thumbs)+30;sheet=Image.new('RGB',(cellw*5,cellh*((len(thumbs)+4)//5)), '#e5e7eb')
        from PIL import ImageDraw
        draw=ImageDraw.Draw(sheet)
        for i,im in enumerate(thumbs):
            x=(i%5)*cellw;y=(i//5)*cellh;sheet.paste(im,(x+10,y+20));draw.text((x+10,y+3),f'{kind} {i+1}',fill='black')
        sheet.save(out/f'{stage}-{kind}-contact.png',optimize=True)
        for width in (1280,390):
            page=doc[index];pix=page.get_pixmap(matrix=fitz.Matrix(width/page.rect.width,width/page.rect.width),alpha=False)
            name=f'{stage}-{kind}-{width}.png';pix.save(out/name)
            manifest[name]={'kind':'actual export raster' if kind=='pdf' else 'LibreOffice-rendered actual PPTX raster','width':pix.width,'height':pix.height,'page':index+1,'total_pages':len(doc)}
        if stage=='after':
            topics=[('long-label','Most common values of notes'),('ecdf','Empirical cumulative distribution of positive_amount')] if kind=='pptx' else [('box','Five-number view of positive_amount')]
            for topic,term in topics:
                index=next(i for i,page in enumerate(doc) if term in page.get_text());page=doc[index]
                name=f'{stage}-{kind}-{topic}-1280.png';page.get_pixmap(matrix=fitz.Matrix(1280/page.rect.width,1280/page.rect.width),alpha=False).save(out/name)
                manifest[name]={'kind':'actual PDF raster' if kind=='pdf' else 'LibreOffice-rendered actual PPTX raster','width':1280,'page':index+1,'topic':topic}
    (out/f'{stage}-manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['before','after']);capture(parser.parse_args().stage)
