"""Affected-view screenshots: actual offline HTML, PDF and Impress output at1280/390."""
import hashlib
import json
from pathlib import Path

import fitz
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright


def main():
    out=Path(__file__).parent;manifest={}
    for old in out.glob('*.png'):old.unlink()
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
        for name in ('boxes','tiny','rates','scatter','high-cardinality'):
            root=Path(f'reports/fix8-{name}')
            for width in (1280,390):
                page=browser.new_page(viewport={'width':width,'height':900},device_scale_factor=1);page.context.set_offline(True);page.set_content((root/'report.html').read_text())
                chart=page.locator('figure.target-chart').first
                def snap(topic):
                    chart.scroll_into_view_if_needed();page.evaluate('(y)=>scrollTo(0,y)',chart.bounding_box()['y']+page.evaluate('scrollY'))
                    file=f'{name}-html-{topic}-{width}.png';page.screenshot(path=str(out/file));manifest[file]={'format':'HTML','width':width,'document_width':page.evaluate('document.documentElement.scrollWidth'),'topic':topic}
                snap('plot')
                if name in ('boxes','tiny','rates','scatter'):
                    chart.locator('details').first.evaluate('(x)=>x.open=true')
                    disclosure=chart.locator('details').first;disclosure.scroll_into_view_if_needed();page.evaluate('(y)=>scrollTo(0,y)',disclosure.bounding_box()['y']+page.evaluate('scrollY'))
                    file=f'{name}-html-values-{width}.png';page.screenshot(path=str(out/file));manifest[file]={'format':'HTML','width':width,'topic':'Chart values disclosure'}
                page.close()
        browser.close()
    for name in ('boxes','tiny','rates','scatter','high-cardinality'):
        root=Path(f'reports/fix8-{name}')
        for kind,path in [('pdf',root/'report.pdf'),('pptx',root/'slides/report.pdf')]:
            doc=fitz.open(path);pages=[i for i,p in enumerate(doc) if 'Target:' in p.get_text()]
            if kind=='pdf' or name!='high-cardinality':pages=pages[:1]
            for j,index in enumerate(pages):
                for width in (1280,390):
                    page=doc[index];pix=page.get_pixmap(matrix=fitz.Matrix(width/page.rect.width,width/page.rect.width),alpha=False)
                    file=f'{name}-{kind}-panel-{j+1}-{width}.png';pix.save(out/file);manifest[file]={'format':kind,'width':pix.width,'page':index+1,'pages':len(doc),'renderer':'ReportLab/PyMuPDF' if kind=='pdf' else 'LibreOffice Impress/PyMuPDF'}
            if kind=='pptx' and name=='high-cardinality':
                thumbs=[]
                for page in doc:
                    pix=page.get_pixmap(matrix=fitz.Matrix(180/page.rect.width,180/page.rect.width),alpha=False);thumbs.append(Image.frombytes('RGB',[pix.width,pix.height],pix.samples))
                sheet=Image.new('RGB',(1000,125*((len(thumbs)+4)//5)),'#e5e7eb');draw=ImageDraw.Draw(sheet)
                for i,im in enumerate(thumbs):x=i%5*200;y=i//5*125;sheet.paste(im,(x+10,y+20));draw.text((x+10,y+3),f'Slide{i+1}',fill='black')
                sheet.save(out/'high-cardinality-pptx-contact.png')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    (out/'image-hashes.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('*.png'))},indent=2)+'\n')
    print('Screenshots',len(list(out.glob('*.png'))))

if __name__=='__main__':main()
