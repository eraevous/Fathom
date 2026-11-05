"""Review-only offline browser capture. No application dependency or external requests."""
from pathlib import Path
import hashlib,json,os,subprocess
from playwright.sync_api import sync_playwright

root=Path('.');out=root/'specs/014-offline-panel/review'
for name,cfg in [('panel','panel.yaml'),('panel-joined','joined.yaml')]:
    subprocess.run(['/workspace/work/env/bin/python','-m','fathom','panel','tests/fixtures/panel/panel.csv','--config','tests/fixtures/panel/'+cfg,'--aggregate','week,month','--out','reports/'+name],env={**os.environ,'PYTHONPATH':'src'},capture_output=True,check=True)
for cmd in ['configure','liftoff']:
    subprocess.run(['/workspace/work/env/bin/python','-m','fathom',cmd,'tests/fixtures/panel/panel.csv','--out','reports/offline-'+cmd],env={**os.environ,'PYTHONPATH':'src'},capture_output=True,check=True)
manifest={};checks={}
views=[('panel','reports/panel/panel.html',[('top','h1'),('frequency','h2:text-is("Frequency")'),('boundaries','h3:text-is("Observed volume and declared boundaries")')]),
       ('joined','reports/panel-joined/panel.html',[('metrics','h2:text-is("Metric join and disagreement")')]),
       ('week','reports/panel/views/week/panel.html',[('top','h1')]),
       ('month','reports/panel/views/month/panel.html',[('top','h1')]),
       ('target','reports/panel-joined/targets/0/report.html',[('top','h1')])]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    for name,path,topics in views:
        for mode in ['light','dark']:
            for width in [1280,390]:
                page=browser.new_page(viewport={'width':width,'height':900},color_scheme=mode);page.context.set_offline(True)
                requests=[];page.on('request',lambda r:requests.append(r.url));page.set_content(Path(path).read_text())
                assert not requests,requests
                assert page.locator('script').count()==0
                assert page.evaluate('document.documentElement.scrollWidth')<=width
                panel=page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--panel').trim()")
                assert panel==('#162427' if mode=='dark' else '#ffffff')
                for topic,selector in topics:
                    if topic in ['frequency','boundaries']:page.locator('details.series-entry').first.evaluate('(el)=>el.open=true')
                    element=page.locator(selector).first;element.scroll_into_view_if_needed();page.evaluate('(y)=>scrollTo(0,y)',element.bounding_box()['y']+page.evaluate('scrollY'))
                    file=f'{name}-{topic}-{mode}-{width}.png';page.screenshot(path=str(out/file));manifest[file]={'width':width,'mode':mode,'view':name,'topic':topic,'document_width':page.evaluate('document.documentElement.scrollWidth'),'height':page.evaluate('document.documentElement.scrollHeight'),'external_requests':requests,'panel':panel}
                page.close()
    for cmd in ['configure','liftoff']:
        page=browser.new_page();page.context.set_offline(True);requests=[];page.on('request',lambda r:requests.append(r.url));page.set_content(Path(f'reports/offline-{cmd}/{cmd}.html').read_text());assert not requests
        assert page.locator('#yaml').inner_text()=='{}\n';checks[cmd]={'external_requests':requests,'untouched_yaml':'{}'};page.close()
    browser.close()
(out/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n');(out/'checks.json').write_text(json.dumps(checks,indent=2,sort_keys=True)+'\n')
(out/'hashes.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.glob('*.png'))},indent=2)+'\n')
print(len(manifest),'screenshots; no external requests or document overflow')
