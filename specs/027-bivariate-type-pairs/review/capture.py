"""FT-R17 capture for spec027: actual HTML reports (build.py) in offline Chromium at 1280/390 px, light/dark.

Per view it opens "Selected pair statistics and method details", screenshots one article per type pair and chart
kind (six), stacks them into one image per view (the four review images), and records page overflow, external
requests, script errors and horizontally scrolling regions inside each type-pair block.
Usage: python3 capture.py REPORT_DIR [OUT_DIR]"""
import json
import re
from pathlib import Path
import sys
from PIL import Image
from playwright.sync_api import sync_playwright

SRC = Path(sys.argv[1])
DEST = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parent
PICKS = [('y', 'x', 'numeric×numeric, target chart note'), ('y', 'region', 'category×numeric, target chart note'),
         ('y', 'arm', 'binary×numeric, target chart note'), ('outcome', 'x', 'binary×numeric, group box'),
         ('outcome', 'exposed', 'binary×binary, heat table'), ('outcome', 'tier', 'category×category, heat table')]
checks = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    for width in (1280, 390):
        for theme in ('light', 'dark'):
            parts = []
            for report, left, what in PICKS:
                context = browser.new_context(viewport={'width': width, 'height': 900}, color_scheme=theme, device_scale_factor=1)
                requests, errors = [], []
                context.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else (requests.append(r.request.url), r.abort()))
                page = context.new_page()
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto((SRC / f'report-{report}.html').resolve().as_uri())
                page.locator('details', has=page.locator('summary', has_text='Selected pair statistics and method details')).first.evaluate('e => e.open = true')
                article = page.locator('article', has=page.locator('div.type-pair')).filter(has=page.locator('h3 code').filter(has_text=re.compile('^' + re.escape(left) + '$'))).first
                article.scroll_into_view_if_needed()
                page.wait_for_timeout(100)
                name = f'part-{report}-{left}-{theme}-{width}.png'
                article.screenshot(path=str(DEST / name))
                parts.append(DEST / name)
                block = article.locator('div.type-pair')
                inner = block.evaluate("e => [...e.querySelectorAll('.table-scroll, figure')].filter(x => x.scrollWidth > x.clientWidth + 1).map(x => x.tagName + ':' + x.scrollWidth + '>' + x.clientWidth)")
                checks.append({'image': name, 'what': what, 'report_target': report, 'pair_left': left, 'width': width, 'theme': theme,
                               'external_requests': requests, 'script_errors': errors,
                               'page_overflow': page.evaluate('document.documentElement.scrollWidth > innerWidth'),
                               'scrolling_regions_in_block': inner,
                               'charts': block.locator('svg[data-kind]').evaluate_all('es => es.map(e => [e.dataset.kind, Math.round(e.getBoundingClientRect().width)])')})
                context.close()
            images = [Image.open(x) for x in parts]
            sheet = Image.new('RGB', (max(i.width for i in images), sum(i.height for i in images) + 12 * len(images)), (128, 128, 128))
            y = 0
            for i in images:
                sheet.paste(i, (0, y))
                y += i.height + 12
            sheet.quantize(256).save(DEST / f'typepairs-{theme}-{width}.png', optimize=True)
    browser.close()
(DEST / 'browser-checks.json').write_text(json.dumps({'checks': checks}, indent=1, ensure_ascii=False) + '\n')
print(json.dumps(checks, indent=1, ensure_ascii=False))
