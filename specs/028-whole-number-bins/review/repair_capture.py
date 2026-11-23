"""2026-11-12 repairs (#45 review): capture the truncated-last-bin and wide-inset histograms offline.

The wide inset uses a core near 10**11 (the old inset was ~557 units wide in a 450-unit plot); the review's
10**15 example cannot be profiled end to end because of a pre-existing ECDF-geometry rounding failure on main.

Run from the repository root: PYTHONPATH=src python3 specs/028-whole-number-bins/review/repair_capture.py
Uses $CHROME, chromium or google-chrome; scrollbars shown; no network requests allowed."""
import json, os, shutil, tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
from fathom.connectors import CSVConnector
from fathom.profiler import profile
from fathom.renderers import render_html

out = Path(__file__).parent
cases = {'repair-last-bin': ('v\n' + '\n'.join(str(i) for i in range(7)) + '\n', {'bins': 3}),
         'repair-wide-inset': ('big\n' + '\n'.join(str(10 ** 11 + v) for v in range(16) for _ in range(3)) + '\n' + str(10 ** 11 + 100000) + '\n', None)}
checks = {}
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('CHROME') or shutil.which('chromium') or shutil.which('google-chrome'),
                                args=['--no-sandbox'], ignore_default_args=['--hide-scrollbars'])
    for name, (text, cfg) in cases.items():
        src = Path(tempfile.mkdtemp()) / 'in.csv'; src.write_text(text, encoding='utf-8')
        html = render_html(profile(CSVConnector(src).load(), cfg))
        for theme in ('light', 'dark'):
            for width in (1280, 390):
                page = browser.new_page(viewport={'width': width, 'height': 900}, color_scheme=theme)
                page.context.set_offline(True); requests = []; page.on('request', lambda r: requests.append(r.url))
                page.set_content(html)
                page.evaluate("document.querySelectorAll('details').forEach(d=>d.open=true)")
                fig = page.locator('figure.chart:has(svg rect)').filter(has_text='Distribution of').first
                fig.scroll_into_view_if_needed(); box = fig.bounding_box(); y = page.evaluate('scrollY')
                page.screenshot(path=str(out / f'{name}-{width}-{theme}.png'), full_page=True,
                                clip={'x': box['x'], 'y': box['y'] + y, 'width': box['width'], 'height': box['height']})
                checks[f'{name}-{width}-{theme}'] = {'requests': requests, 'page_overflow': page.evaluate('document.documentElement.scrollWidth>innerWidth'),
                                                     'svg_overflow': page.evaluate("[...document.querySelectorAll('figure.chart svg')].filter(s=>s.getBoundingClientRect().right>innerWidth+1).length")}
                page.close()
    browser.close()
(out / 'repair-checks.json').write_text(json.dumps(checks, sort_keys=True, indent=2) + '\n')
print(json.dumps(checks, sort_keys=True))
