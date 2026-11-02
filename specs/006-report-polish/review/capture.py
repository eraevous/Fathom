"""Actual browser/export screenshots and honest default/expanded heights.

Run from repo root with review-only Playwright, Chromium, PyMuPDF and Pillow.
Expects before/after profile+exports in reports/polish-{stage}-{movies,college};
Impress-converted slides/report.pdf alongside each PPTX. Does not fetch data.
"""

import json
from pathlib import Path

import fitz
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright


def capture():
    out=Path(__file__).parent;manifest={};heights={}
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
        for stage in ('before','after'):
            for dataset in ('movies','college'):
                root=Path(f'reports/polish-{stage}-{dataset}')
                for width in (1280,390):
                    page=browser.new_page(viewport={'width':width,'height':900},device_scale_factor=1);page.context.set_offline(True)
                    page.set_content((root/'report.html').read_text())
                    default=page.evaluate('document.documentElement.scrollHeight')
                    if stage=='after':page.locator('details.column-entry').evaluate_all('(xs)=>xs.forEach(x=>x.open=true)')
                    expanded=page.evaluate('document.documentElement.scrollHeight')
                    heights[f'{stage}-{dataset}-{width}']={'default':default,'all_columns_open':expanded,'document_width':page.evaluate('document.documentElement.scrollWidth')}
                    if stage=='after':page.locator('details.column-entry').evaluate_all('(xs)=>xs.forEach(x=>x.open=false)')
                    # Default compact headers, then an expanded representative column.
                    entry=page.locator('.column-entry').first
                    entry.scroll_into_view_if_needed();page.evaluate('(y)=>scrollTo(0,y)',entry.bounding_box()['y']+page.evaluate('scrollY'))
                    name=f'{stage}-{dataset}-headers-{width}.png';page.screenshot(path=str(out/name));manifest[name]={'format':'HTML','width':width,'topic':'default column headers'}
                    target='Worldwide Gross' if dataset=='movies' else 'Median'
                    entry=page.locator('.column-entry').filter(has=page.locator('h3',has_text=target)).first
                    if stage=='after':entry.evaluate('(x)=>x.open=true')
                    entry.scroll_into_view_if_needed();page.evaluate('(y)=>scrollTo(0,y)',entry.bounding_box()['y']+page.evaluate('scrollY'))
                    name=f'{stage}-{dataset}-column-{width}.png';page.screenshot(path=str(out/name));manifest[name]={'format':'HTML','width':width,'topic':target}
                    if dataset=='movies':
                        for topic,selector in [('box','svg[aria-label^="Five-number"]'),('log','svg[aria-label*="log10"]')]:
                            charts=entry.locator('.chart').filter(has=page.locator(selector))
                            if charts.count():
                                chart=charts.first;chart.scroll_into_view_if_needed();page.evaluate('(y)=>scrollTo(0,y)',chart.bounding_box()['y']+page.evaluate('scrollY'))
                                name=f'{stage}-movies-{topic}-{width}.png';page.screenshot(path=str(out/name));manifest[name]={'format':'HTML','width':width,'topic':topic}
                    page.close()
        browser.close()
    for stage,dataset in [('before','movies'),('after','movies'),('after','college')]:
        root=Path(f'reports/polish-{stage}-{dataset}')
        for kind,path in [('pdf',root/'report.pdf'),('pptx',root/'slides/report.pdf')]:
            doc=fitz.open(path);term='Worldwide Gross' if dataset=='movies' else 'Median'
            preferred=('Positive log10 distribution of Worldwide Gross' if stage=='after' else 'Distribution of Worldwide Gross') if dataset=='movies' else 'Distribution of Median'
            index=next((i for i,page in enumerate(doc) if preferred in page.get_text()),next((i for i,page in enumerate(doc) if 'distribution of' in page.get_text().lower()),0))
            # Representative full page/slide, actual office output for PPTX.
            for width in (1280,390):
                page=doc[index];pix=page.get_pixmap(matrix=fitz.Matrix(width/page.rect.width,width/page.rect.width),alpha=False)
                name=f'{stage}-{dataset}-{kind}-{width}.png';pix.save(out/name);manifest[name]={'format':kind,'width':pix.width,'page':index+1,'pages':len(doc),'renderer':'ReportLab/PyMuPDF' if kind=='pdf' else 'LibreOffice Impress/PyMuPDF'}
            if stage=='after':
                thumbs=[]
                for page in doc:
                    pix=page.get_pixmap(matrix=fitz.Matrix(180/page.rect.width,180/page.rect.width),alpha=False);thumbs.append(Image.frombytes('RGB',[pix.width,pix.height],pix.samples))
                cellh=max(im.height for im in thumbs)+22;sheet=Image.new('RGB',(1000,cellh*((len(thumbs)+4)//5)),'#e5e7eb');draw=ImageDraw.Draw(sheet)
                for i,im in enumerate(thumbs):
                    x=(i%5)*200;y=(i//5)*cellh;sheet.paste(im,(x+10,y+20));draw.text((x+10,y+3),f'{kind} {i+1}',fill='black')
                sheet.save(out/f'{stage}-{dataset}-{kind}-contact.png',optimize=True)
    # Full-deck close-quartile regression, rendered by actual Impress.
    for kind,path in [('pdf',Path('reports/polish-after-movies/report.pdf')),('pptx-full',Path('reports/polish-full-movies/slides/report.pdf'))]:
        doc=fitz.open(path)
        index=next(i for i,page in enumerate(doc) if 'Five-number view of Worldwide Gross' in page.get_text())
        for width in (1280,390):
            page=doc[index];pix=page.get_pixmap(matrix=fitz.Matrix(width/page.rect.width,width/page.rect.width),alpha=False)
            name=f'after-movies-{kind}-box-{width}.png';pix.save(out/name);manifest[name]={'format':kind,'width':pix.width,'page':index+1,'pages':len(doc),'topic':'close quartile labels'}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    (out/'heights.json').write_text(json.dumps(heights,indent=2,sort_keys=True)+'\n')
    print(json.dumps(heights,indent=2))


if __name__=='__main__':capture()
