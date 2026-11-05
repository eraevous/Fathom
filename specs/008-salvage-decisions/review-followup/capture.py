"""Offline, actual CSS cascade audit, before/after PR16 review fixes; no report script."""
import hashlib,json,subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
from fathom.connectors import CSVConnector
from fathom.profiler import profile
from fathom.renderers import render_html
from fathom.palette import theme_css,THEMES,DARK_CATEGORICAL,CATEGORICAL

out=Path(__file__).parent
source=Path('tests/fixtures/target-review/high-cardinality.csv')
html=render_html(profile(CSVConnector(source).load(),{'target':'target','columns':{'g':{'type':'categorical'},'target':{'type':'categorical'}}}))
old={};exec(subprocess.check_output(['git','show','a52ce37:src/fathom/palette.py'],text=True),old)
before=html.replace(theme_css(),old['theme_css']())
modes=[('light','light',None,'screen'),('dark','dark',None,'screen'),('override-light','dark','light','screen'),('override-dark','light','dark','screen'),('print-system-dark','dark',None,'print'),('print-forced-dark','light','dark','print')]
manifest={}
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for version,content in [('before',before),('after',html)]:
  for name,scheme,theme,media in modes:
   for width in (1280,390):
    page=browser.new_page(viewport={'width':width,'height':900},color_scheme=scheme);page.context.set_offline(True);page.set_content(content)
    if theme:page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
    page.emulate_media(media=media)
    chart=page.locator('figure.target-chart').first
    probe=page.evaluate('''(colours)=>({panel:getComputedStyle(document.documentElement).getPropertyValue('--panel').trim(), colours:colours.map(c=>{let e=document.querySelector('svg [fill="'+c+'"]');return e?getComputedStyle(e).fill:null})})''',CATEGORICAL)
    expected='dark' if media!='print' and (theme=='dark' or theme is None and scheme=='dark') else 'light'
    if version=='after':
     assert probe['panel']==THEMES[expected]['panel'],(name,probe)
     expected_series=DARK_CATEGORICAL if expected=='dark' else CATEGORICAL
     for seen,hexcolour in zip(probe['colours'],expected_series):
      rgb='rgb('+', '.join(str(int(hexcolour[i:i+2],16)) for i in (1,3,5))+')'
      assert seen==rgb,(name,seen,rgb)
    filename=f'{version}-{name}-{width}.png'
    # Keep before captures to the two failing cases; after covers all six modes.
    if version=='after' or name in ('dark','print-forced-dark'):
     chart.screenshot(path=str(out/filename));manifest[filename]={'width':width,'media':media,'scheme':scheme,'override':theme,**probe}
    page.close()
 browser.close()
(out/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
(out/'image-hashes.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('*.png'))},indent=2)+'\n')
print('Cascade assertions passed in all six modes at both widths; screenshots',len(manifest))
