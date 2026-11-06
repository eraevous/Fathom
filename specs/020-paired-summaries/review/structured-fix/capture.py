"""Actual Chromium, offline, fixed1280 viewport, two public-film findings."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
out=Path(__file__).parent;checks={}
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for stage in ['before','after']:
  for theme in ['light','dark']:
   page=browser.new_page(viewport={'width':1280,'height':900},color_scheme=theme);page.context.set_offline(True)
   requests=[];page.on('request',lambda r:requests.append(r.url));page.set_content(Path('/tmp/fix34-'+stage+'/report.html').read_text())
   roots=page.locator('#key-findings > ul > li')
   for topic,element in [('relationships',roots.first),('adventure',roots.filter(has_text='Adventure').first)]:
    element.scroll_into_view_if_needed();page.screenshot(path=str(out/f'{stage}-{topic}-{theme}-1280.png'))
   assert not requests and not page.evaluate('document.documentElement.scrollWidth>innerWidth')
   checks[stage+'-'+theme]={'requests':requests,'viewport':[1280,900],'document_overflow':False}
   page.close()
 browser.close()
(out/'browser-checks.json').write_text(json.dumps(checks,sort_keys=True,indent=2)+'\n')
