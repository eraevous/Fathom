"""Actual offline review of finding, summaries, transpose and no-script fallback."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path(__file__).parent;checks={}
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for stage in ['before','after']:
  for theme in ['light','dark']:
   for width in [1280,390]:
    page=browser.new_page(viewport={'width':width,'height':900},color_scheme=theme);page.context.set_offline(True);requests=[];page.on('request',lambda r:requests.append(r.url));page.set_content(Path('/tmp/view20-'+stage+'/profile.html').read_text())
    if stage=='after':
     table=page.locator('.distribution-table').nth(1);table.scroll_into_view_if_needed();page.screenshot(path=str(out/f'{stage}-summary-rows-{theme}-{width}.png'))
     text=table.inner_text();b=page.locator('[data-transpose]').nth(1);b.focus();page.keyboard.press('Enter');assert table.get_attribute('data-orientation')=='metrics_as_rows';table.scroll_into_view_if_needed();page.screenshot(path=str(out/f'{stage}-summary-metrics-{theme}-{width}.png'))
     b.focus();page.keyboard.press('Space');assert table.inner_text()==text
     for a in page.locator('#distribution-summaries a').all():assert page.locator(a.get_attribute('href')).count()==1
    else:
     page.locator('.opening').scroll_into_view_if_needed();page.screenshot(path=str(out/f'before-summary-{theme}-{width}.png'))
    finding=page.locator('article[id^="target-group-"]:not([id$="review"])').first;finding.scroll_into_view_if_needed();page.screenshot(path=str(out/f'{stage}-finding-{theme}-{width}.png'))
    assert not requests;overflow=page.evaluate('document.documentElement.scrollWidth>innerWidth');assert not overflow
    checks[f'{stage}-{theme}-{width}']={'requests':requests,'overflow':overflow};page.close()
 for theme in ['light','dark']:
  for width in [1280,390]:
   for orientation in ['columns_as_rows','metrics_as_rows']:
    page=browser.new_page(viewport={'width':width,'height':900},color_scheme=theme,java_script_enabled=False);page.context.set_offline(True);page.set_content(Path('/tmp/view20-'+('after' if orientation=='columns_as_rows' else 'metrics')+'/profile.html').read_text());page.locator('#distribution-summaries').scroll_into_view_if_needed();page.screenshot(path=str(out/f'nojs-{orientation}-{theme}-{width}.png'))
    assert all(not b.is_visible() for b in page.locator('[data-transpose]').all())
    assert page.locator('.distribution-table').first.get_attribute('data-orientation')==orientation
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth');checks[f'nojs-{orientation}-{theme}-{width}']={'controls_hidden':True,'orientation':orientation};page.close()
 browser.close()
(out/'browser-checks.json').write_text(json.dumps(checks,sort_keys=True,indent=2)+'\n')
