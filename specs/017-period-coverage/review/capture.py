"""Offline screenshots: pinned public taxis; no application dependency."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path(__file__).parent;checks={}
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for stage in ('before','after'):
  for width in ([1280] if stage=='before' else [1280,390]):
   page=browser.new_page(viewport={'width':width,'height':900});page.context.set_offline(True);req=[];page.on('request',lambda r:req.append(r.url))
   page.set_content(Path('reports/demo-'+stage+'/profile/report.html').read_text())
   page.screenshot(path=str(out/f'{stage}-head-{width}.png'))
   page.locator('#temporal-structure').scroll_into_view_if_needed();page.screenshot(path=str(out/f'{stage}-temporal-{width}.png'))
   page.locator('#temporal-structure tr').filter(has_text='Amplitude').first.evaluate('(e)=>e.scrollIntoView({block:"start"})');page.screenshot(path=str(out/f'{stage}-amplitude-{width}.png'))
   if stage=='after':
    page.locator('caption').filter(has_text='Boundary timestamp-span').first.scroll_into_view_if_needed();page.screenshot(path=str(out/f'{stage}-edges-{width}.png'))
    if width==390:
     page.locator('caption').filter(has_text='Boundary timestamp-span').first.evaluate('(e)=>{let d=e.parentElement.parentElement;d.scrollLeft=d.scrollWidth}');page.screenshot(path=str(out/'after-edges-right-390.png'))
   entry=page.locator('details.column-entry').first;entry.evaluate('(e)=>e.open=true');entry.locator('summary').first.evaluate('(e)=>e.scrollIntoView({block:"start"})');page.screenshot(path=str(out/f'{stage}-dictionary-{width}.png'))
   if stage=='after' and width==1280:
    hint=page.locator('details.column-entry').filter(has=page.locator('summary h3',has_text='pickup_zone')).first;hint.evaluate('(e)=>e.open=true');hint.locator('summary').first.evaluate('(e)=>e.scrollIntoView({block:"start"})');page.screenshot(path=str(out/'after-string-hint-1280.png'))
   checks[f'{stage}-{width}']={'requests':req,'overflow':page.evaluate('document.documentElement.scrollWidth>innerWidth')};assert not req and not checks[f'{stage}-{width}']['overflow'];page.close()
 page=browser.new_page(viewport={'width':1280,'height':900});page.context.set_offline(True);req=[];page.on('request',lambda r:req.append(r.url));page.set_content(Path('reports/demo-after/brief/liftoff.html').read_text());detail=page.locator('details').filter(has=page.locator('#lift-series-detail-0')).first;detail.evaluate('(e)=>e.open=true');page.locator('#lift-series-detail-0 caption').filter(has_text='Boundary timestamp-span').first.scroll_into_view_if_needed();page.screenshot(path=str(out/'after-brief-edges-1280.png'));checks['brief']={'requests':req,'overflow':page.evaluate('document.documentElement.scrollWidth>innerWidth')};assert not req and not checks['brief']['overflow'];page.close()
 browser.close()
(out/'checks.json').write_text(json.dumps(checks,sort_keys=True,indent=2)+'\n')
