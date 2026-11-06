"""Actual authenticated local session; browser blocks every non-loopback URL."""
import json
import os
from pathlib import Path
import select
import subprocess
import sys
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[3]
OUT=Path('/tmp/fathom-serve24-review')
DEST=Path(__file__).parent
OUT.mkdir(exist_ok=True)
data=DEST/'synthetic.csv'
env={**os.environ,'PYTHONPATH':str(ROOT/'src'),'FATHOM_DENY_NETWORK':'1','FATHOM_ALLOW_LOOPBACK':'1'}
process=subprocess.Popen(['/workspace/work/env/bin/python','-u',str(ROOT/'tests/offline_runner.py'),'serve',str(data),'--out',str(OUT),'--idle-timeout','120'],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
assert select.select([process.stdout],[],[],20)[0]
url=process.stdout.readline().strip();assert url.startswith('http://127.0.0.1:')
origin='http://'+urlsplit(url).netloc
checks=[]
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  for width in [1280,390]:
   for theme in ['light','dark']:
    context=browser.new_context(viewport={'width':width,'height':960},color_scheme=theme)
    requests=[];errors=[]
    def route(r):
     if r.request.url.startswith(origin+'/'):r.continue_()
     else:requests.append(r.request.url);r.abort()
    context.route('**/*',route)
    page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(url);page.locator('#rerun').wait_for()
    console=[];page.on('console',lambda m:console.append(m.text) if m.type=='error' else None)
    page.locator('input[data-text="question"]').fill('Which synthetic values need review?')
    page.locator('input[data-text="question"]').dispatch_event('input')
    page.locator('#rerun').click();page.get_by_text('Report updated',exact=True).wait_for()
    page.screenshot(path=str(DEST/f'live-{theme}-{width}.png'))
    frame=page.frame_locator('#local-report');frame.locator('h1').wait_for();assert frame.locator('body').inner_text().strip()
    assert not console,console
    page.locator('#live-report').scroll_into_view_if_needed()
    page.wait_for_timeout(250)
    frame.locator('h1').evaluate('(e)=>e.scrollIntoView()')
    page.wait_for_timeout(100)
    page.screenshot(path=str(DEST/f'report-{theme}-{width}.png'))
    overflow=page.evaluate('document.documentElement.scrollWidth>innerWidth')
    assert not requests and not errors and not overflow,(requests,errors,overflow)
    checks.append({'view':'live','width':width,'theme':theme,'external_requests':requests,'errors':errors,'overflow':overflow,'rerun':'Report updated'})
    context.close()
  context=browser.new_context(viewport={'width':390,'height':960},java_script_enabled=False)
  page=context.new_page();page.goto(url);assert 'JavaScript is off' in page.locator('body').inner_text()
  page.screenshot(path=str(DEST/'no-js-390.png'));context.close()
  # Real Stop button and listener termination.
  context=browser.new_context(viewport={'width':1280,'height':960});page=context.new_page();page.goto(url);page.locator('#stop').click();page.get_by_text('Stopped. Saved reports remain available on disk.',exact=True).wait_for();context.close()
  browser.close()
 process.wait(timeout=8)
 assert process.returncode==0,process.stderr.read()
 (DEST/'browser-checks.json').write_text(json.dumps({'checks':checks,'stop':'listener closed; process exit 0','no_js':'static command and fallback visible','tokens':'not saved in review evidence'},indent=2)+'\n')
finally:
 if process.poll() is None:process.terminate();process.wait(timeout=5)
