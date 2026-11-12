"""Spec 027: bivariate type-pair layer. Hand formulas, planted pairs, null decoys."""
import csv
import io
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

from fathom.models import ProfilingResult, canonical_json
from fathom.renderers import render_html, render_markdown


def lcg(seed):
    """Deterministic uniform(0,1) stream, so fixtures never depend on a library RNG."""
    state = seed
    while True:
        state = (1103515245 * state + 12345) % 2**31
        yield state / 2**31


def csv_text(header, rows):
    return ','.join(header) + '\n' + ''.join(','.join(str(v) for v in row) + '\n' for row in rows)


def pair_for(doc, left):
    return next(p for p in doc['bivariate'] if p['left'] == left)


# ---------------------------------------------------------------- hand formulas

def test_average_ranks_and_spearman_hand_values():
    from fathom.type_pairs import average_ranks, spearman
    assert average_ranks([10, 20, 20, 30]) == [1, 2.5, 2.5, 4]
    # No ties: rho = 1 - 6*sum(d^2)/(n(n^2-1)) = 1 - 24/120.
    assert spearman([1, 2, 3, 4, 5], [2, 1, 4, 3, 5]) == pytest.approx(0.8)
    # Ties: Pearson on average ranks [1,2.5,2.5,4] vs [1,2,3,4] = 4.5/sqrt(4.5*5).
    assert spearman([1, 2, 2, 3], [1, 2, 3, 4]) == pytest.approx(4.5 / math.sqrt(22.5))
    assert spearman([1, 1, 1], [1, 2, 3]) is None


def test_rank_biserial_matches_glass_formula_and_dominance():
    from fathom.type_pairs import rank_biserial
    assert rank_biserial([1, 2, 3], [4, 5, 6]) == pytest.approx(1)
    assert rank_biserial([4, 5, 6], [1, 2, 3]) == pytest.approx(-1)
    # Mean ranks 3 and 4 of n=6: 2*(4-3)/6; dominance (6-3)/9 gives the same 1/3.
    assert rank_biserial([1, 3, 5], [2, 4, 6]) == pytest.approx(1 / 3)
    assert rank_biserial([1, 2], [1, 2]) == pytest.approx(0)


def test_kruskal_wallis_and_rank_eta_squared():
    from fathom.type_pairs import kruskal_wallis
    h, eta2 = kruskal_wallis([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    # 12/(9*10)*(6^2/3+15^2/3+24^2/3) - 3*10 = 7.2; (H-k+1)/(n-k) = 5.2/6.
    assert h == pytest.approx(7.2) and eta2 == pytest.approx(5.2 / 6)
    h, eta2 = kruskal_wallis([[1, 2], [1, 2]])
    assert h == pytest.approx(0) and eta2 < 0.01


def test_bias_corrected_cramers_v():
    from fathom.type_pairs import cramers_v_corrected
    assert cramers_v_corrected([[10, 0], [0, 10]]) == pytest.approx(1)
    assert cramers_v_corrected([[5, 5], [5, 5]]) == pytest.approx(0)
    # Sparse 3x3 noise: plain V is inflated, corrected V is not larger.
    from fathom.target import association
    table = [[2, 1, 1], [1, 2, 1], [1, 1, 2]]
    cases = [(r, c) for r in range(3) for c in range(3) for _ in range(table[r][c])]
    plain = association('categorical', 'categorical', [(str(a), str(b)) for a, b in cases])['value']
    assert cramers_v_corrected(table) < plain


def test_two_by_two_odds_ratio_risk_difference_phi_and_haldane():
    from fathom.type_pairs import two_by_two
    m = two_by_two(20, 10, 5, 15)
    assert m['odds_ratio'] == pytest.approx(6)
    assert m['odds_ratio_correction'] == 'none'
    assert m['risk_difference'] == pytest.approx(20 / 30 - 5 / 20)
    assert m['phi'] == pytest.approx(250 / math.sqrt(30 * 20 * 25 * 25))
    z = two_by_two(5, 0, 2, 3)
    assert z['odds_ratio'] == pytest.approx(5.5 * 3.5 / (0.5 * 2.5))
    assert 'Haldane' in z['odds_ratio_correction']
    assert z['risk_difference'] == pytest.approx(1 - 0.4)


# ---------------------------------------------------------------- planted pairs

@pytest.fixture
def numeric_target(make_profile):
    u = lcg(7)
    rows = []
    for i in range(1000):
        x = next(u) * 100
        arm = 'ctl' if i % 2 else 'trt'
        region = 'ABCD'[(i // 2) % 4]
        noise = next(u) * 10
        target = 2 * x + (30 if arm == 'trt' else 0) + {'A': 0, 'B': 40, 'C': 80, 'D': 120}[region] + noise
        rows.append([round(x, 3), arm, region, round(target, 3), round(next(u) * 100, 3),
                     'yz'[int(next(u) * 2)], 'PQRS'[int(next(u) * 4)]])
    text = csv_text(['x', 'arm', 'region', 'target', 'noise_num', 'noise_bin', 'noise_cat'], rows)
    return make_profile(text, {'target': 'target', 'pair_budget': 20})


def test_planted_pairs_are_classified_and_measured(numeric_target):
    d = numeric_target.document
    assert pair_for(d, 'x')['type_pair']['pair_type'] == 'numeric×numeric'
    assert pair_for(d, 'arm')['type_pair']['pair_type'] == 'binary×numeric'
    assert pair_for(d, 'region')['type_pair']['pair_type'] == 'category×numeric'
    arm = pair_for(d, 'arm')['type_pair']
    assert arm['measures']['index_level'] == 'trt' and arm['measures']['reference_level'] == 'ctl'
    assert arm['measures']['median_difference'] > 0 and -1 <= arm['measures']['rank_biserial'] <= 1
    region = pair_for(d, 'region')['type_pair']
    assert region['measures']['groups_k'] == 4 and region['measures']['eta_squared_h'] > 0.3
    assert [g['value'] for g in region['groups']] == ['A', 'B', 'C', 'D']
    assert all({'n', 'median', 'q1', 'q3', 'iqr', 'mean'} <= g.keys() for g in region['groups'])
    assert not pair_for(d, 'x')['type_pair']['wording']['near_zero']


def test_null_decoys_are_worded_near_zero_without_direction(numeric_target):
    d = numeric_target.document
    for name in ('noise_num', 'noise_bin', 'noise_cat'):
        tp = pair_for(d, name)['type_pair']
        assert tp['wording']['near_zero'], (name, tp['wording'])
        f = next(f for f in d['findings'] if f.get('rule') == 'type_pair_association' and f['columns'][0] == name)
        assert f['kind'] == 'observation' and 'near zero' in f['message']
        assert 'tends' not in f['message'] and 'higher' not in f['message']
        assert '0.1' in f['gate']


def test_existing_pearson_ranking_and_selection_unchanged(numeric_target):
    d = numeric_target.document
    x = pair_for(d, 'x')
    assert x['method'] == 'pearson' and x['type_pair']['measures']['pearson_r'] == x['statistics']['pearson_r']
    assert 'type_pair' not in {k for r in d['selection']['ranked'] for k in r}
    ranked = [r['left'] for r in d['selection']['ranked']]
    assert ranked == [p['left'] for p in d['bivariate']]
    assert d['selection']['ranking_rule'].startswith('Declared target/literal question-column focus')
    # Only observation findings are added; each pair keeps exactly one review action.
    actions = [f for f in d['findings'] if f['kind'] == 'action' and f['id'].startswith('pair-')]
    assert len(actions) == len(d['bivariate'])
    assert all(f['kind'] == 'observation' for f in d['findings'] if f.get('rule') == 'type_pair_association')


def test_monotone_nonlinear_spearman_exceeds_pearson(make_profile):
    rows = [[i, round(math.exp(i / 3), 6)] for i in range(1, 41)]
    d = make_profile(csv_text(['x', 'y'], rows), {'target': 'y'}).document
    m = pair_for(d, 'x')['type_pair']['measures']
    assert m['spearman_rho'] == pytest.approx(1)
    assert m['spearman_rho'] - m['pearson_r'] >= 0.2 and m['disagreement']
    f = next(f for f in d['findings'] if f.get('rule') == 'type_pair_association')
    assert 'monotone' in f['message']


def test_category_and_binary_targets(make_profile):
    u = lcg(11)
    rows = []
    for i in range(300):
        exposed = 'yes' if i % 3 == 0 else 'no'
        outcome = 'hit' if (exposed == 'yes' and next(u) < 0.7) or (exposed == 'no' and next(u) < 0.2) else 'miss'
        tier = 'abc'[i % 3]
        rows.append([exposed, tier, outcome, round(next(u) * 50 + (20 if outcome == 'hit' else 0), 3)])
    d = make_profile(csv_text(['exposed', 'tier', 'outcome', 'score'], rows), {'target': 'outcome', 'pair_budget': 20}).document
    bb = pair_for(d, 'exposed')['type_pair']
    assert bb['pair_type'] == 'binary×binary'
    t = bb['table']
    assert t['row_levels'] == ['no', 'yes'] and t['column_levels'] == ['hit', 'miss']
    # Index levels are the second in sort order (yes, miss): a=(yes,miss) b=(yes,hit) c=(no,miss) d=(no,hit).
    a, b = t['counts'][1][1], t['counts'][1][0]
    c, dd = t['counts'][0][1], t['counts'][0][0]
    assert bb['measures']['odds_ratio'] == pytest.approx((a * dd) / (b * c), rel=1e-9)
    assert bb['measures']['risk_difference'] == pytest.approx(a / (a + b) - c / (c + dd), rel=1e-9)
    assert bb['chart']['kind'] == 'heat_table'
    assert pair_for(d, 'tier')['type_pair']['pair_type'] == 'category×category'
    bn = pair_for(d, 'score')['type_pair']
    assert bn['pair_type'] == 'binary×numeric' and bn['chart']['kind'] == 'group_box'


def test_two_by_two_zero_cell_reports_haldane(make_profile):
    rows = [['1', '1']] * 6 + [['1', '0']] * 0 + [['0', '1']] * 3 + [['0', '0']] * 5
    d = make_profile(csv_text(['flag', 'event'], rows), {'target': 'event'}).document
    tp = pair_for(d, 'flag')['type_pair']
    assert tp['pair_type'] == 'binary×binary'
    assert tp['measures']['odds_ratio'] == pytest.approx(6.5 * 5.5 / (0.5 * 3.5))
    assert 'Haldane' in tp['measures']['odds_ratio_correction']
    f = next(f for f in d['findings'] if f.get('rule') == 'type_pair_association')
    assert 'Haldane' in f['message']


def test_high_cardinality_table_is_capped_and_over_twenty_stays_excluded(make_profile):
    rows = [[f'L{i % 15:02d}', f'T{(i * 7) % 13:02d}', f'W{i % 25:02d}'] for i in range(600)]
    d = make_profile(csv_text(['many', 'target', 'wide'], rows),
                     {'target': 'target', 'pair_budget': 5, 'columns': {'wide': {'type': 'categorical'}}}).document
    tp = pair_for(d, 'many')['type_pair']
    assert tp['pair_type'] == 'category×category'
    t = tp['table']
    assert len(t['row_levels']) == 10 and len(t['column_levels']) == 10
    assert t['other_row_levels'] == 5 and t['other_column_levels'] == 3
    assert len(t['counts']) == 11 and all(len(r) == 11 for r in t['counts'])
    assert sum(map(sum, t['counts'])) == tp['n'] == 600
    reasons = {e['column']: e['reason'] for e in d['target_analysis']['excluded']}
    assert 'twenty' in reasons['wide']


def test_missingness_pairs_and_no_target_have_no_type_pair(make_profile):
    assert make_profile('x,y\n1,2\n2,4\n3,5\n').document['bivariate'] == []
    csv_rows = 'g,v\n' + 'A,\n' * 10 + 'B,1\n' * 10
    d = make_profile(csv_rows, {'columns': {'g': {'type': 'categorical'}}}).document
    assert all('type_pair' not in p for p in d['bivariate'] if p['method'] == 'missingness_by_group')


# ---------------------------------------------------------------- artifact and views

def test_artifact_validates_and_legacy_without_type_pair_still_loads(numeric_target, tmp_path):
    path = tmp_path / 'p.json'
    path.write_text(numeric_target.to_json(), encoding='utf-8')
    loaded = ProfilingResult.load(path).document
    assert loaded['schema_version'] == 2
    legacy = json.loads(numeric_target.to_json())
    for p in legacy['bivariate']:
        p.pop('type_pair', None)
    legacy['findings'] = [f for f in legacy['findings'] if f.get('rule') != 'type_pair_association']
    path.write_text(canonical_json(legacy), encoding='utf-8')
    assert render_html(ProfilingResult.load(path))
    bad = json.loads(numeric_target.to_json())
    bad['bivariate'][0]['type_pair']['pair_type'] = 'everything×everything'
    path.write_text(canonical_json(bad), encoding='utf-8')
    with pytest.raises(ValueError):
        ProfilingResult.load(path)


def test_reports_show_measures_charts_and_single_comparison_lines(numeric_target, make_profile):
    from fathom.finding_view import comparison_count, finding_tree
    html, md = render_html(numeric_target), render_markdown(numeric_target)
    for text in (html, md):
        assert 'Spearman rho' in text and 'rank-biserial' in text and 'η²H' in text
    d = numeric_target.document
    for f in d['findings']:
        if f.get('rule') == 'type_pair_association':
            tree = finding_tree(f, d)
            assert tree['children']
            assert all(comparison_count(line, f['columns']) <= 1 for line in [tree['text']] + tree['children'])
    rows = [['yes' if i % 3 == 0 else 'no', 'hit' if i % 4 == 0 else 'miss'] for i in range(60)]
    p = make_profile(csv_text(['exposed', 'outcome'], rows), {'target': 'outcome'})
    assert 'data-kind="heat_table"' in render_html(p) and 'odds ratio' in render_markdown(p)


def test_relations_and_findings_csv_carry_new_fields(numeric_target):
    from fathom.tidy import tidy_files
    files = tidy_files(json.loads(numeric_target.to_json()))
    rel = list(csv.DictReader(io.StringIO(files['relations.csv'])))
    assert {'type_pair.pair_type', 'type_pair.measures.spearman_rho', 'type_pair.measures.rank_biserial'} <= set(rel[0])
    assert {r['type_pair.pair_type'] for r in rel} >= {'numeric×numeric', 'binary×numeric', 'category×numeric'}
    found = list(csv.DictReader(io.StringIO(files['findings.csv'])))
    assert any(r.get('rule') == 'type_pair_association' for r in found)


def test_output_is_byte_identical_across_processes(tmp_path):
    u = lcg(3)
    rows = [[round(next(u), 6), 'ab'[i % 2], 'xyz'[i % 3], round(next(u), 6)] for i in range(80)]
    src = tmp_path / 'in.csv'
    src.write_text(csv_text(['n1', 'b1', 'c1', 'target'], rows), encoding='utf-8')
    code = ('import sys;from fathom.connectors import CSVConnector;from fathom.profiler import profile;'
            "sys.stdout.write(profile(CSVConnector(sys.argv[1]).load(),{'target':'target'}).to_json())")
    root = Path(__file__).resolve().parents[1] / 'src'
    outs = [subprocess.run([sys.executable, '-c', code, str(src)], capture_output=True, text=True, check=True,
                           env={'PYTHONPATH': str(root), 'PYTHONHASHSEED': seed}).stdout for seed in ('1', '2')]
    assert outs[0] == outs[1] and '"type_pair"' in outs[0]


# ---------------------------------------------------------------- review fixes (PR #41)

def _cols(*spec):
    return [{'name': n, 'effective_type': t} for n, t in spec]


def test_binary_level_only_present_where_partner_missing_does_not_crash():
    from fathom.type_pairs import describe
    rows = [['a', '1'], ['a', '2'], ['a', '3'], ['b', None], ['b', None], ['c', '4']]
    pair = {'left': 'g', 'right': 'v', 'method': 'grouped_numeric', 'statistics': {}, 'association': {}}
    # Reviewer's case: whole-column binary g, but only 'a' has a numeric partner.
    lone = describe(pair, [['a', '1'], ['a', '2'], ['a', '3'], ['b', None], ['b', None]], _cols(('g', 'categorical'), ('v', 'numeric')))
    assert lone['pair_type'] == 'category×numeric' and lone['measures']['groups_k'] == 1
    tp = describe(pair, rows, _cols(('g', 'categorical'), ('v', 'numeric')))
    # Roles come from complete cases: g has levels a and c there.
    assert tp['pair_type'] == 'binary×numeric' and tp['roles'][0]['levels'] == ['a', 'c']
    assert 'complete cases' in tp['binary_rule']


def test_two_by_two_zero_margin_odds_ratio_not_estimable():
    from fathom.type_pairs import two_by_two
    m = two_by_two(0, 0, 3, 4)
    assert m['odds_ratio'] is None and 'not estimable' in m['odds_ratio_status']
    assert m['risk_difference'] is None and m['phi'] is None


def test_rank_eta_squared_stored_clipped_at_zero():
    from fathom.type_pairs import describe, message
    rows = [['A', '1'], ['A', '2'], ['A', '3'], ['B', '1'], ['B', '2'], ['B', '3'], ['C', '1'], ['C', '2'], ['C', '3']]
    pair = {'left': 'g', 'right': 'v', 'method': 'grouped_numeric', 'statistics': {}, 'association': {}}
    tp = describe(pair, rows, _cols(('g', 'categorical'), ('v', 'numeric')))
    assert tp['measures']['eta_squared_h'] == 0 and 'clipped' in tp['measures']['eta_squared_h_basis']


def test_undefined_kruskal_wallis_h_is_worded_undefined():
    """Name kept for append-only record references; since 5866390168 the wording is the stored reason, not 'undefined'."""
    from fathom.type_pairs import describe, message
    rows = [['A', '5'], ['B', '5'], ['C', '5'], ['A', '5']]
    pair = {'left': 'g', 'right': 'v', 'method': 'grouped_numeric', 'statistics': {}, 'association': {}}
    tp = describe(pair, rows, _cols(('g', 'categorical'), ('v', 'numeric')))
    text = message(pair, tp)
    # Since 5866390168 a null measure prints its stored reason, never 'undefined' or 'None'.
    assert 'None' not in text and 'undefined' not in text and 'Kruskal-Wallis H not estimable: all values tie' in text


def test_spearman_needs_three_cases_and_wording_stays_neutral():
    from fathom.type_pairs import describe, message, spearman
    assert spearman([1, 2], [3, 4]) is None
    pair = {'left': 'x', 'right': 'y', 'method': 'pearson', 'statistics': {'pearson_r': 1.0}, 'association': {}}
    # With roles from complete cases, two numeric cases are two-valued on both sides, so the
    # pair is never read as numeric×numeric and no Spearman direction can be worded from n=2.
    tp = describe(pair, [['1', '3'], ['2', '4']], _cols(('x', 'numeric'), ('y', 'numeric')))
    assert tp['pair_type'] == 'binary×binary' and 'spearman_rho' not in tp['measures']
    assert 'tends' not in message(pair, tp)


# ---------------------------------------------------------------- Kate review (PR #41, review 5837301347)

def _saved(result, tmp_path, mutate):
    doc = json.loads(result.to_json())
    mutate(doc)
    path = tmp_path / 'bad.json'
    path.write_text(canonical_json(doc), encoding='utf-8')
    return path


def _first(doc, kind):
    return next(p['type_pair'] for p in doc['bivariate'] if p.get('type_pair', {}).get('pair_type') == kind)


@pytest.mark.parametrize('kind,mutate', [
    ('binary×numeric', lambda tp: tp.update(chart={'kind': 'group_box'})),
    ('category×numeric', lambda tp: tp.update(chart={'kind': 'target_chart', 'title': 'Target: region × target'})),
    ('numeric×numeric', lambda tp: tp.update(chart={'kind': 'heat_table'})),
    ('category×numeric', lambda tp: [g.pop(k) for g in tp['groups'] for k in ('median', 'q1', 'q3', 'iqr', 'mean')]),
    ('category×numeric', lambda tp: tp.pop('groups')),
    ('binary×numeric', lambda tp: tp.update(pair_type='numeric×numeric')),
    ('binary×numeric', lambda tp: tp['measures'].pop('rank_biserial')),
    ('numeric×numeric', lambda tp: tp['measures'].update(spearman_rho=None)),
    ('binary×numeric', lambda tp: tp['roles'][0].pop('levels', None) or tp['roles'][1].pop('levels', None)),
])
def test_malformed_type_pair_payloads_rejected_before_rendering(numeric_target, tmp_path, kind, mutate):
    path = _saved(numeric_target, tmp_path, lambda d: mutate(_first(d, kind)))
    with pytest.raises(ValueError):
        ProfilingResult.load(path)


@pytest.fixture
def table_target(make_profile):
    rows = [['yes' if i % 3 == 0 else 'no', 'abc'[i % 3], 'hit' if i % 4 == 0 else 'miss'] for i in range(60)]
    return make_profile(csv_text(['exposed', 'tier', 'outcome'], rows), {'target': 'outcome', 'pair_budget': 5})


@pytest.mark.parametrize('kind,mutate', [
    ('binary×binary', lambda tp: tp.pop('table')),
    ('binary×binary', lambda tp: tp['table'].pop('row_column')),
    ('binary×binary', lambda tp: tp['chart'].pop('row_labels')),
    ('binary×binary', lambda tp: tp['chart'].update(counts=[[1, 2, 3]])),
    ('category×category', lambda tp: tp['chart'].update(kind='group_box')),
    ('category×category', lambda tp: tp['measures'].update(cramers_v_bias_corrected=None)),
])
def test_malformed_table_payloads_rejected(table_target, tmp_path, kind, mutate):
    path = _saved(table_target, tmp_path, lambda d: mutate(_first(d, kind)))
    with pytest.raises(ValueError):
        ProfilingResult.load(path)


def test_every_null_measure_carries_a_status_and_reports_show_it():
    from fathom.type_pairs import cramers_v_corrected_status, kruskal_wallis_status, two_by_two, describe, tables
    value, reason = cramers_v_corrected_status([[1, 0], [0, 1]])
    assert value is None and 'not estimable' in reason
    h, e2, reasons = kruskal_wallis_status([[5, 5], [5]])
    assert h is None and e2 is None and reasons['kruskal_wallis_h'] and reasons['eta_squared_h']
    m = two_by_two(0, 3, 0, 4)
    assert all(m[k] is None and 'not estimable' in m[k + '_status'] for k in ('odds_ratio', 'risk_difference', 'phi'))
    rows = [['A', '5'], ['B', '5'], ['C', '5'], ['A', '5']]
    pair = {'left': 'g', 'right': 'v', 'method': 'grouped_numeric', 'statistics': {}, 'association': {}}
    tp = describe(pair, rows, _cols(('g', 'categorical'), ('v', 'numeric')))
    for key, value in tp['measures'].items():
        if value is None:
            assert isinstance(tp['measures'].get(key + '_status'), str), key
    text = str(tables({'type_pair': tp}))
    assert 'all values tie' in text and "'undefined'" not in text


@pytest.mark.parametrize('cells', [(0, 3, 0, 4), (3, 0, 4, 0), (0, 0, 3, 4), (3, 4, 0, 0)])
def test_two_by_two_any_empty_margin_is_not_estimable(cells):
    from fathom.type_pairs import two_by_two
    m = two_by_two(*cells)
    assert m['odds_ratio'] is None and m['risk_difference'] is None and m['phi'] is None


# ---------------------------------------------------------------- reviewer-2 visual pass (FT-R17)

def test_type_pair_views_use_display_formatting(make_profile):
    import re
    from fathom.presentation import formatted
    from fathom.renderers import type_pair_html
    from fathom.type_pairs import tables
    u = lcg(11)
    rows = [['yes' if i % 3 == 0 else 'no', 'abc'[i % 3], 'hit' if next(u) < 0.4 else 'miss', round(next(u) * 50.0 + 0.01 * i, 5)] for i in range(300)]
    d = make_profile(csv_text(['exposed', 'tier', 'outcome', 'score'], rows), {'target': 'outcome', 'pair_budget': 20}).document
    for pair in d['bivariate']:
        html = re.sub(r'<[^>]+>', ' ', type_pair_html(pair))  # visible text only, not SVG coordinates
        assert not re.search(r'\d\.\d{7,}', html), (pair['left'], re.findall(r'\d+\.\d{7,}', html)[:3])
    tier = pair_for(d, 'tier')
    measure_rows = dict(tables(tier)[0]['rows'][:2])
    assert measure_rows["Cramer's V"] == formatted(tier['type_pair']['measures']['cramers_v'])


def test_heat_table_is_an_html_table_with_fixed_size_text_and_scroll_cue(make_profile):
    from fathom.renderers import type_pair_html
    rows = [['yes' if i % 3 == 0 else 'no', 'hit' if i % 4 == 0 else 'miss'] for i in range(60)]
    d = make_profile(csv_text(['exposed', 'outcome'], rows), {'target': 'outcome'}).document
    html = type_pair_html(d['bivariate'][0])
    assert '<table' in html and 'data-kind="heat_table"' in html and '<svg' not in html
    # Recheck 5837820574: a 2x2 cannot overflow, so it carries no scroll note.
    assert 'scroll sideways' not in html


# ---------------------------------------------------------------- reviewer-3 visual pass (5837638868)

def test_null_headline_shows_its_reason_not_undefined(make_profile):
    from fathom.finding_view import finding_tree
    from fathom.type_pairs import tables
    d = make_profile('g,t\na,x\nb,y\nc,z\n', {'target': 't', 'columns': {'g': {'type': 'categorical'}, 't': {'type': 'categorical'}}}).document
    pair = d['bivariate'][0]
    assert pair['type_pair']['wording']['magnitude'] is None
    assert 'bias-corrected' in pair['type_pair']['wording']['magnitude_status']
    f = next(f for f in d['findings'] if f.get('rule') == 'type_pair_association')
    text = str(tables(pair)) + str(finding_tree(f, d)) + render_markdown(ProfilingResult(d))
    assert 'undefined' not in text.replace('Undefined', '')
    assert 'headline magnitude not estimable' in text


def test_disagreement_note_appears_in_measure_table(make_profile):
    from fathom.type_pairs import tables
    rows = [[i, round(math.exp(i / 3), 6)] for i in range(1, 41)]
    pair = make_profile(csv_text(['x', 'y'], rows), {'target': 'y'}).document['bivariate'][0]
    assert any('rank and linear' in r[0] for r in tables(pair)[0]['rows'])


def test_target_chart_reference_links_to_the_chart(numeric_target):
    import re
    html = render_html(numeric_target)
    links = set(re.findall(r'<a href="#(target-chart-\d+)"', html))
    assert links and all(f'id="{a}"' in html for a in links)


def test_binary_level_labels_are_not_rounded(make_profile):
    from fathom.type_pairs import tables
    rows = [['-0.0093456', '1'], ['0.0481234', '0'], ['-0.0093456', '0'], ['0.0481234', '1']]
    pair = make_profile(csv_text(['v', 'flag'], rows), {'target': 'flag'}).document['bivariate'][0]
    text = str(tables(pair))
    assert '-0.0093456' in text and '0.0481234' in text


def test_box_chart_values_match_per_group_table(make_profile):
    import re
    from fathom.renderers import type_pair_html
    u = lcg(5)
    rows = [['hit' if i % 3 else 'miss', round(next(u) * 80.0 + 0.0037 * i, 4)] for i in range(90)]
    pair = pair_for(make_profile(csv_text(['outcome', 'score'], rows), {'target': 'outcome'}).document, 'score')
    html = type_pair_html(pair)
    for g in pair['type_pair']['groups']:
        from fathom.presentation import formatted
        assert html.count('>' + formatted(g['q3']) + '<') >= 2, g


# ---------------------------------------------------------------- reviewer-3 recheck (5837820574)

def test_scroll_note_only_beside_wide_tables(numeric_target):
    import re
    from fathom.renderers import type_pair_html
    d = numeric_target.document
    plain_block = type_pair_html(pair_for(d, 'x'), d['target_analysis']['charts'])
    assert 'scroll-note' not in plain_block and 'scrolls sideways' not in plain_block
    grouped = type_pair_html(pair_for(d, 'region'), d['target_analysis']['charts'])
    # The note sits directly after the wide per-group table, not at the top of the block.
    assert re.search(r'Per-group summary.*?</table></div><p class="scroll-note[^"]*">', grouped, re.S)
    assert grouped.index('scroll-note') > grouped.index('Per-group summary')


def test_type_pair_box_chart_fits_viewport_css(numeric_target):
    text = render_html(numeric_target).split('</style>')[0]
    assert 'min-width:560px' not in text
    assert '.type-pair .chart svg{width:100%' in text


def test_disagreement_rule_is_linked_and_shown(make_profile):
    import re
    from fathom.renderers import type_pair_html
    rows = [[i, round(math.exp(i / 3), 6)] for i in range(1, 41)]
    d = make_profile(csv_text(['x', 'y'], rows), {'target': 'y'}).document
    html = type_pair_html(d['bivariate'][0], d['target_analysis']['charts'])
    link = re.search(r'<a href="#(rule-[0-9a-f]+)">', html)
    assert link and f'id="{link.group(1)}"' in html and 'Disagreement rule:' in html


def test_null_headline_says_not_estimable_once_and_levels_split(make_profile):
    from fathom.type_pairs import tables
    d = make_profile('g,t\na,x\nb,y\nc,z\n', {'target': 't', 'columns': {'g': {'type': 'categorical'}, 't': {'type': 'categorical'}}}).document
    text = str(tables(d['bivariate'][0]))
    assert text.count('not estimable') == text.count('bias-corrected dimensions'), text
    rows = [['yes' if i % 3 == 0 else 'no', 'hit' if i % 4 == 0 else 'miss'] for i in range(60)]
    bb = make_profile(csv_text(['exposed', 'outcome'], rows), {'target': 'outcome'}).document['bivariate'][0]
    labels = [r[0] for r in tables(bb)[0]['rows']]
    assert 'index levels' in labels and 'reference levels' in labels


# ---------------------------------------------------------------- Kate re-review (5838167239)

def test_binary_level_mapping_is_validated(table_target, tmp_path):
    ok = _saved(table_target, tmp_path, lambda d: None)
    ProfilingResult.load(ok)  # the valid sort-order mapping loads
    for mutate in (lambda m: m.update(index_levels=list(reversed(m['index_levels']))),
                   lambda m: m.update(reference_levels=[m['reference_levels'][0], 'other'])):
        path = _saved(table_target, tmp_path, lambda d: mutate(_first(d, 'binary×binary')['measures']))
        with pytest.raises(ValueError):
            ProfilingResult.load(path)


def test_groups_k_must_match_groups(numeric_target, tmp_path):
    path = _saved(numeric_target, tmp_path, lambda d: _first(d, 'category×numeric')['measures'].update(groups_k=99))
    with pytest.raises(ValueError):
        ProfilingResult.load(path)


# ---------------------------------------------------------------- execution review codex:rev-2 (5838328411)

def _mutated_load(result, tmp_path, mutate):
    return _saved(result, tmp_path, mutate)


def test_missing_magnitude_key_rejected_but_explicit_null_with_reason_renders(numeric_target, tmp_path):
    def drop(d):
        w = _first(d, 'numeric×numeric')['wording']
        del w['magnitude']
        w.update(near_zero=False, magnitude_status='not estimable: synthetic missing value')
    with pytest.raises(ValueError):
        ProfilingResult.load(_saved(numeric_target, tmp_path, drop))

    def null(d):
        for tp in [_first(d, 'numeric×numeric')] + [f['evidence'][0]['value'] for f in d['findings']
                                                    if f.get('rule') == 'type_pair_association' and f['evidence'][0]['value']['pair_type'] == 'numeric×numeric']:
            # Since 5864410175 wording must follow the measures, so the headline measures are null too, with reasons.
            tp['measures'].update(pearson_r=None, pearson_r_status='not estimable: synthetic', spearman_rho=None,
                                  spearman_rho_status='not estimable: synthetic', rank_linear_gap=None,
                                  rank_linear_gap_status='not estimable: synthetic', disagreement=False)
            tp['wording'].update(magnitude=None, near_zero=False, magnitude_status='not estimable: synthetic explicit null')
    loaded = ProfilingResult.load(_saved(numeric_target, tmp_path, null))
    assert 'synthetic explicit null' in render_html(loaded) and 'synthetic explicit null' in render_markdown(loaded)


@pytest.mark.parametrize('mutate', [
    lambda c: c.update(x_scale='log10', data=[{**c['data'][0], 'box': {'min': -2, 'q1': -1, 'median': 0, 'q3': 1, 'max': 2}}]),
    lambda c: c.update(plotted='oops'),
    lambda c: c.update(omitted_points=-1),
    lambda c: c.update(x_domain=[0, 1]),
    lambda c: c.update(values_format='raw-ish'),
    lambda c: c['data'][0].update(extra='?'),
])
def test_grouped_box_renderer_fields_validated(table_target, make_profile, tmp_path, mutate):
    u = lcg(5)
    rows = [['hit' if i % 3 else 'miss', round(next(u) * 80.0 + 1, 4)] for i in range(60)]
    p = make_profile(csv_text(['outcome', 'score'], rows), {'target': 'outcome'})
    with pytest.raises(ValueError):
        ProfilingResult.load(_saved(p, tmp_path, lambda d: mutate(pair_for(d, 'score')['type_pair']['chart'])))


import re as _re
BARE_NULL = _re.compile(r"\bundefined\b|\bNone\b(?! recorded| flagged)")  # existing empty-list wording on main


def assert_no_bare_null(text):
    hit = BARE_NULL.search(text)
    assert not hit, text[max(0, hit.start() - 80):hit.end() + 40]


def _small_profiles(make_profile):
    u = lcg(9)
    num = [[round(next(u) * 10, 3), 'ab'[i % 2], 'pqr'[i % 3], round(next(u) * 10 + (i % 3), 3)] for i in range(30)]
    cat = [['yes' if i % 3 == 0 else 'no', 'abc'[i % 3], 'hit' if (i * 7) % 5 < 2 else 'miss', round(next(u) * 5, 3)] for i in range(30)]
    return [make_profile(csv_text(['x', 'arm', 'grp', 'y'], num), {'target': 'y', 'pair_budget': 20}),
            make_profile(csv_text(['exposed', 'tier', 'outcome', 'score'], cat), {'target': 'outcome', 'pair_budget': 20})]


def _paths(value, prefix=()):
    """Every container key and the first list element: enough to touch each field the renderers read."""
    yield prefix
    if isinstance(value, dict):
        for k in value:
            yield from _paths(value[k], prefix + (k,))
    elif isinstance(value, list) and value:
        yield from _paths(value[0], prefix + (0,))


MUTATIONS = [('delete', None), ('null', None), ('text', 'oops'), ('negative', -1), ('float', 2.5),
             ('bool', True), ('list', []), ('dict', {})]


def test_fuzz_type_pair_fields_load_rejects_or_both_renderers_succeed(make_profile):
    import copy
    from fathom.finding_view import finding_tree, html_tree, markdown_tree
    from fathom.renderers import type_pair_html, type_pair_markdown
    from fathom.models import validate_document
    checked = accepted = 0
    for result in _small_profiles(make_profile):
        base = json.loads(result.to_json())
        semantic = []
        targets = [('bivariate', i, 'type_pair') for i, p in enumerate(base['bivariate']) if 'type_pair' in p]
        targets += [('findings', i, 'evidence', 0, 'value') for i, f in enumerate(base['findings']) if f.get('rule') == 'type_pair_association']
        for root in targets:
            node = base
            for k in root:
                node = node[k]
            for path in _paths(node):
                if not path:
                    continue
                for name, value in MUTATIONS:
                    if name == 'delete' and isinstance(path[-1], int):
                        continue
                    doc = copy.deepcopy(base)
                    parent = doc
                    for k in root + path[:-1]:
                        parent = parent[k]
                    if name == 'delete':
                        del parent[path[-1]]
                    else:
                        parent[path[-1]] = copy.deepcopy(value)
                    checked += 1
                    try:
                        validate_document(json.loads(canonical_json(doc)))
                    except ValueError:
                        continue
                    accepted += 1
                    try:
                        # Every path that reads a type-pair block, for every accepted mutation ...
                        charts = doc['target_analysis']['charts']
                        for pair in doc['bivariate']:
                            if 'type_pair' in pair:
                                assert_no_bare_null(type_pair_html(pair, charts) + type_pair_markdown(pair, charts))
                        for f in doc['findings']:
                            if f.get('rule') == 'type_pair_association':
                                tree = finding_tree(f, doc)
                                assert_no_bare_null(html_tree(tree, f['columns']) + markdown_tree(tree, f['columns']))
                        # ... and both full reports for a deterministic sample (full renders cost ~0.2 s each).
                        if accepted % 10 == 1:
                            r = ProfilingResult(doc)
                            render_html(r)
                            render_markdown(r)
                    except Exception as error:  # noqa: BLE001 - any crash after a successful load is the defect
                        raise AssertionError(f'{root + path} {name}: loaded but render failed: {error!r}')
            # Value-level inconsistencies (5864410175): a nulled measure with unchanged wording, flipped near_zero,
            # a shifted magnitude. Each must be rejected on load or render.
            for key in list(node['measures']):
                if key.endswith('_status') or not isinstance(node['measures'][key], (int, float)) or isinstance(node['measures'][key], bool):
                    continue
                semantic.append((root, lambda tp, k=key: tp['measures'].update({k: None, k + '_status': 'not estimable: fuzz'})))
                for bad in (1.5, -1.5, 1e9):  # out-of-range values (5867367630)
                    semantic.append((root, lambda tp, k=key, v=bad: tp['measures'].update({k: v})))
            semantic.append((root, lambda tp: tp['wording'].update(near_zero=not tp['wording']['near_zero'])))
            semantic.append((root, lambda tp: tp['wording'].update(magnitude=0.42)))
        for root, mutate in semantic:
            doc = copy.deepcopy(base)
            node = doc
            for k in root:
                node = node[k]
            mutate(node)
            checked += 1
            try:
                validate_document(json.loads(canonical_json(doc)))
            except ValueError:
                continue
            accepted += 1
            from fathom.type_pairs import RANGES
            for pair in doc['bivariate']:
                for k, v in pair.get('type_pair', {}).get('measures', {}).items():
                    if k in RANGES and v is not None:
                        assert RANGES[k][0] <= v <= RANGES[k][1], (k, v)
            charts = doc['target_analysis']['charts']
            for pair in doc['bivariate']:
                if 'type_pair' in pair:
                    assert_no_bare_null(type_pair_html(pair, charts) + type_pair_markdown(pair, charts))
            for f in doc['findings']:
                if f.get('rule') == 'type_pair_association':
                    assert_no_bare_null(str(finding_tree(f, doc)))
            r = ProfilingResult(doc)
            render_html(r)
            render_markdown(r)
    assert checked > 1000 and accepted


# ---------------------------------------------------------------- Codex bot review (5843951149)

def test_unrepresentable_group_iqr_is_null_with_reason_and_renders(make_profile, tmp_path):
    rows = [['A', '-1e308'], ['A', '-1e308'], ['A', '1e308'], ['A', '1e308']] + [['B', str(v)] for v in (1, 2, 3, 4)]
    p = make_profile(csv_text(['g', 'target'], rows), {'target': 'target', 'columns': {'g': {'type': 'categorical'}}})
    path = tmp_path / 'p.json'
    path.write_text(p.to_json(), encoding='utf-8')
    loaded = ProfilingResult.load(path)
    tp = pair_for(loaded.document, 'g')['type_pair']
    a = next(g for g in tp['groups'] if g['value'] == 'A')
    assert a['iqr'] is None and 'floating-point' in a['iqr_status']
    assert 'floating-point' in render_html(loaded) and 'floating-point' in render_markdown(loaded)
    # The key itself is still required.
    with pytest.raises(ValueError):
        ProfilingResult.load(_saved(p, tmp_path, lambda d: [g.pop('iqr') for g in pair_for(d, 'g')['type_pair']['groups']]))
    # A null without its reason is rejected.
    with pytest.raises(ValueError):
        ProfilingResult.load(_saved(p, tmp_path, lambda d: [g.pop('iqr_status', None) for g in pair_for(d, 'g')['type_pair']['groups']]))


def test_no_rank_direction_when_spearman_is_near_zero(make_profile):
    from fathom.type_pairs import message
    rows = [[0, 0], [1, 4], [2, 3], [3, 2], [100, 1]]
    d = make_profile(csv_text(['x', 'y'], rows), {'target': 'y'}).document
    pair = d['bivariate'][0]
    m = pair['type_pair']['measures']
    assert abs(m['pearson_r']) >= 0.1 and abs(m['spearman_rho']) < 0.1
    text = message(pair, pair['type_pair'])
    assert 'tends' not in text and 'rank measure is near zero' in text


# ---------------------------------------------------------------- Copilot review (5861282816)

def test_type_pair_box_axis_shows_declared_units(make_profile):
    from fathom.renderers import type_pair_html, type_pair_markdown
    u = lcg(4)
    rows = [['hit' if i % 3 else 'miss', round(next(u) * 80.0 + 1, 3)] for i in range(60)]
    d = make_profile(csv_text(['outcome', 'score'], rows), {'target': 'outcome', 'columns': {'score': {'units': 'USD'}}}).document
    pair = pair_for(d, 'score')
    assert pair['type_pair']['chart']['x_label'] == 'score (USD)'
    charts = d['target_analysis']['charts']
    assert 'score (USD)' in type_pair_html(pair, charts) and 'score (USD)' in type_pair_markdown(pair, charts)


def test_near_zero_uses_the_stored_rounded_magnitude():
    from fathom.type_pairs import describe
    rows = [['A', '2'], ['A', '3'], ['B', '0'], ['B', '1'], ['B', '3'], ['B', '4'], ['B', '5']]
    pair = {'left': 'g', 'right': 'v', 'method': 'grouped_numeric', 'statistics': {}, 'association': {}}
    tp = describe(pair, rows, _cols(('g', 'categorical'), ('v', 'numeric')))
    assert tp['pair_type'] == 'binary×numeric' and tp['measures']['rank_biserial'] == 0.1
    assert tp['wording']['magnitude'] == 0.1 and tp['wording']['near_zero'] is False


READING_FRAGMENTS = {'numeric×numeric': 'tends to go with', 'binary×numeric': 'tend to be',
                     'category×numeric': 'Group medians run from', 'binary×binary': 'common when',
                     'category×category': 'Shares of'}


def test_finding_tree_carries_the_reading_sentence(numeric_target, table_target, make_profile):
    from fathom.finding_view import finding_tree
    seen = set()
    cases = [numeric_target, table_target,
             make_profile('g,t\na,x\nb,y\nc,z\n', {'target': 't', 'columns': {'g': {'type': 'categorical'}, 't': {'type': 'categorical'}}})]
    for result in cases:
        d = result.document
        html, md = render_html(result), render_markdown(result)
        for f in d['findings']:
            if f.get('rule') != 'type_pair_association':
                continue
            tp = f['evidence'][0]['value']
            lines = finding_tree(f, d)['children']
            reading = next((line for line in lines if line.startswith('reading: ')), None)
            assert reading, (tp['pair_type'], lines)
            if tp['wording']['magnitude'] is None:
                fragment = 'no direction is stated'
            elif tp['wording']['near_zero']:
                fragment = 'Magnitude near zero'
            else:
                fragment = READING_FRAGMENTS[tp['pair_type']]
            assert fragment in reading, (tp['pair_type'], reading)
            assert fragment in html and fragment in md
            seen.add((tp['pair_type'], fragment))
    assert {k for k, _ in seen} == set(READING_FRAGMENTS)
    assert any(f == 'Magnitude near zero' for _, f in seen) and any(f == 'no direction is stated' for _, f in seen)


# ---------------------------------------------------------------- Copilot review (5864410175)

def test_wording_must_match_stored_measures(numeric_target, tmp_path):
    def null_rb(d):
        tp = _first(d, 'binary×numeric')
        tp['measures'].update(rank_biserial=None, rank_biserial_status='not estimable: synthetic')
    with pytest.raises(ValueError):
        ProfilingResult.load(_saved(numeric_target, tmp_path, null_rb))
    with pytest.raises(ValueError):
        ProfilingResult.load(_saved(numeric_target, tmp_path, lambda d: _first(d, 'numeric×numeric')['wording'].update(near_zero=True)))
    with pytest.raises(ValueError):
        ProfilingResult.load(_saved(numeric_target, tmp_path, lambda d: _first(d, 'category×numeric')['wording'].update(magnitude=0.5)))


def test_reading_is_null_safe_for_every_direction_measure():
    from fathom.type_pairs import reading
    base = {'roles': [{'column': 'g', 'role': 'binary', 'levels': ['a', 'b']}, {'column': 'v', 'role': 'numeric'}],
            'wording': {'magnitude': 0.5, 'near_zero': False}}
    bn = {**base, 'pair_type': 'binary×numeric', 'measures': {'rank_biserial': None, 'index_level': 'b', 'reference_level': 'a'}}
    assert 'no direction is stated' in reading(bn)
    bb = {'pair_type': 'binary×binary', 'roles': [{'column': 'g', 'role': 'binary', 'levels': ['a', 'b']}, {'column': 'h', 'role': 'binary', 'levels': ['x', 'y']}],
          'wording': {'magnitude': 0.5, 'near_zero': False},
          'measures': {'risk_difference': None, 'index_levels': ['b', 'y'], 'reference_levels': ['a', 'x']}}
    assert 'no direction is stated' in reading(bb)


def test_missing_target_chart_is_reported_unavailable_without_a_dead_link(make_profile):
    from fathom.renderers import type_pair_html, type_pair_markdown
    rows = [['', v] for v in [1, 2, 1, 3, 2, 1, 2, 3, 1, 2] * 3 + [1000]] + [[x, t] for x, t in zip(range(5, 11), [0, -1, -2, 0, -1, -2])]
    d = make_profile(csv_text(['x', 'target'], rows), {'target': 'target'}).document
    pair = pair_for(d, 'x')
    charts = d['target_analysis']['charts']
    assert pair['type_pair']['chart']['kind'] == 'target_chart'
    assert not any(c['title'] == pair['type_pair']['chart']['title'] for c in charts)
    html, md = type_pair_html(pair, charts), type_pair_markdown(pair, charts)
    for text in (html, md):
        assert 'not available' in text and 'See: Target' not in text and 'existing target chart' not in text
    assert '#target-chart-' not in html and '#target-chart-' not in md


# ---------------------------------------------------------------- Copilot review (5866390168)

def test_overflowing_differences_print_their_reason():
    from fathom.type_pairs import describe, message, tables, tree
    rows = [['A', v] for v in ('-1.1e308', '-1e308', '-9e307')] + [['B', v] for v in ('9e307', '1e308', '1.1e308')]
    pair = {'left': 'g', 'right': 'v', 'method': 'grouped_numeric', 'statistics': {}, 'association': {}}
    tp = describe(pair, rows, _cols(('g', 'categorical'), ('v', 'numeric')))
    m = tp['measures']
    assert m['median_difference'] is None and 'floating-point' in m['median_difference_status']
    assert m['mean_difference'] is None and 'floating-point' in m['mean_difference_status']
    f = {'columns': ['g', 'v']}
    for text in (message(pair, tp), str(tables({'type_pair': tp})), str(tree(f, tp))):
        assert_no_bare_null(text)
        assert text.count('not representable: the result exceeds the floating-point range') >= 2


def test_no_bare_null_anywhere_in_generated_outputs(numeric_target, table_target, make_profile):
    from fathom.tidy import tidy_files
    from fathom.finding_view import finding_tree, html_tree, markdown_tree
    from fathom.renderers import type_pair_html, type_pair_markdown
    rows = [['A', v] for v in ('-1.1e308', '-1e308', '-9e307')] + [['B', v] for v in ('9e307', '1e308', '1.1e308')]
    cases = [numeric_target, table_target, *_small_profiles(make_profile),
             make_profile('g,t\na,x\nb,y\nc,z\n', {'target': 't', 'columns': {'g': {'type': 'categorical'}, 't': {'type': 'categorical'}}}),
             make_profile(csv_text(['g', 'v'], rows), {'target': 'v', 'columns': {'g': {'type': 'categorical'}}})]
    kinds = set()
    for result in cases:
        d = result.document
        kinds |= {p['type_pair']['pair_type'] for p in d['bivariate'] if 'type_pair' in p}
        for f in d['findings']:
            if f.get('rule') == 'type_pair_association':
                assert_no_bare_null(f['message'])
                assert_no_bare_null(str(finding_tree(f, d)))
        # Everything type-pair code prints. The generic raw-evidence disclosure (pre-existing on main) prints stored
        # JSON nulls as 'None' for every finding, so the full page is not swept.
        charts = d['target_analysis']['charts']
        for pair in d['bivariate']:
            if 'type_pair' in pair:
                assert_no_bare_null(type_pair_html(pair, charts) + type_pair_markdown(pair, charts))
        for f in d['findings']:
            if f.get('rule') == 'type_pair_association':
                tree = finding_tree(f, d)
                assert_no_bare_null(html_tree(tree, f['columns']) + markdown_tree(tree, f['columns']))
        render_html(result), render_markdown(result)
        files = tidy_files(json.loads(result.to_json()))
        assert_no_bare_null(files['findings.csv'] + files['relations.csv'])
    assert kinds == set(READING_FRAGMENTS)


# ---------------------------------------------------------------- Copilot review (5867367630)

def _consistent_nxn(tp, r, rho, gap, disagreement):
    tp['measures'].update(pearson_r=r, spearman_rho=rho, rank_linear_gap=gap, disagreement=disagreement)
    tp['wording'].update(magnitude=max(abs(r), abs(rho)), near_zero=max(abs(r), abs(rho)) < 0.1)


def test_rank_linear_gap_and_disagreement_must_be_recomputable(numeric_target, tmp_path):
    with pytest.raises(ValueError, match='out of range|does not match'):  # Copilot's example: 2.5 is outside [-1, 1]
        ProfilingResult.load(_saved(numeric_target, tmp_path, lambda d: _consistent_nxn(_first(d, 'numeric×numeric'), 0.5, 0.6, 2.5, True)))
    with pytest.raises(ValueError, match='does not match'):
        ProfilingResult.load(_saved(numeric_target, tmp_path, lambda d: _consistent_nxn(_first(d, 'numeric×numeric'), 0.5, 0.6, 0.1, True)))
    # Valid: gap is |rho| - |r| (signed, range [-1, 1]); disagreement follows the disclosed 0.2 cut.
    ProfilingResult.load(_saved(numeric_target, tmp_path, lambda d: _consistent_nxn(_first(d, 'numeric×numeric'), 0.5, 0.6, 0.1, False)))
    ProfilingResult.load(_saved(numeric_target, tmp_path, lambda d: _consistent_nxn(_first(d, 'numeric×numeric'), 0.3, 0.5, 0.2, True)))


@pytest.mark.parametrize('kind,key,value', [
    ('numeric×numeric', 'pearson_r', 1.5), ('numeric×numeric', 'spearman_rho', -1.2),
    ('binary×numeric', 'rank_biserial', 1.01), ('category×numeric', 'eta', 1.2), ('category×numeric', 'eta', -0.1),
    ('category×numeric', 'eta_squared_h', -0.5), ('category×numeric', 'eta_squared_h', 1.5),
    ('category×numeric', 'kruskal_wallis_h', -3),
])
def test_measure_bounds_numeric_target(numeric_target, tmp_path, kind, key, value):
    with pytest.raises(ValueError, match='out of range'):
        ProfilingResult.load(_saved(numeric_target, tmp_path, lambda d: _first(d, kind)['measures'].update({key: value})))


@pytest.mark.parametrize('kind,key,value', [
    ('binary×binary', 'phi', 1.5), ('binary×binary', 'risk_difference', -1.5), ('binary×binary', 'odds_ratio', 0),
    ('binary×binary', 'odds_ratio', -2), ('category×category', 'cramers_v', 1.5), ('category×category', 'cramers_v_bias_corrected', -0.2),
])
def test_measure_bounds_table_target(table_target, tmp_path, kind, key, value):
    with pytest.raises(ValueError, match='out of range'):
        ProfilingResult.load(_saved(table_target, tmp_path, lambda d: _first(d, kind)['measures'].update({key: value})))


def test_two_by_two_measures_must_match_the_stored_table(table_target, tmp_path):
    def shift(d):
        tp = _first(d, 'binary×binary')
        tp['table']['counts'][0][0] += 1
        tp['n'] += 1
    with pytest.raises(ValueError, match='not match'):
        ProfilingResult.load(_saved(table_target, tmp_path, shift))
    with pytest.raises(ValueError, match='does not match'):
        ProfilingResult.load(_saved(table_target, tmp_path, lambda d: _first(d, 'category×category')['measures'].update(rows_k=7)))


def test_boundary_values_load(make_profile, tmp_path):
    rows = [[i, 2 * i + 1] for i in range(1, 11)]
    p = make_profile(csv_text(['x', 'y'], rows), {'target': 'y'})
    m = p.document['bivariate'][0]['type_pair']['measures']
    assert m['pearson_r'] == 1 and m['spearman_rho'] == 1 and m['rank_linear_gap'] == 0
    path = tmp_path / 'b.json'
    path.write_text(p.to_json(), encoding='utf-8')
    ProfilingResult.load(path)
    rows = [['a', 'x']] * 4 + [['b', 'y']] * 4
    p = make_profile(csv_text(['flag', 'event'], rows), {'target': 'event'})
    m = p.document['bivariate'][0]['type_pair']['measures']
    assert m['phi'] == 1 and m['risk_difference'] == 1 and m['odds_ratio'] > 0
    path.write_text(p.to_json(), encoding='utf-8')
    ProfilingResult.load(path)
