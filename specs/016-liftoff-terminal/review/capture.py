"""Actual no-JavaScript fallback review; pinned public baseline is supplied locally."""
import json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path(__file__).parent;checks={}
paths={'before':Path(sys.argv[1]),'after':Path('reports/demo-terminal/liftoff.html')}
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for stage,path in paths.items():
  page=browser.new_page(viewport={'width':1280,'height':900},java_script_enabled=False);page.context.set_offline(True);req=[];page.on('request',lambda r:req.append(r.url));page.set_content(path.read_text())
  page.locator('noscript').scroll_into_view_if_needed();page.screenshot(path=str(out/f'{stage}-nojs-1280.png'))
  checks[stage]={'requests':req,'fallback':page.locator('noscript').inner_text()};assert not req
  page.close()
 for stage,path in [('before',Path(sys.argv[2])),('after',Path('reports/demo-terminal/report.html'))]:
  page=browser.new_page(viewport={'width':1280,'height':900});page.context.set_offline(True);page.set_content(path.read_text());page.screenshot(path=str(out/f'{stage}-head-1280.png'));page.close()
 browser.close()
(out/'checks.json').write_text(json.dumps(checks,sort_keys=True,indent=2)+'\n')
