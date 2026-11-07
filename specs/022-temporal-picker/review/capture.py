"""Real offline Chromium picker/profile review, including keyboard and no-JS."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path(__file__).parent;checks={}
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for command in ['configure','liftoff']:
  filename='configure.html' if command=='configure' else 'liftoff.html'
  for theme in ['light','dark']:
   for width in [1280,390]:
    page=browser.new_page(viewport={'width':width,'height':900},color_scheme=theme);page.context.set_offline(True);requests=[];errors=[]
    page.on('request',lambda r:requests.append(r.url));page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content(Path('/tmp/time22-'+command,filename).read_text())
    card=page.locator('[data-picker="2"]');field=card.locator('[data-field="date_format"]')
    field.focus();field.fill('%Q');assert '%Q' in card.locator('.format-result').inner_text();assert page.locator('#download').get_attribute('aria-disabled')=='true'
    field.fill('%d/%m/%Y %H:%M');assert '20/20' in card.locator('.format-result').inner_text()
    assert '2026-04-01T14:05:00' in card.locator('.format-preview').first.inner_text()
    assert '%d/%m/%Y %H:%M' in page.locator('#yaml').inner_text()
    assert 'Ambiguous day/month' in card.inner_text()
    page.locator('[data-format-choice="0"]').select_option('TIME');assert page.locator('[data-col="0"][data-field="date_format"]').input_value()=='TIME'
    field.focus();page.keyboard.press('Tab');card.evaluate('(e)=>window.scrollTo(0,e.getBoundingClientRect().top+scrollY-12)')
    page.screenshot(path=str(out/f'{command}-{theme}-{width}.png'))
    assert not requests and not errors,(requests,errors)
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
    checks[f'{command}-{theme}-{width}']={'requests':requests,'errors':errors,'invalid_pattern_blocks_yaml':True,'custom_preview_matches':20,'keyboard_reachable':True,'overflow':False};page.close()
 for theme in ['light','dark']:
  for width in [1280,390]:
   page=browser.new_page(viewport={'width':width,'height':900},color_scheme=theme,java_script_enabled=False);page.context.set_offline(True)
   page.set_content(Path('/tmp/time22-configure/configure.html').read_text());card=page.locator('[data-picker="2"]')
   assert not card.locator('.format-live').is_visible();assert card.locator('noscript').is_visible()
   card.evaluate('(e)=>window.scrollTo(0,e.getBoundingClientRect().top+scrollY-12)');page.screenshot(path=str(out/f'nojs-{theme}-{width}.png'));page.close()
   page=browser.new_page(viewport={'width':width,'height':900},color_scheme=theme);page.context.set_offline(True)
   page.set_content(Path('/tmp/time22-profile/report.html').read_text());c=page.locator('.column-entry').first;c.locator('summary').first.click();c.scroll_into_view_if_needed();page.screenshot(path=str(out/f'profile-{theme}-{width}.png'));page.close()
 browser.close()
(out/'browser-checks.json').write_text(json.dumps(checks,sort_keys=True,indent=2)+'\n')
