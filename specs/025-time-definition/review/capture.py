"""Offline native-disclosure/keyboard/card/YAML check, scripts on and off."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
OUT=Path(__file__).parent;checks=[]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 for view in ['configure','liftoff']:
  html=Path('/tmp/fathom-clock25',view,view+'.html').read_text()
  for scripts in [True,False]:
   for width in [1280,390]:
    for theme in ['light','dark']:
     context=browser.new_context(viewport={'width':width,'height':1100},color_scheme=theme,java_script_enabled=scripts)
     context.set_offline(True);page=context.new_page();requests=[];errors=[]
     page.on('request',lambda r:requests.append(r.url));page.on('pageerror',lambda e:errors.append(str(e)))
     page.set_content(html)
     card=page.locator('[data-definition="0"]');summary=card.locator('summary').first
     summary.focus();page.keyboard.press('Enter');assert card.get_attribute('open') is not None
     if scripts:
      for j,role in enumerate(['I','M','S','F','p']):card.locator('[data-time-role="'+str(j)+'"]').select_option(role)
      card.locator('[data-definition-rate]').fill('24')
      assert '3/6' in card.locator('.definition-result').inner_text()
      assert 'frame_at_or_above_rate' in card.inner_text()
      card.locator('[data-use-definition]').click()
      yaml=page.locator('#yaml').inner_text();assert 'frame_rate: 24' in yaml and '%I:%M:%S:%F %p' in yaml
      # Change to fraction: old base/rate must not persist in emitted YAML.
      card.locator('[data-time-role="3"]').select_option('f');card.locator('[data-use-definition]').click()
      assert 'frame_rate:' not in page.locator('#yaml').inner_text()
      card.locator('[data-time-role="3"]').select_option('F');card.locator('[data-definition-rate]').fill('24');card.locator('[data-use-definition]').click()
     else:
      fallback=card.locator('details').last;fallback.locator('summary').click()
      assert 'guide profile DATA.csv' in card.inner_text() and '%F' in card.inner_text()
      assert not card.locator('[data-use-definition]').is_visible()
     card.scroll_into_view_if_needed();page.wait_for_timeout(100)
     mode='scripts' if scripts else 'no-js'
     card.screenshot(path=str(OUT/f'{view}-{mode}-{theme}-{width}.png'))
     overflow=page.evaluate('document.documentElement.scrollWidth>innerWidth') if scripts else None
     assert not requests and not errors and not overflow,(requests,errors,overflow)
     checks.append({'view':view,'scripts':scripts,'width':width,'theme':theme,'requests':requests,'errors':errors,'overflow':overflow,'keyboard_disclosure':True,'frame_fault_and_yaml_checked':scripts})
     context.close()
 browser.close()
(OUT/'browser-checks.json').write_text(json.dumps(checks,sort_keys=True,indent=2)+'\n')
