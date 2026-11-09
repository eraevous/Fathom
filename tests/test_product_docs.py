"""Public product front door: local links, honest scope and reproducible synthetic demo."""
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links, self.resources = [], [], []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.append(a['id'])
        if tag == 'a':
            self.links.append(a.get('href', ''))
        if 'src' in a or tag == 'link':
            self.resources.append(a.get('src', a.get('href', '')))


def test_landing_offline_resources_unique_ids_and_working_local_links():
    text = (ROOT / 'docs/index.html').read_text()
    page = Page(); page.feed(text)
    assert len(page.ids) == len(set(page.ids))
    assert not page.resources
    assert 'fetch(' not in text and 'localStorage' not in text
    assert '@import' not in text and 'url(' not in text
    for href in page.links:
        if href.startswith('#'):
            assert href[1:] in page.ids
        elif not href.startswith('https://'):
            assert (ROOT / 'docs' / href.split('#')[0]).is_file(), href
    assert 'Illustrative preview' in text
    assert 'synthetic data' in text and '127.0.0.1' in text
    assert 'sample_rows' in text
    assert 'hidden class="theme"' in text and 'hidden class="copy"' in text
    assert 'prefers-reduced-motion' in text


def test_readme_and_moved_guide_keep_local_references():
    for rel in ['README.md', 'docs/guide.md']:
        path = ROOT / rel
        text = path.read_text()
        for target in re.findall(r'\]\(([^)]+)\)', text):
            if not target.startswith(('https://', '#')):
                assert (path.parent / target.split('#')[0]).exists(), (rel, target)
    readme = (ROOT / 'README.md').read_text()
    assert 'sample_rows: 0' in readme and 'not redaction' in readme
    assert 'not on PyPI' in readme and 'guide serve' in readme
    guide = (ROOT / 'docs/guide.md').read_text()
    assert 'no server is included' not in guide
    assert 'HTML is self-contained and uses no script' not in guide


def test_showcase_rebuild_is_deterministic_and_synthetic():
    demo = ROOT / 'docs/demo-report.html'
    before = demo.read_bytes()
    subprocess.run([sys.executable, 'scripts/build_showcase.py'], cwd=ROOT, check=True, capture_output=True)
    assert demo.read_bytes() == before
    assert b'tests/fixtures/review.csv' in before
    assert b'Fathom' in before
