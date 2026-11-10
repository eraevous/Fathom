"""FT-R17 fixture for spec027: one synthetic table, two reports (numeric target y, binary target outcome) that
between them show all five type pairs and all three type-pair chart kinds. Synthetic only; deterministic LCG."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tests')]
from test_type_pairs import _five_type_tables  # noqa: E402
from fathom.connectors import CSVConnector  # noqa: E402
from fathom.profiler import profile  # noqa: E402
from fathom.renderers import render_html  # noqa: E402

HERE = Path(__file__).parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE
data = HERE / 'synthetic.csv'
data.write_text(_five_type_tables(), encoding='utf-8')
seen = {}
for target in ('y', 'outcome'):
    result = profile(CSVConnector(data).load(), {'target': target, 'pair_budget': 20})
    (OUT / f'report-{target}.html').write_text(render_html(result), encoding='utf-8')
    for p in result.document['bivariate']:
        tp = p.get('type_pair')
        if tp:
            seen.setdefault(tp['pair_type'], []).append({'report': target, 'pair': [p['left'], p['right']], 'chart': (tp.get('chart') or {}).get('kind')})
print(json.dumps(seen, indent=1, ensure_ascii=False))
