"""Rebuild the public showcase from authored synthetic input, never user data."""
from pathlib import Path
from fathom.config import load_config
from fathom.connectors import CSVConnector
from fathom.profiler import profile
from fathom.renderers import render_html


def main():
    root = Path(__file__).resolve().parents[1]
    # Relative origins make this demo stable across checkout locations.
    import os
    os.chdir(root)
    result = profile(CSVConnector(Path('tests/fixtures/review.csv')).load(),
                     load_config(Path('tests/fixtures/review.yaml')))
    Path('docs/demo-report.html').write_text(render_html(result), encoding='utf-8')
    print('Wrote docs/demo-report.html from tests/fixtures/review.csv (synthetic).')


if __name__ == '__main__':
    main()
