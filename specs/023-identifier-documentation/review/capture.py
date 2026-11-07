"""Real offline identifier/role/panel navigation review."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
out=Path(__file__).parent;checks={}
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for view,filename in [('profile','/tmp/id23-profile/report.html'),('configure','/tmp/id23-configure/configure.html'),('panel','/tmp/id23-panel/panel.html')]:
  for theme in ['light','dark']:
   for width in [1280,390]:
    page=browser.new_page(viewport={'width':width,'height':900},color_scheme=theme);page.context.set_offline(True);requests=[];errors=[];page.on('request',lambda r:requests.append(r.url));page.on('pageerror',lambda e:errors.append(str(e)));page.set_content(Path(filename).read_text())
    if view=='configure':
     select=page.locator('[data-col="0"][data-field="role"]');select.select_option('identifier');assert 'role: "identifier"' in page.locator('#yaml').inner_text();select.focus();page.keyboard.press('Tab');select.scroll_into_view_if_needed()
    else:
     card=page.locator('#report-identifiers details').first;card.locator('summary').first.click();card.evaluate('(e)=>window.scrollTo(0,e.getBoundingClientRect().top+scrollY-12)')
     for link in page.locator('#report-identifiers a[href^="#"]').all():assert page.locator(link.get_attribute('href')).count()==1
    assert not requests and not errors,(view,requests,errors)
    overflow=page.evaluate('document.documentElement.scrollWidth>innerWidth');assert not overflow,(view,width)
    page.screenshot(path=str(out/f'{view}-{theme}-{width}.png'));checks[f'{view}-{theme}-{width}']={'requests':requests,'errors':errors,'overflow':overflow,'role_yaml_checked':view=='configure','real_anchor_destinations':view!='configure'};page.close()
 browser.close()
(out/'browser-checks.json').write_text(json.dumps(checks,sort_keys=True,indent=2)+'\n')
