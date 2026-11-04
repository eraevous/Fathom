"""Inspect main68890bf output from its archived source, not this stacked branch."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path(__file__).parent;results={}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for name in ['empty-values','repeated-key']:
  html=Path('/workspace/work/xksj-main-readable/'+name+'.html').read_text()
  doc=json.loads(Path('/workspace/work/xksj-main-readable/'+name+'.json').read_text())
  for width in [1280,390]:
   page=b.new_page(viewport={'width':width,'height':900});page.context.set_offline(True);page.set_content(html)
   headings=page.locator('section>h2').all_text_contents();text=page.locator('body').inner_text()
   assert headings[:3]==['Dictionary','Provenance','Dataset summary']
   assert page.locator('pre').count()==0 and not page.locator('#full-view').is_checked()
   assert doc['source']['sha256'] not in text
   assert page.locator('details.column-entry').count()==len(doc['columns'])
   assert page.locator('details.column-entry[open]').count()==0
   page.locator('#findings').scroll_into_view_if_needed();page.evaluate('(y)=>scrollTo(0,y)',page.locator('#findings').bounding_box()['y']+page.evaluate('scrollY'));page.screenshot(path=str(out/f'{name}-main-{width}.png'))
   results[f'{name}-{width}']={'source':'68890bf','section_order':headings,'pre_blocks':0,'columns_collapsed':True,'source_hash_hidden':True,'visible_text_characters':len(text),'document_width':page.evaluate('document.documentElement.scrollWidth')}
   page.close()
 b.close()
(out/'dom.json').write_text(json.dumps(results,indent=2,sort_keys=True)+'\n')
print('Main is structured prose/tables, collapsed dictionary/evidence, summarized findings; four screenshots.')
