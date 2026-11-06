"""Actual offline review of synthetic years; Playwright is review-only."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path(__file__).parent;checks={}
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for name,path in [('before-failure','before/report.html'),('after-failure','failure/report.html'),('annual','profile/report.html'),('panel','panel/panel.html')]:
  for width in ([1280] if name=='before-failure' else [1280,390]):
   page=browser.new_page(viewport={'width':width,'height':900});page.context.set_offline(True);req=[];page.on('request',lambda r:req.append(r.url));page.set_content(Path('reports/years',path).read_text());page.screenshot(path=str(out/f'{name}-head-{width}.png'))
   if name=='annual':
    entry=page.locator('details.column-entry').first;entry.evaluate('(e)=>e.open=true');entry.locator('summary').first.evaluate('(e)=>e.scrollIntoView({block:"start"})');page.screenshot(path=str(out/f'annual-column-{width}.png'))
    page.locator('#temporal-structure').scroll_into_view_if_needed();page.screenshot(path=str(out/f'annual-structure-{width}.png'))
   if name=='panel':
    page.locator('details').filter(has_text='north').first.evaluate('(e)=>e.open=true');page.screenshot(path=str(out/f'panel-details-{width}.png'))
   checks[f'{name}-{width}']={'requests':req,'overflow':page.evaluate('document.documentElement.scrollWidth>innerWidth')};assert not req and not checks[f'{name}-{width}']['overflow'];page.close()
 page=browser.new_page(viewport={'width':390,'height':900},color_scheme='dark');page.context.set_offline(True);page.set_content(Path('reports/years/failure/report.html').read_text());page.screenshot(path=str(out/'after-failure-dark-390.png'));page.close();browser.close()
(out/'checks.json').write_text(json.dumps(checks,sort_keys=True,indent=2)+'\n')
