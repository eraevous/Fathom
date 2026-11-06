"""Actual offline browser review; no resource request is allowed."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
out=Path(__file__).parent;checks={}
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for stage in ['before','after']:
  for view in ['profile','brief','panel']:
   for width in [1280,390]:
    page=browser.new_page(viewport={'width':width,'height':900});page.context.set_offline(True);requests=[];page.on('request',lambda r:requests.append(r.url))
    page.set_content(Path('/tmp/style-'+stage,view+'.html').read_text());page.screenshot(path=str(out/f'{stage}-{view}-{width}.png'))
    checks[f'{stage}-{view}-{width}']={'requests':requests,'overflow':page.evaluate('document.documentElement.scrollWidth>innerWidth')}
    assert not requests and not checks[f'{stage}-{view}-{width}']['overflow']
    if stage=='after' and view in ['profile','brief']:
     b=page.locator('.report-nav button');assert b.is_visible()
     if width==390:
      assert b.get_attribute('aria-expanded')=='false';b.focus();page.keyboard.press('Enter');assert b.get_attribute('aria-expanded')=='true'
      page.screenshot(path=str(out/f'after-{view}-nav-open-{width}.png'))
     links=page.locator('.report-nav a');assert all(page.locator(links.nth(i).get_attribute('href')).count()==1 for i in range(links.count()))
     page.emulate_media(media='print');assert not page.locator('.report-nav').is_visible();page.emulate_media(media='screen')
    if stage=='after' and view=='profile':
     f=page.locator('article.finding:not(.repetitive)').first;f.scroll_into_view_if_needed();page.screenshot(path=str(out/f'after-finding-{width}.png'))
     assert not f.locator('details').first.get_attribute('open')
    page.close()
 for view in ['profile','brief']:
  for width in [1280,390]:
   page=browser.new_page(viewport={'width':width,'height':900},java_script_enabled=False);page.context.set_offline(True);page.set_content(Path('/tmp/style-after',view+'.html').read_text());page.screenshot(path=str(out/f'after-{view}-nojs-{width}.png'))
   assert not page.locator('.report-nav button').is_visible()
   assert all(page.locator('.report-nav a').nth(i).is_visible() for i in range(page.locator('.report-nav a').count()))
   checks[f'{view}-nojs-{width}']={'all_nav_links_visible':True,'overflow':page.evaluate('document.documentElement.scrollWidth>innerWidth')};assert not checks[f'{view}-nojs-{width}']['overflow'];page.close()
 browser.close()
(out/'checks.json').write_text(json.dumps(checks,sort_keys=True,indent=2)+'\n')
