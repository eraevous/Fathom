"""Spec 033: speedups must not change any answer (CHARTER rule 7: byte-identical output)."""
import random

from fathom.parsing import reaches
from fathom.quality import copy_evidence
from fathom.temporal_profiles import intraday_profile
from fathom.temporal_formats import parse_temporal


def slow_copy_evidence(left, right):
    share = lambda c, t: c / t if t else None
    joint = [(a, b) for a, b in zip(left, right) if a is not None and b is not None]
    agreement = share(sum(a == b for a, b in zip(left, right)), len(left))
    joint_agreement = share(sum(a == b for a, b in joint), len(joint))
    near = bool(joint and joint_agreement >= .95 and agreement is not None and
                (agreement == 1 or (len(left) >= 5 and len(joint) >= 5 and agreement >= .95)))
    return {"agreement": agreement, "jointly_present": len(joint), "joint_agreement": joint_agreement, "near": near}


def test_reaches_matches_full_count_for_ratio_and_threshold_tests():
    rng = random.Random(33)
    tests = [lambda h, t: h / t >= .8, lambda h, t: h >= t * .8, lambda h, t: h >= t * 1]
    for _ in range(3000):
        n = rng.randint(1, 40)
        p = rng.choice([0, .5, .79, .8, .81, .95, 1])
        values = [rng.random() < p for _ in range(n)]
        for test in tests:
            assert reaches(bool, values, test) == test(sum(values), n)


def test_reaches_stops_early_on_a_hopeless_column():
    seen = []
    def predicate(v):
        seen.append(v)
        return False
    assert reaches(predicate, list(range(1000)), lambda h, t: h >= t) is False
    assert len(seen) == 1


def test_copy_evidence_one_pass_matches_reference():
    rng = random.Random(7)
    for _ in range(2000):
        n = rng.randint(0, 12)
        pool = ['a', 'b', None]
        left = [rng.choice(pool) for _ in range(n)]
        right = [x if rng.random() < .8 else rng.choice(pool) for x in left]
        assert copy_evidence(left, right) == slow_copy_evidence(left, right)


def test_intraday_counts_match_per_cell_reference():
    from datetime import date
    values = ['2024-03-0%d %02d:%02d:%02d' % (d, h, m, s) for d in range(1, 8) for h in (0, 9, 23) for m, s in ((0, 0), (30, 59))]
    values += ['10:15', '11:45 PM', '2024-03-02 09:00+02:00']
    parsed = [(v, p) for v in values if (p := parse_temporal(v)) is not None]
    out, charts = intraday_profile(parsed, 'when', lambda *a, **k: {'args': a, **k})
    for basis in out['bases']:
        ps = [p for _, p in parsed if 'time' in p and p['clock_basis'] == basis['basis']]
        assert basis['hour_counts'] == {f'{h:02d}': sum(p['hour'] == h for p in ps) for h in range(24)}
        assert basis['minute_counts'] == {f'{m:02d}': sum(p['minute'] == m for p in ps) for m in range(60)}
        assert basis['second_counts'] == {f'{s:02d}': sum(p['second'] == s for p in ps) for s in range(60)}
        expected = {day: {f'{h:02d}': sum('date' in p and date.fromisoformat(p['date']).weekday() == i and p['hour'] == h for p in ps) for h in range(24)}
                    for i, day in enumerate(('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'))}
        assert basis['weekday_hour_counts'] == (expected if any('date' in p for p in ps) else {})


# Slice 2: sort once, parse once, select top-k without a full sort.

def reference_percentile(values, p, rule):
    """The pre-slice-2 percentile, copied verbatim so the test doesn't compare the new code with itself."""
    if not values: return None
    ordered=sorted(values);position=(len(ordered)-1)*p/100
    lo=int(position);hi=min(lo+1,len(ordered)-1);w=position-lo
    scale=max(abs(ordered[lo]),abs(ordered[hi]),1)
    return rule((ordered[lo]/scale*(1-w)+ordered[hi]/scale*w)*scale)


def test_sorted_percentile_matches_percentile():
    from fathom.univariate import percentile, sorted_percentile, geometry, stored
    rng = random.Random(330)
    for _ in range(2000):
        values = [rng.choice([rng.gauss(0, 1e6), float(rng.randint(-3, 3)), -0.0, 0.0]) for _ in range(rng.randint(0, 30))]
        ordered = sorted(values)
        for p in (0, 1, 5, 25, 50, 75, 95, 99, 100):
            for rule in (stored, geometry):
                expected = repr(reference_percentile(values, p, rule))  # repr tells -0.0 from 0.0
                assert repr(sorted_percentile(ordered, p, rule)) == expected
                assert repr(percentile(values, p, rule)) == expected


def test_common_matches_full_sort_with_ties():
    from collections import Counter
    from fathom.univariate import common
    rng = random.Random(331)
    for _ in range(2000):
        counter = Counter(rng.choice('abcdefghijklmnop') for _ in range(rng.randint(0, 60)))
        for least in (False, True):
            for limit in (1, 3, 10, 20):
                full = sorted(counter.items(), key=lambda x: (x[1] if least else -x[1], x[0]))[:limit]
                assert common(counter, least, limit) == [{'value': v, 'count': n} for v, n in full]


def test_numeric_profile_parses_each_cell_once(monkeypatch):
    import fathom.univariate as uni
    from fathom.parsing import finite_number
    calls = []
    monkeypatch.setattr(uni, 'finite_number', lambda v: calls.append(v) or finite_number(v))
    values = ['1', '2', '$3', '(4)', 'x', '1,000', '2']
    uni.numeric_profile(values, 'amount', None)
    assert len(calls) == len(values)


def test_quality_parses_each_numeric_cell_once(monkeypatch):
    import fathom.quality as quality
    from fathom.parsing import finite_number
    calls = []
    monkeypatch.setattr(quality, 'finite_number', lambda v: calls.append(v) or finite_number(v))
    rows = [[str(i % 7), 'g%d' % (i % 3), None if i % 5 == 0 else str(i)] for i in range(40)]
    columns = [{'name': n, 'effective_type': t, 'missing': sum(r[i] is None for r in rows), 'inference': {'type': t}}
               for i, (n, t) in enumerate((('a', 'numeric'), ('g', 'categorical'), ('b', 'numeric')))]
    quality.quality_profile(rows, columns, {'columns': {}}, lambda *a, **k: None)
    assert len(calls) == 2 * len(rows)
