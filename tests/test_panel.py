"""Analytic truth, eligibility decoys and training-window invariance for spec014."""
import copy
import csv
from datetime import date, timedelta
import json
from pathlib import Path

import pytest

from fathom.connectors import CSVConnector
from fathom.models import ProfilingResult
from fathom.panel import build_panel, panel_files
from fathom.panel_stats import summarize, poisson_mae

FIX = Path(__file__).parent / 'fixtures/panel'


def periods(values, exposures=None):
    return [{'period': (date(2020, 1, 6) + timedelta(days=i)).isoformat(),
             'state': 'missing' if v is None else 'observed', 'value': v,
             'exposure': (exposures or [1] * len(values))[i]} for i, v in enumerate(values)]


def scalar(v):
    assert v['status'] == 'computed', v
    return v['value']


def test_five_states_and_exact_denominators():
    p = periods([0, 2, None, 4, 0, None, 0]);p[4]['state'] = 'closed';p[4]['exposure'] = 0;p[5]['state'] = 'absent'
    r = summarize(p, 'day')
    assert r['duration']['usable_observations'] == 4
    assert r['duration']['observed_exposure'] == 5
    assert r['duration']['usable_exposure'] == 4
    assert r['duration']['states'] == {'observed': 4, 'missing': 1, 'closed': 1, 'absent': 1}
    assert scalar(r['amplitude']['mean']) == 1.5
    assert scalar(r['amplitude']['zero_share']) == .5
    assert scalar(r['amplitude']['positive_mean']) == 3
    assert scalar(r['amplitude']['positive_cv2']) == pytest.approx(1 / 9)
    assert scalar(r['amplitude']['iqr']) == 2.5
    assert scalar(r['amplitude']['dispersion_to_mean']) == pytest.approx(22 / 9)
    assert scalar(r['amplitude']['mean_per_exposure']) == 1.5
    assert scalar(r['frequency']['adi']) == 2
    assert r['frequency']['mean_positive_gap']['status'] == 'undefined'
    assert r['frequency']['longest_zero_run'] == 1
    assert r['duration']['regime_age']['status'] == 'not estimable'


@pytest.mark.parametrize('values', [[0] * 12, [1] * 28, [.5] * 20])
def test_zero_constant_noncount_decoys(values):
    r = summarize(periods(values), 'day')
    if not any(values):
        assert r['sbc']['status'] == 'undefined'
        assert r['amplitude']['dispersion_to_mean']['status'] == 'undefined'
        assert scalar(r['noise']['poisson_mse']) == 0
    elif values[0] == 1:
        assert r['sbc']['value'] == 'smooth'
        assert r['noise']['nb2_mse']['status'] == 'not estimable'
    else:
        assert r['noise']['poisson_mse']['status'] == 'not estimable'


def test_unequal_exposure_is_not_missing_or_equal_count_evidence():
    r = summarize(periods([1, 2, 1, 2], [1, 2, 1, 2]), 'day')
    assert r['duration']['unequal_exposure'] is True
    assert r['duration']['usable_observations'] == 4
    assert scalar(r['amplitude']['mean_per_exposure']) == 1
    assert r['sbc']['status'] == r['noise']['poisson_mse']['status'] == 'not estimable'


@pytest.mark.parametrize('mean', [0, 1, 10, 1000])
def test_poisson_oracle_median_absolute_error(mean):
    r = poisson_mae(mean);v = scalar(r)
    if mean == 0: assert v == 0
    if mean == 1: assert v == pytest.approx(2 / 2.718281828459045, rel=1e-12)
    assert v >= 0 and v <= mean ** .5 + 1


def test_calendar_strength_and_clean_short_decoys():
    r = summarize(periods([i % 7 for i in range(28)]), 'day')
    assert r['wavelength']['week']['complete_cycles'] == 4
    assert scalar(r['wavelength']['week']['strength']) > .99
    assert summarize(periods(list(range(14))), 'day')['wavelength']['week']['strength']['status'] == 'not estimable'
    assert summarize(periods([1] * 28), 'day')['wavelength']['week']['strength']['status'] == 'undefined'
    gapped = periods([i % 7 for i in range(28)]);gapped[0]['state'] = 'missing'
    y = summarize(gapped, 'day')['wavelength']['week']
    assert y['calendar_cycles_covered'] == 4 and y['complete_cycles'] == 3


def write_csv(path, fields, rows):
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields);w.writeheader();w.writerows(rows)


def build(tmp_path, values, **extra):
    path = tmp_path / 'series.csv'
    write_csv(path, ['id', 'day', 'value'], [{'id': '001', 'day': (date(2020, 1, 1) + timedelta(days=i)).isoformat(), 'value': v} for i, v in enumerate(values)])
    return build_panel(CSVConnector(path).load(), {'series': ['id'], 'time': 'day', 'value': 'value', 'period': 'day', **extra}, tmp_path)


def test_windows_and_aggregate_boundaries_do_not_leak(tmp_path):
    w = tmp_path / 'windows.csv'
    write_csv(w, ['id', 'model', 'window', 'train_start', 'train_end', 'eval_start', 'eval_end'],
              [{'id': '001', 'model': 'm', 'window': 'w', 'train_start': '2020-01-01', 'train_end': '2020-01-20', 'eval_start': '2020-01-21', 'eval_end': '2020-02-09'}])
    a = build(tmp_path, [i % 3 for i in range(40)], windows='windows.csv', aggregate=['week', 'month'])
    b = build(tmp_path, [i % 3 if i < 20 else 100000 for i in range(40)], windows='windows.csv', aggregate=['week', 'month'])
    for x, y in [(a.document, b.document), *[(a.document['views'][g], b.document['views'][g]) for g in ('week', 'month')]]:
        for dimension in ('duration', 'amplitude', 'frequency', 'wavelength', 'sbc', 'noise'):
            assert x['rows'][0][dimension] == y['rows'][0][dimension], dimension
    assert any(p['partial'] for p in a.document['views']['week']['periods'][0]['training'])
    assert a.document['rows'][0]['volumes']['training']['value'] == a.document['views']['week']['rows'][0]['volumes']['training']['value']


def test_thresholds_and_composite_metric_join_with_unmatched_keys(tmp_path):
    w = tmp_path / 'w.csv';fields = ['id', 'model', 'window', 'train_start', 'train_end', 'eval_start', 'eval_end']
    write_csv(w, fields, [{'id': '001', 'model': 'm', 'window': 'w', 'train_start': '2020-01-01', 'train_end': '2020-01-10', 'eval_start': '2020-01-11', 'eval_end': '2020-01-20'}])
    write_csv(tmp_path / 'metrics.csv', ['id', 'model', 'window', 'horizon', 'score_a', 'score_b'],
              [{'id': '001', 'model': 'm', 'window': 'w', 'horizon': '1', 'score_a': 1, 'score_b': 2},
               {'id': '999', 'model': 'm', 'window': 'w', 'horizon': '1', 'score_a': 3, 'score_b': 4}])
    d = build(tmp_path, [0] * 10 + [10] * 10, windows='w.csv',
              thresholds=[{'name': 'synthetic', 'value': 5, 'per_days': 10}],
              metrics={'path': 'metrics.csv', 'columns': ['score_a', 'score_b'], 'targets': ['score_a']}).document
    t = d['rows'][0]['thresholds'][0]
    assert t['training']['side'] == 'below' and t['evaluation']['side'] == 'above' and t['disagree']
    assert d['metric_join']['unmatched_metrics_count'] == 1
    assert d['joined'][0]['id'] == '001' and d['joined'][0]['horizon'] == '1'
    assert d['target_profiles'][0]['artifact']['purpose']['target'] == 'score_a'


def test_synthetic_fixture_found_and_missing_states():
    import yaml
    cfg = yaml.safe_load((FIX / 'panel.yaml').read_text())
    d = build_panel(CSVConnector(FIX / 'panel.csv').load(), cfg, FIX).document
    rows = {r['series'][0]: r for r in d['rows']}
    assert rows['closures']['duration']['states']['closed'] == 12
    assert rows['missing']['duration']['states']['missing'] > 0 and rows['missing']['duration']['states']['absent'] > 0
    assert scalar(rows['overdispersed']['noise']['nb2_k']) > 0
    assert rows['regime']['duration']['regime_age']['status'] == 'not estimable'
    assert scalar(rows['weekly']['wavelength']['week']['strength']) > .8
    assert rows['annual_short']['wavelength']['year']['strength']['status'] == 'not estimable'
    assert scalar(rows['annual_long']['wavelength']['year']['strength']) > .8
    assert rows['exposure']['duration']['unequal_exposure']


def test_saved_artifact_and_escaped_report(tmp_path):
    r = build(tmp_path, [0, 1, 2]);p = tmp_path / 'panel.json';p.write_text(r.to_json())
    assert ProfilingResult.load(p).document == r.document
    files = panel_files(r);assert 'series-signals.csv' in files and 'panel.html' in files
    assert files == panel_files(ProfilingResult.load(p))
    d = copy.deepcopy(r.document);d['rows'][0]['model'] = '<img src=x onerror=alert(1)>'
    from fathom.panel_view import html
    assert '<img src=x' not in html(ProfilingResult(d))


@pytest.mark.parametrize('edit', ['duplicate', 'unknown', 'negative', 'state'])
def test_invalid_declarations_fail_without_silent_drop(tmp_path, edit):
    path = tmp_path / 'bad.csv';path.write_text('id,day,value,state\na,2020-01-01,1,observed\n')
    cfg = {'series': ['id'], 'time': 'day', 'value': 'value', 'period': 'day'}
    if edit == 'duplicate': path.write_text(path.read_text() + 'a,2020-01-01,2,observed\n')
    if edit == 'unknown': cfg['time'] = 'nope'
    if edit == 'negative': path.write_text(path.read_text().replace(',1,', ',-1,'))
    if edit == 'state': cfg['observation_state'] = 'state';path.write_text(path.read_text().replace('observed', 'maybe'))
    with pytest.raises(ValueError):build_panel(CSVConnector(path).load(), cfg, tmp_path)


def test_state_runs_are_distinct_and_closures_break_them():
    p = periods([None, None, 0, None, None]);p[1]['state'] = 'absent';p[2]['state'] = 'closed'
    r = summarize(p, 'day')['frequency']
    assert r['longest_missing_run'] == 2 and r['longest_absent_run'] == 1
    assert r['longest_unavailable_run'] == 2 and r['longest_zero_run'] == 0


def test_rank_ties_and_distinct_series_metric_disagreement(tmp_path):
    from fathom.panel import ranks, spearman
    assert ranks([10, 10, 20]) == [1.5, 1.5, 3]
    assert scalar(spearman([1, 2, 2], [3, 2, 2])) == pytest.approx(-1)
    assert spearman([1, 1, 1], [1, 2, 3])['status'] == 'not estimable'
    data = tmp_path / 'data.csv'
    write_csv(data, ['id', 'day', 'value'], [{'id': key, 'day': '2020-01-01', 'value': 1} for key in ['001', '002', '003', '004']])
    write_csv(tmp_path / 'metrics.csv', ['id', 'model', 'window', 'a', 'b'],
              [{'id': key, 'model': 'not declared', 'window': 'full', 'a': i, 'b': 4 - i} for i, key in enumerate(['001', '002', '003'])])
    r = build_panel(CSVConnector(data).load(), {'series': ['id'], 'time': 'day', 'value': 'value', 'period': 'day', 'metrics': {'path': 'metrics.csv', 'columns': ['a', 'b'], 'targets': []}}, tmp_path).document
    overall = next(x for x in r['disagreement'] if x['subset'] == 'overall')
    assert scalar(overall['spearman']) == -1 and overall['series_count'] == overall['rows'] == 3
    assert r['metric_join']['unmatched_signals_count'] == 1 and len(r['joined']) == 4


def test_repeated_model_rows_are_not_three_independent_series(tmp_path):
    data = tmp_path / 'data.csv';data.write_text('id,day,value\n001,2020-01-01,1\n')
    fields = ['id', 'model', 'window', 'train_start', 'train_end', 'eval_start', 'eval_end']
    write_csv(tmp_path / 'w.csv', fields, [{'id': '001', 'model': str(i), 'window': 'w', 'train_start': '2020-01-01', 'train_end': '2020-01-01', 'eval_start': '', 'eval_end': ''} for i in range(3)])
    write_csv(tmp_path / 'm.csv', ['id', 'model', 'window', 'a', 'b'], [{'id': '001', 'model': str(i), 'window': 'w', 'a': i, 'b': i} for i in range(3)])
    cfg = {'series': ['id'], 'time': 'day', 'value': 'value', 'period': 'day', 'windows': 'w.csv', 'metrics': {'path': 'm.csv', 'columns': ['a', 'b'], 'targets': []}}
    d = build_panel(CSVConnector(data).load(), cfg, tmp_path).document
    overall = next(r for r in d['disagreement'] if r['subset'] == 'overall')
    assert overall['rows'] == 3 and overall['series_count'] == 1 and overall['spearman']['status'] == 'not estimable'


def test_cross_series_sum_and_mean_views_preserve_lineage(tmp_path):
    path = tmp_path / 'cross.csv';rows = []
    for key, value in [('a', 1), ('b', 3)]:
        for i in range(14): rows.append({'id': key, 'day': (date(2020, 1, 6) + timedelta(days=i)).isoformat(), 'value': value, 'cohort': 'g'})
    write_csv(path, ['id', 'day', 'value', 'cohort'], rows)
    cfg = {'series': ['id'], 'time': 'day', 'value': 'value', 'period': 'day', 'aggregate': ['week'], 'aggregation': {'rule': 'sum', 'group_by': ['cohort']}}
    d = build_panel(CSVConnector(path).load(), cfg, tmp_path).document['views']['week']
    assert len(d['rows']) == 1 and d['rows'][0]['series'] == ['g']
    assert d['rows'][0]['volumes']['training']['value'] == 56
    assert d['lineage']['members'] == [[['a'], ['b']]]
    assert all(p['constituents'] == p['expected_constituents'] == 14 for p in d['periods'][0]['training'])
    cfg['aggregation']['rule'] = 'mean'
    m = build_panel(CSVConnector(path).load(), cfg, tmp_path).document['views']['week']
    assert scalar(m['rows'][0]['amplitude']['mean']) == 2
    assert m['periods'][0]['training'][0]['source_exposure_total'] == 14
    assert m['rows'][0]['noise']['poisson_mse']['status'] == 'not estimable'


def test_duplicate_metric_keys_are_errors_and_missing_values_stay_missing(tmp_path):
    rows = [{'id': '001', 'model': 'not declared', 'window': 'full', 'a': ''}] * 2
    write_csv(tmp_path / 'm.csv', ['id', 'model', 'window', 'a'], rows)
    cfg = {'path': 'm.csv', 'columns': ['a'], 'targets': []}
    with pytest.raises(ValueError, match='duplicate metric'): build(tmp_path, [1, 2], metrics=cfg)
    write_csv(tmp_path / 'm.csv', ['id', 'model', 'window', 'a'], rows[:1])
    d = build(tmp_path, [1, 2], metrics=cfg).document
    assert d['joined'][0]['a'] is None and d['metric_join']['unmatched_metrics_count'] == 0


def test_long_constant_seasonality_and_poisson_cap_decoys():
    p = [{'period': (date(2018, 1, 1) + timedelta(days=i)).isoformat(), 'state': 'observed', 'value': 1, 'exposure': 1} for i in range(1096)]
    y = summarize(p, 'day')['wavelength']['year']
    assert y['complete_cycles'] == 3 and y['strength']['status'] == 'undefined'
    assert poisson_mae(100001)['status'] == 'not estimable'


@pytest.mark.parametrize('values,expected', [([1, 1], 'smooth'), ([1, 9], 'erratic'), ([0, 0, 0, 1, 1], 'intermittent'), ([0, 0, 0, 1, 9], 'lumpy')])
def test_sbc_classes_have_disclosed_classic_denominators(values, expected):
    assert summarize(periods(values), 'day')['sbc']['value'] == expected


def test_nb2_moment_floor_and_contiguous_gap_variability():
    n = summarize(periods([0, 0, 0, 8]), 'day')['noise']
    assert scalar(n['nb2_k']) == pytest.approx(2 / 7)
    assert scalar(n['nb2_mse']) == 16
    f = summarize(periods([1, 0, 1, 0, 0, 1]), 'day')['frequency']
    assert scalar(f['mean_positive_gap']) == 2.5
    assert scalar(f['positive_gap_cv2']) == .04


def test_native_monthly_calendar_year_strength():
    p = [{'period': date(2018 + i // 12, i % 12 + 1, 1).isoformat(), 'state': 'observed', 'value': i % 12 + 1, 'exposure': 1} for i in range(36)]
    r = summarize(p, 'month')['wavelength']
    assert r['year']['complete_cycles'] == r['year']['calendar_cycles_covered'] == 3
    assert scalar(r['year']['strength']) == 1
    assert r['month']['strength']['status'] == 'not estimable'


def test_cross_series_windows_must_align_instead_of_duplicating_keys(tmp_path):
    path = tmp_path / 'x.csv';path.write_text('id,day,value,cohort\na,2020-01-01,1,g\nb,2020-01-01,1,g\nb,2020-01-02,1,g\n')
    cfg = {'series': ['id'], 'time': 'day', 'value': 'value', 'period': 'day', 'aggregate': ['week'], 'aggregation': {'rule': 'sum', 'group_by': ['cohort']}}
    with pytest.raises(ValueError, match='aligned'): build_panel(CSVConnector(path).load(), cfg, tmp_path)


def test_view_comparison_includes_evaluation_side_changes(tmp_path):
    path = tmp_path / 'v.csv';rows = []
    for key in ('a', 'b'):
        for i in range(21): rows.append({'id': key, 'day': (date(2020, 1, 6) + timedelta(days=i)).isoformat(), 'value': int(key == 'b' and i >= 14), 'cohort': 'g'})
    write_csv(path, ['id', 'day', 'value', 'cohort'], rows)
    write_csv(tmp_path / 'w.csv', ['id', 'model', 'window', 'train_start', 'train_end', 'eval_start', 'eval_end'],
              [{'id': key, 'model': 'm', 'window': 'w', 'train_start': '2020-01-06', 'train_end': '2020-01-19', 'eval_start': '2020-01-20', 'eval_end': '2020-01-26'} for key in ('a', 'b')])
    cfg = {'series': ['id'], 'time': 'day', 'value': 'value', 'period': 'day', 'windows': 'w.csv', 'aggregate': ['week'], 'aggregation': {'rule': 'sum', 'group_by': ['cohort']}, 'thresholds': [{'name': 'synthetic', 'value': .5, 'per_days': 1}]}
    d = build_panel(CSVConnector(path).load(), cfg, tmp_path).document
    changed = next(r for r in d['comparison'] if r['source_series'] == ['a'])
    assert changed['source_evaluation_sides'] == ['below'] and changed['view_evaluation_sides'] == ['above']


@pytest.mark.parametrize('field', ['schema', 'count', 'estimate', 'noise', 'exposure', 'partial', 'disagreement', 'view_path'])
def test_malformed_panel_artifact_is_rejected_at_load(tmp_path, field):
    d = copy.deepcopy(build(tmp_path, [0, 1, 2]).document)
    if field == 'schema': d['schema_version'] = 2.0
    if field == 'count': d['rows'][0]['duration']['usable_observations'] = 'three'
    if field == 'estimate': d['rows'][0]['amplitude']['mean']['value'] = 'numeric?'
    if field == 'noise': del d['rows'][0]['noise']['poisson_mse']
    if field == 'exposure': d['periods'][0]['training'][0]['exposure'] = -1
    if field == 'partial': d['periods'][0]['training'][0]['partial'] = 'false'
    if field == 'disagreement': d['disagreement'] = [{'subset': 'bad'}]
    if field == 'view_path': d['views']['../../escape'] = copy.deepcopy(d)
    with pytest.raises(ValueError): ProfilingResult(d)
