"""Spec 033 benchmark: time `guide profile` on a seeded synthetic table (no real data).

    python scripts/bench_speed.py --rows 200000 --out /tmp/bench

Prints wall seconds. Compare runs on the same machine only.
"""
import argparse, csv, random, subprocess, sys, time
from pathlib import Path


def write_table(path, rows, seed=1):
    rng = random.Random(seed)
    names = [f'x{i}' for i in range(12)] + [f'c{i}' for i in range(6)] + ['date', 'y']
    with open(path, 'w', newline='') as f:
        w = csv.writer(f); w.writerow(names)
        for r in range(rows):
            xs = [rng.gauss(0, 1) for _ in range(12)]
            cs = [rng.choice('abcdefgh') for _ in range(6)]
            day = f'2020-{1 + r // 28 % 12:02d}-{1 + r % 28:02d} {r % 24:02d}:{r % 60:02d}:00'
            w.writerow(xs + cs + [day, 2 * xs[0] + rng.gauss(0, 1)])


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--rows', type=int, default=200000); ap.add_argument('--out', required=True)
    a = ap.parse_args(); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    table = out / 'bench.csv'; write_table(table, a.rows)
    start = time.perf_counter()
    subprocess.run([sys.executable, '-m', 'fathom', 'profile', str(table), '--out', str(out / 'report')], check=True, capture_output=True)
    print(f'{a.rows} rows x 20 columns: {time.perf_counter() - start:.1f} s')


if __name__ == '__main__':
    main()
