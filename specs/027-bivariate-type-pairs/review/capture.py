"""Offline Chromium capture of each type-pair article at 1280/390 in light and dark; no resource request allowed."""
import json, os, shutil, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
src, out = Path(sys.argv[1]), Path(__file__).parent
checks = {}


def shot(page, element, path):
    """Page screenshot clipped to the element: element screenshots omit scrollbars, which are the scroll cue here."""
    element.scroll_into_view_if_needed()
    box = element.bounding_box(); y = page.evaluate('scrollY')
    page.screenshot(path=path, full_page=True, clip={'x': box['x'], 'y': box['y'] + y, 'width': box['width'], 'height': box['height']})

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('CHROME') or shutil.which('chromium') or shutil.which('google-chrome'), args=['--no-sandbox'], ignore_default_args=['--hide-scrollbars'])  # show scrollbars as real browsers do
    for report in ['numeric', 'categorical', 'capped', 'edge']:
        for theme in ['light', 'dark']:
            for width in [1280, 390]:
                page = browser.new_page(viewport={'width': width, 'height': 900}, color_scheme=theme)
                page.context.set_offline(True); requests = []; page.on('request', lambda r: requests.append(r.url))
                page.set_content((src / (report + '.html')).read_text(encoding='utf-8'))
                page.evaluate("document.querySelectorAll('#report-relations details').forEach(d=>d.open=true)")
                articles = page.locator('#report-relations article:has-text("Type-pair measures")')
                key = f'{report}-{theme}-{width}'
                checks[key] = {'requests': requests, 'page_overflow': page.evaluate('document.documentElement.scrollWidth>innerWidth'), 'articles': articles.count(), 'svg_overflow': page.evaluate(
                    "[...document.querySelectorAll('#report-relations article svg')].filter(s=>s.getBoundingClientRect().right>innerWidth+1).length")}
                for i in range(articles.count()):
                    a = articles.nth(i); title = a.locator('h3').inner_text().replace(' × ', '-x-').replace(' ', '_')
                    shot(page, a, str(out / f'{report}-{title}-{theme}-{width}.png'))
                # Target charts the type-pair layer references (scatter for numeric×numeric, grouped box for category×numeric).
                figures = page.locator('#report-relations > div[id^="target-chart-"] > figure.target-chart')
                checks[key]['target_charts'] = figures.count()
                for i in range(figures.count()):
                    fig = figures.nth(i); title = fig.locator('.chart-title').inner_text().replace('Target: ', '').replace(' × ', '-x-').replace(' ', '_')
                    shot(page, fig, str(out / f'{report}-target-chart-{title}-{theme}-{width}.png'))
                checks[key]['table_overflow'] = page.evaluate(
                    "[...document.querySelectorAll('.type-pair .table-scroll')].filter(d=>d.scrollWidth>d.clientWidth+1).length")
                page.close()
    browser.close()
(out / 'checks.json').write_text(json.dumps(checks, sort_keys=True, indent=2) + '\n')
print(json.dumps(checks, sort_keys=True))
