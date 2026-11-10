"""Build the synthetic type-pair reports reviewed here (same generators as tests/test_type_pairs.py)."""
import sys, tempfile
from pathlib import Path
root = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(root / 'src'), str(root / 'tests')]
from fathom.connectors import CSVConnector
from fathom.profiler import profile
from fathom.renderers import render_html
from test_type_pairs import lcg, csv_text


def numeric():
    u = lcg(7); rows = []
    for i in range(1000):
        x = next(u) * 100; arm = 'ctl' if i % 2 else 'trt'; region = 'ABCD'[(i // 2) % 4]; noise = next(u) * 10
        t = 2 * x + (30 if arm == 'trt' else 0) + {'A': 0, 'B': 40, 'C': 80, 'D': 120}[region] + noise
        rows.append([round(x, 3), arm, region, round(t, 3), round(next(u) * 100, 3), 'yz'[int(next(u) * 2)], 'PQRS'[int(next(u) * 4)]])
    return csv_text(['x', 'arm', 'region', 'target', 'noise_num', 'noise_bin', 'noise_cat'], rows), {'target': 'target', 'pair_budget': 20}


def categorical():
    u = lcg(11); rows = []
    for i in range(300):
        exposed = 'yes' if i % 3 == 0 else 'no'
        outcome = 'hit' if (exposed == 'yes' and next(u) < 0.7) or (exposed == 'no' and next(u) < 0.2) else 'miss'
        rows.append([exposed, 'abc'[i % 3], outcome, round(next(u) * 50 + (20 if outcome == 'hit' else 0), 3)])
    return csv_text(['exposed', 'tier', 'outcome', 'score'], rows), {'target': 'outcome', 'pair_budget': 20}


def capped():
    rows = [[f'Level-{i % 15:02d}', f'Target-{(i * 7) % 13:02d}'] for i in range(600)]
    return csv_text(['many', 'target'], rows), {'target': 'target', 'pair_budget': 5}


def build(out):
    out.mkdir(parents=True, exist_ok=True)
    for name, make in [('numeric', numeric), ('categorical', categorical), ('capped', capped)]:
        text, cfg = make()
        src = Path(tempfile.mkdtemp()) / (name + '.csv'); src.write_text(text, encoding='utf-8')
        (out / (name + '.html')).write_text(render_html(profile(CSVConnector(src).load(), cfg)), encoding='utf-8')


if __name__ == '__main__':
    build(Path(sys.argv[1]))
