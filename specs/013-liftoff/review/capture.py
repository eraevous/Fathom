"""Offline actual browser review and YAML download roundtrip; no app dependency."""
import hashlib,json,os,subprocess
from pathlib import Path
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

out=Path(__file__).parent
root=Path('reports/liftoff-taxis')
manifest={};checks={}
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1280,'height':900},accept_downloads=True);page.context.set_offline(True)
 page.set_content((root/'liftoff.html').read_text())
 assert page.locator('#yaml').inner_text()=='{}\n'
 assert page.locator('#brief script').count()==0
 assert page.locator('[data-interval]:checked,[data-series]:checked').count()==0
 # A selector cannot apply a series declaration without its checkbox.
 page.locator('[data-series-grain="0"]').select_option('hour');assert page.locator('#yaml').inner_text()=='{}\n'
 page.locator('[data-series-grain="0"]').select_option('auto')
 schema=json.loads(page.locator('#fathom-schema').text_content())
 pick=next(i for i,v in enumerate(schema['interval_options']) if v['start']=='pickup' and v['end']=='dropoff')
 si=next(i for i,v in enumerate(schema['time_series_options']) if v['column']=='pickup')
 page.locator(f'[data-interval="{pick}"]').check();page.locator(f'[data-series="{si}"]').check()
 page.locator('#target').select_option(str(schema['target_options'].index('tip')))
 yaml_text=page.locator('#yaml').inner_text()
 with page.expect_download() as download:page.locator('#download').click()
 download.value.save_as(str(root/'liftoff.yaml'))
 assert (root/'liftoff.yaml').read_text()==yaml_text
 m=json.loads(unquote(page.locator('#manifest').get_attribute('href').split(',',1)[1]))
 assert m['yaml_sha256']==hashlib.sha256(yaml_text.encode()).hexdigest()
 assert any(c.get('series',{}).get('time')=='pickup' and c['state']=='suggested' for c in m['controls'])
 (root/'config-manifest.json').write_text(json.dumps(m,indent=2,sort_keys=True)+'\n')
 page.close()
 subprocess.run(['/workspace/work/env/bin/python','-m','fathom','profile','tests/fixtures/liftoff/taxis.csv','--config',str(root/'liftoff.yaml'),'--out',str(root/'declared')],env={**os.environ,'PYTHONPATH':'src'},check=True,capture_output=True)
 d=json.loads((root/'declared/guide-profile.json').read_text());b=json.loads((root/'liftoff-profile.json').read_text())['liftoff']
 interval=next(x for x in b['previews']['intervals'] if x['declaration']=={'start':'pickup','end':'dropoff'})
 ts=next(x for x in b['previews']['time_series'] if x['declaration']['time']=='pickup')
 assert interval['result']==d['row_structure']['intervals'][0]
 assert ts['result']==d['time_series']['series'][0]
 group=next(g for g in d['target_analysis']['groups'] if g['group_column']=='payment')
 cash=next(g for g in group['groups'] if g['value']=='cash')
 assert cash['valid']==1812 and cash['statistics']['min']==cash['statistics']['max']==0
 checks['download_roundtrip']={'interval_equal_pairs':6,'cash_group_valid':1812,'cash_min_max':[0,0],'series_exactly_equal':True,'target':'tip','yaml_sha256':m['yaml_sha256']}
 # Standalone configure remains a separate command, without the liftoff-only controls.
 subprocess.run(['/workspace/work/env/bin/python','-m','fathom','configure','tests/fixtures/liftoff/taxis.csv','--out',str(root/'configure')],env={**os.environ,'PYTHONPATH':'src'},check=True,capture_output=True)
 views=[('liftoff',root/'liftoff.html',[('brief','#brief'),('conditional','text=Conditional measurements — not declarations'),('form','#configurations'),('series','text=Declared time series')]),
        ('configure',root/'configure/configure.html',[('form','h1')]),
        ('declared',root/'declared/report.html',[('row','#rows-dup-time-0'),('temporal','#temporal-structure'),('temporal-chart','#temporal-structure figure.chart')])]
 for name,path,topics in views:
  for mode in ['light','dark']:
   for width in [1280,390]:
    page=browser.new_page(viewport={'width':width,'height':900},color_scheme=mode);page.context.set_offline(True);page.set_content(path.read_text())
    if name=='configure':assert page.locator('[data-series]').count()==0
    if name in ['liftoff','configure']:assert page.locator('#yaml').inner_text()=='{}\n'
    panel=page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--panel').trim()")
    assert panel==('#162427' if mode=='dark' else '#ffffff')
    for topic,selector in topics:
     
     if name=='declared':page.locator('#full-view').check()
     loc=page.locator(selector).first;loc.scroll_into_view_if_needed();page.evaluate('(y)=>scrollTo(0,y)',loc.bounding_box()['y']+page.evaluate('scrollY'))
     file=f'{name}-{topic}-{mode}-{width}.png';page.screenshot(path=str(out/file));manifest[file]={'page':name,'topic':topic,'mode':mode,'width':width,'document_width':page.evaluate('document.documentElement.scrollWidth'),'height':page.evaluate('document.documentElement.scrollHeight'),'panel':panel,'full_findings':name=='declared'}
    ids=page.locator('[id]').evaluate_all('(els)=>els.map(e=>e.id)');assert len(ids)==len(set(ids)),name
    if name=='declared':
     assert page.locator('script').count()==0
     fills=page.locator('svg[data-kind=stem] line[stroke]').evaluate_all('(es)=>es.map(e=>getComputedStyle(e).stroke)')
     assert ('rgb(92, 184, 189)' if mode=='dark' else 'rgb(33, 110, 115)') in fills
    page.close()
 browser.close()
(out/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
(out/'checks.json').write_text(json.dumps(checks,indent=2,sort_keys=True)+'\n')
(out/'image-hashes.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('*.png'))},indent=2)+'\n')
print('Browser download/stage boundary/theme checks passed;',len(manifest),'screenshots')
