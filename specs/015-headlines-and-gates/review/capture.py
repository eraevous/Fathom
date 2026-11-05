"""Review-only actual offline screenshots of pinned public taxis."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path(__file__).parent;checks={}
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for stage in ('before','after'):
  for name,path in [('profile','profile/report.html'),('brief','brief/liftoff.html')]:
   for width in ([1280] if stage=='before' else [1280,390]):
    page=browser.new_page(viewport={'width':width,'height':900});page.context.set_offline(True);requests=[];page.on('request',lambda req:requests.append(req.url))
    page.set_content(Path('reports/demo-'+stage,path).read_text());page.screenshot(path=str(out/f'{stage}-{name}-{width}.png'))
    checks[f'{stage}-{name}-{width}']={'requests':requests,'overflow':page.evaluate('document.documentElement.scrollWidth>innerWidth')}
    assert not requests and not checks[f'{stage}-{name}-{width}']['overflow']
    if stage=='after':assert page.locator('#key-findings li').count()<=5
    page.close()
 browser.close()
(out/'checks.json').write_text(json.dumps(checks,sort_keys=True,indent=2)+'\n')
