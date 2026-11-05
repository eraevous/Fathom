"""Declared long-panel profiling through Fathom's connector/result interface."""
from collections import Counter, defaultdict
from datetime import date, timedelta
from hashlib import sha256
import csv
import io
import itertools
import math
from pathlib import Path
import re
import statistics as st

import pandas as pd

from .connectors import CSVConnector
from .models import GuideDataFrame, ProfilingResult, SchemaContract, canonical_json
from .panel_stats import advance, calendar, estimate, floor, summarize, usable
from .profiler import profile

RULES = {
    'eligibility': 'usable: observed finite nonnegative value, positive known exposure, complete bucket; missing/absent/closed break runs and positive gaps; unequal exposure is an orthogonal flag',
    'training': 'all signals and model parameters use training periods only; evaluation contributes volume context only; inclusive nonoverlapping windows',
    'amplitude': 'population positive CV2; sample variance/mean dispersion; IQR inclusive interpolation; mean per exposure = sum(values)/sum(exposures)',
    'frequency': 'classic SBC ADI=usable/positive; mean positive gap excludes gaps across unavailable periods; no calendar compression',
    'sbc': 'classic descriptive cutoffs: ADI>=1.32 and positive population CV2>=0.49; smooth/erratic below ADI cutoff, intermittent/lumpy above; no automatic model selection',
    'seasonality': 'three complete eligible calendar cycles; adjusted in-sample phase explained variance, not significance; singleton phases omitted',
    'noise': 'oracle estimates conditional on Poisson or NB2 counts, equal exposure and training moments; no parameter uncertainty or fitted forecast',
    'volume': 'sum of known viewed quantities, including partial-bucket subtotals; per-days scales by full calendar duration; missing coverage makes this observed volume, never imputed total',
    'aggregation': 'split training/evaluation first; sum or mean usable members and exposure with same operator; source totals/state counts retained; incomplete/unknown buckets ineligible',
    'metrics': 'exact composite keys; pairwise finite Spearman with average tied ranks; repeated model/window/horizon rows are not independent; disagreement is not failure',
}


def iso(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value): raise ValueError('panel dates require YYYY-MM-DD')
    d = date.fromisoformat(value)
    if not 2 <= d.year <= 9997: raise ValueError('panel calendar years must be 0002..9997')
    return d


def number(value, label, missing=True):
    if value is None or value == '':
        if missing: return None
        raise ValueError(label + ' is required')
    try: n = float(value)
    except (TypeError, ValueError): raise ValueError(label + ' must be finite numeric') from None
    if not math.isfinite(n) or abs(n) > 1e100: raise ValueError(label + ' outside finite numerical cap')
    return n


def read_table(path):
    data = CSVConnector(path).load()
    return data, data.frame.to_dict('records')


def configuration(raw, names):
    allowed = {'series', 'time', 'value', 'period', 'exposure', 'observation_state', 'windows', 'metrics', 'thresholds', 'aggregation', 'aggregate'}
    if not isinstance(raw, dict) or set(raw) - allowed: raise ValueError('unknown panel configuration keys')
    cfg = dict(raw)
    ids = cfg.get('series')
    if not isinstance(ids, list) or not ids or any(not isinstance(n, str) or n not in names or n in {'model', 'window', 'horizon'} for n in ids) or len(set(ids)) != len(ids): raise ValueError('panel series must list known distinct columns outside reserved model/window/horizon keys')
    if cfg.get('period') not in {'day', 'week', 'month'}: raise ValueError('panel period must be day, week or month')
    roles = ids + [cfg.get('time'), cfg.get('value')] + [cfg[k] for k in ('exposure', 'observation_state') if k in cfg]
    if any(not isinstance(n, str) or n not in names for n in roles) or len(set(roles)) != len(roles): raise ValueError('panel roles require distinct known columns')
    agg = cfg.setdefault('aggregation', {'rule': 'sum', 'group_by': []})
    if not isinstance(agg, dict) or set(agg) - {'rule', 'group_by'} or agg.get('rule', 'sum') not in {'sum', 'mean'}: raise ValueError('invalid panel aggregation')
    agg = {**agg, 'rule': agg.get('rule', 'sum'), 'group_by': agg.get('group_by', [])};cfg['aggregation'] = agg
    if not isinstance(agg['group_by'], list) or any(not isinstance(n, str) for n in agg['group_by']) or len(set(agg['group_by'])) != len(agg['group_by']) or any(n not in names or n in roles[len(ids):] for n in agg['group_by']): raise ValueError('invalid aggregation group columns')
    thresholds = cfg.setdefault('thresholds', [])
    if not isinstance(thresholds, list) or len(thresholds) > 30: raise ValueError('invalid volume thresholds')
    seen = set()
    for t in thresholds:
        if not isinstance(t, dict) or set(t) != {'name', 'value', 'per_days'} or not isinstance(t['name'], str) or not t['name'] or t['name'] in seen: raise ValueError('thresholds need unique names, value, per_days')
        if type(t['value']) not in (int, float) or not math.isfinite(t['value']) or t['value'] < 0 or type(t['per_days']) not in (int, float) or not math.isfinite(t['per_days']) or t['per_days'] <= 0: raise ValueError('invalid volume threshold value or period')
        seen.add(t['name'])
    grains = cfg.setdefault('aggregate', [])
    if not isinstance(grains, list) or any(not isinstance(g, str) for g in grains) or len(set(grains)) != len(grains) or any(g not in {'week', 'month'} for g in grains): raise ValueError('aggregate must list distinct week/month views')
    if grains and cfg['period'] != 'day': raise ValueError('generated week/month views require daily source periods; coarser totals cannot be allocated across boundaries')
    for k in ('windows',):
        if k in cfg and (not isinstance(cfg[k], str) or not cfg[k]): raise ValueError(k + ' must be a local CSV path')
    m = cfg.get('metrics')
    if m is not None:
        if not isinstance(m, dict) or set(m) - {'path', 'columns', 'targets'} or not isinstance(m.get('path'), str): raise ValueError('invalid metrics declaration')
        cols = m.get('columns');targets = m.get('targets', cols)
        if not isinstance(cols, list) or not 1 <= len(cols) <= 12 or any(not isinstance(n, str) or not n for n in cols) or len(set(cols)) != len(cols) or not isinstance(targets, list) or any(not isinstance(t, str) for t in targets) or len(set(targets)) != len(targets) or any(t not in cols for t in targets): raise ValueError('declare 1..12 distinct metric columns and targets')
        cfg['metrics'] = {**m, 'targets': targets}
    return cfg


def raw_panel(data, cfg):
    if not len(data.frame) or len(data.frame) > 200000: raise ValueError('panel needs 1..200000 input rows')
    series = defaultdict(dict);groups = {}
    for position, r in enumerate(data.frame.to_dict('records'), 1):
        key = tuple(r[n] for n in cfg['series'])
        if any(v is None for v in key): raise ValueError(f'missing series key at row {position}')
        d = iso(r[cfg['time']]);bucket = floor(d, cfg['period'])
        if d != bucket: raise ValueError('native week/month rows must be labelled by period start')
        if bucket in series[key]: raise ValueError('duplicate series/calendar period')
        value = number(r[cfg['value']], 'panel value')
        exposure = number(r.get(cfg.get('exposure')), 'exposure') if cfg.get('exposure') else 1.0
        state = r[cfg['observation_state']] if cfg.get('observation_state') else 'observed'
        if state not in {'observed', 'missing', 'closed'}: raise ValueError('observation state must be observed, missing or closed')
        if value is not None and value < 0: raise ValueError('panel values must be nonnegative')
        if state == 'closed':
            if value not in (0, None) or cfg.get('exposure') and exposure not in (0, None): raise ValueError('closure contradicts value/exposure')
            exposure = 0.0
        elif state == 'missing':
            if value is not None: raise ValueError('missing measurement contradicts a supplied value')
        elif value is None: state = 'missing'
        if state != 'closed' and exposure is not None and exposure <= 0: raise ValueError('nonpositive exposure requires a closure declaration')
        p = {'period': bucket.isoformat(), 'state': state, 'value': value, 'exposure': exposure,
             'exposure_status': 'known' if exposure is not None else 'missing', 'partial': False}
        series[key][bucket] = p
        group = tuple(r[n] for n in cfg['aggregation']['group_by'])
        if key in groups and groups[key] != group: raise ValueError('aggregation group columns must be constant within series')
        groups[key] = group
    if len(series) > 2000: raise ValueError('panel exceeds 2000 series')
    return series, groups


def windows(series, cfg, root):
    source = None
    if cfg.get('windows'):
        data, rows = read_table(root / cfg['windows']);source = data.source
        required = set(cfg['series'] + ['model', 'train_start', 'train_end', 'eval_start', 'eval_end'])
        if not required <= set(data.frame.columns) or not rows or len(rows) > 10000: raise ValueError('invalid windows CSV schema or row count')
        if 'horizon' in data.frame.columns and any(r.get('horizon') is None for r in rows): raise ValueError('declared window horizon cannot be blank')
    else:
        rows = [{**dict(zip(cfg['series'], key)), 'model': 'not declared', 'window': 'full',
                 'train_start': min(ps).isoformat(), 'train_end': (advance(max(ps), cfg['period']) - timedelta(days=1)).isoformat(),
                 'eval_start': None, 'eval_end': None} for key, ps in sorted(series.items())]
    out = [];seen = set()
    for r in rows:
        key = tuple(r[n] for n in cfg['series'])
        if key not in series or not r['model']: raise ValueError('window references unknown series or blank model')
        start, end = iso(r['train_start']), iso(r['train_end'])
        es, ee = (iso(r[k]) if r.get(k) else None for k in ('eval_start', 'eval_end'))
        if start > end or bool(es) != bool(ee) or es and (end >= es or es > ee): raise ValueError('training/evaluation windows must be ordered and nonoverlapping')
        for a, b in [(start, end)] + ([(es, ee)] if es else []):
            if floor(a, cfg['period']) != a or advance(floor(b, cfg['period']), cfg['period']) - timedelta(days=1) != b: raise ValueError('windows must align with native calendar periods')
        name = r.get('window') or f'{start}/{end}|{es or ""}/{ee or ""}'
        identity = (*key, r['model'], name, r.get('horizon'))
        if identity in seen: raise ValueError('duplicate window composite key')
        seen.add(identity)
        out.append({'series': list(key), 'model': r['model'], 'window': name, 'horizon': r.get('horizon'),
                    'train_start': start.isoformat(), 'train_end': end.isoformat(),
                    'eval_start': es.isoformat() if es else None, 'eval_end': ee.isoformat() if ee else None})
    return sorted(out, key=lambda r: (r['series'], r['model'], r['window'], r['horizon'] or '')), source


def regularize(ps, start, end, grain):
    if not start: return []
    return [dict(ps.get(d, {'period': d.isoformat(), 'state': 'absent', 'value': None, 'exposure': None, 'partial': False})) for d in calendar(iso(start), iso(end), grain)]


def volume(ps, start, end):
    # Volume is the observed subtotal, not a comparable-exposure estimator. Partial
    # buckets retain known quantity even though they cannot enter signal fitting.
    values = [p['value'] for p in ps if p.get('value') is not None and (p['state'] == 'observed' or p.get('known_value_members', 0))]
    return {'value': math.fsum(values) if values else None, 'usable_periods': sum(usable(p) for p in ps), 'known_value_periods': len(values), 'calendar_periods': len(ps),
            'calendar_days': (iso(end) - iso(start)).days + 1 if start else 0,
            'status': 'computed' if values else 'undefined',
            'reservation': 'observed volume only; unavailable periods are not imputed'}


def threshold_rows(train, evaluation, declarations):
    out = []
    for t in declarations:
        def side(v):
            if v['value'] is None or not v['calendar_days']: return {'value': None, 'side': 'unknown', 'distance': None, 'coverage': v['usable_periods']}
            x = v['value'] * t['per_days'] / v['calendar_days']
            return {'value': x, 'side': 'below' if x < t['value'] else 'above' if x > t['value'] else 'at',
                    'distance': x - t['value'], 'usable_periods': v['usable_periods'], 'calendar_periods': v['calendar_periods']}
        a, b = side(train), side(evaluation)
        out.append({**t, 'training': a, 'evaluation': b, 'disagree': a['side'] != b['side'] if 'unknown' not in (a['side'], b['side']) else None})
    return out


def row_result(w, train, evaluation, cfg, grain):
    a, b = volume(train, w['train_start'], w['train_end']), volume(evaluation, w['eval_start'], w['eval_end'])
    stats = summarize(train, grain)
    if grain != cfg['period'] and cfg['aggregation']['rule'] == 'mean':
        for key in ('poisson_mse', 'poisson_median_mae', 'nb2_k', 'nb2_mse'):
            stats['noise'][key] = estimate(status='not estimable', reason='mean aggregation changes count units, even if averages are integers')
    return {**w, 'period': grain, **stats, 'volumes': {'training': a, 'evaluation': b},
            'thresholds': threshold_rows(a, b, cfg['thresholds'])}


def aggregate_periods(collection, grain, rule):
    buckets = defaultdict(list)
    for ps in collection:
        for p in ps: buckets[floor(iso(p['period']), grain)].append(p)
    out = []
    for d, members in sorted(buckets.items()):
        expected = (advance(d, grain) - d).days * len(collection)
        states = dict(Counter(p['state'] for p in members));partial = len(members) != expected
        measured = [p for p in members if usable(p)]
        known_values = [p for p in members if p['state'] == 'observed' and p.get('value') is not None]
        vals = [p['value'] for p in known_values]
        exp = [p['exposure'] for p in members if p['state'] != 'absent' and p.get('exposure') is not None]
        known = math.fsum(vals);total_exp = math.fsum(exp)
        unknown = any(not usable(p) and p['state'] != 'closed' for p in members)
        state = 'closed' if states.get('closed') == len(members) else 'missing' if partial or unknown else 'observed'
        n = len(known_values) if rule == 'mean' else 1
        out.append({'period': d.isoformat(), 'state': state, 'value': known / n if n and vals else None,
                    'exposure': total_exp / n if n and exp else 0 if state == 'closed' else None,
                    'partial': partial, 'known_subtotal': known, 'known_value_members': len(known_values), 'source_exposure_total': total_exp,
                    'constituent_states': states, 'constituents': len(members), 'expected_constituents': expected})
    return out


def flatten(value, prefix='', compact=False):
    out = {}
    for k, v in value.items():
        name = prefix + k
        if compact and name == 'noise.assumption': continue
        if isinstance(v, dict):
            if compact and {'value', 'status', 'reason'} <= v.keys(): v = {'value': v['value'], 'status': v['status']}
            out.update(flatten(v, name + '.', compact=compact))
        elif isinstance(v, list): out[name] = canonical_json(v).strip()
        else: out[name] = v
    return out


def row_key(r):
    return (tuple(r['series']), r['model'], r['window'], r.get('horizon'))


def csv_text(rows):
    fields = sorted({k for r in rows for k in r});stream = io.StringIO(newline='')
    if fields:
        writer = csv.DictWriter(stream, fields, lineterminator='\n');writer.writeheader();writer.writerows(rows)
    return stream.getvalue()


def ranks(values):
    out = [0.0] * len(values);ordered = sorted(range(len(values)), key=values.__getitem__);start = 0
    for _, group in itertools.groupby(ordered, key=values.__getitem__):
        indices = list(group);rank = (start + 1 + start + len(indices)) / 2
        for i in indices: out[i] = rank
        start += len(indices)
    return out


def spearman(a, b):
    x, y = ranks(a), ranks(b)
    if len(x) < 3 or not st.pvariance(x) or not st.pvariance(y): return estimate(status='not estimable', reason='fewer than three pairs or constant ranks')
    return estimate(st.correlation(x, y))


def join_metrics(doc, cfg, root):
    m = cfg.get('metrics')
    if not m: return
    data, metrics = read_table(root / m['path']);key_names = cfg['series'] + ['model', 'window']
    if not set(key_names + m['columns']) <= set(data.frame.columns): raise ValueError('metrics CSV missing declared keys or metrics')
    if set(m['columns']) & set(key_names + ['horizon']): raise ValueError('metric columns cannot be join keys')
    horizon = 'horizon' in data.frame.columns
    index = defaultdict(list);seen = set()
    for r in metrics:
        key = tuple(r[n] for n in key_names);full = key + ((r.get('horizon'),) if horizon else ())
        if any(x is None for x in full) or full in seen: raise ValueError('blank or duplicate metric composite key')
        seen.add(full)
        for n in m['columns']: r[n] = number(r[n], 'metric ' + n)
        index[key].append(r)
    joined = [];matched = set();unmatched = []
    reserved = set(flatten(doc['rows'][0], compact=True)) | {'series'}
    if set(m['columns']) & reserved: raise ValueError('metric names collide with signal columns')
    if set(cfg['series']) & (reserved - {'series'}): raise ValueError('series key collides with generated signal column; rename the input key')
    for r in doc['rows']:
        base = {**flatten(r, compact=True), **dict(zip(cfg['series'], r['series']))};key = tuple(r['series']) + (r['model'], r['window'])
        matches = [v for v in index.get(key, []) if r.get('horizon') is None or v.get('horizon') == r['horizon']]
        if not horizon and r.get('horizon') is not None: raise ValueError('metrics need horizon when windows declare it')
        if not matches:
            unmatched.append(list(key) + ([r['horizon']] if r.get('horizon') is not None else []))
            joined.append({**base, **{n: None for n in m['columns']}})
        for v in matches:
            full = key + ((v['horizon'],) if horizon else ());matched.add(full)
            joined.append({**base, **{n: v[n] for n in m['columns']}, **({'horizon': v['horizon']} if horizon else {})})
    if len(joined) > 200000: raise ValueError('joined panel exceeds 200000 rows')
    unmatched_metrics = sorted([list(k) for k in seen - matched])
    doc['joined'] = joined;doc['metric_join'] = {'source': data.source, 'key_columns': key_names + (['horizon'] if horizon else []),
        'unmatched_signals_count': len(unmatched), 'unmatched_signals': unmatched,
        'unmatched_metrics_count': len(unmatched_metrics), 'unmatched_metrics': unmatched_metrics,
        'horizon_expansion': horizon and any(r.get('horizon') is None for r in doc['rows']),
        'reservation': RULES['metrics']}
    subsets = defaultdict(list);subsets['overall'] = joined
    native_rows = {row_key(r): r for r in doc['rows']}
    for r in joined:
        subsets['SBC: ' + str(r['sbc.value'] or r['sbc.status'])].append(r)
        if cfg['thresholds']:
            key = (tuple(r[n] for n in cfg['series']), r['model'], r['window'], r.get('horizon'))
            native = native_rows.get(key) or native_rows[(key[0], key[1], key[2], None)]
            band = '; '.join(t['name'] + '=' + t['training']['side'] for t in native['thresholds'])
            subsets['Volume band: ' + band].append(r)
        subsets['Slice: ' + canonical_json([r['model'], r['window'], r.get('horizon')]).strip()].append(r)
    for name, rows in sorted(subsets.items()):
        for a, b in itertools.combinations(m['columns'], 2):
            valid = [r for r in rows if r.get(a) is not None and r.get(b) is not None]
            series_count = len({tuple(r[n] for n in cfg['series']) for r in valid})
            doc['disagreement'].append({'subset': name, 'metric_a': a, 'metric_b': b,
                'rows': len(valid), 'series_count': series_count,
                'spearman': spearman([r[a] for r in valid], [r[b] for r in valid]) if series_count >= 3 else estimate(status='not estimable', reason='fewer than three distinct series'), 'reservation': RULES['metrics']})
            if len(doc['disagreement']) > 20000: raise ValueError('metric disagreement exceeds 20000 rows')
    # Existing target analysis, not a new metric evaluator or forecast model.
    fields = sorted({k for r in joined for k in r})
    def csv_cell(v):
        if v is None: return None
        text = str(v)
        return text if text.strip() else None
    frame = pd.DataFrame([{k: csv_cell(r.get(k)) for k in fields} for r in joined], columns=fields, dtype=object)
    source = {'connector': 'panel-metric-join', 'origin': 'joined-signals.csv', 'sha256': sha256(csv_text(joined).encode()).hexdigest()}
    for target in m['targets']:
        result = profile(GuideDataFrame(frame, SchemaContract().resolve(fields), source),
                         {'target': target, 'columns': {n: {'type': 'categorical', 'exclude_from_target': True} for n in key_names + (['horizon'] if horizon else [])},
                          'row_unit': 'series/model/window/horizon observations; repeated series are not independent'})
        doc['target_profiles'].append({'metric': target, 'artifact': result.document})


def build_panel(data, raw_config, root=Path('.')):
    cfg = configuration(raw_config, list(data.frame.columns));series, groups = raw_panel(data, cfg);ws, wsource = windows(series, cfg, Path(root))
    doc = {'kind': 'panel', 'schema_version': 2, 'source': data.source, 'configuration': cfg,
           'rules': RULES, 'rows': [], 'periods': [], 'views': {}, 'comparison': [], 'joined': [],
           'metric_join': None, 'disagreement': [], 'target_profiles': [], 'findings': [],
           'coverage': {'input_rows': len(data.frame), 'input_series': len(series), 'window_rows': len(ws),
                        'series_without_windows': [list(k) for k in sorted(series) if list(k) not in [w['series'] for w in ws]], 'windows_source': wsource}}
    contexts = []
    for w in ws:
        ps = series[tuple(w['series'])];train = regularize(ps, w['train_start'], w['train_end'], cfg['period']);evaluation = regularize(ps, w['eval_start'], w['eval_end'], cfg['period'])
        doc['rows'].append(row_result(w, train, evaluation, cfg, cfg['period']));doc['periods'].append({'training': train, 'evaluation': evaluation});contexts.append((w, train, evaluation))
    native_rows = {row_key(r): r for r in doc['rows']}
    for grain in cfg['aggregate']:
        grouped = defaultdict(list)
        declared_bounds = {}
        for w, a, b in contexts:
            key = groups[tuple(w['series'])] if cfg['aggregation']['group_by'] else tuple(w['series'])
            identity = (key, w['model'], w['window'], w['horizon'])
            bounds = (w['train_start'], w['train_end'], w['eval_start'], w['eval_end'])
            if identity in declared_bounds and declared_bounds[identity] != bounds: raise ValueError('cross-series aggregation requires aligned training/evaluation windows')
            declared_bounds[identity] = bounds
            grouped[(key, w['model'], w['window'], w['horizon'], w['train_start'], w['train_end'], w['eval_start'], w['eval_end'])].append((w, a, b))
        view = {'kind': 'panel', 'schema_version': 2, 'source': data.source, 'configuration': {**cfg, 'period': grain, 'aggregate': [], 'series': cfg['aggregation']['group_by'] or cfg['series']},
                'rules': RULES, 'rows': [], 'periods': [], 'views': {}, 'comparison': [], 'joined': [], 'metric_join': None, 'disagreement': [], 'target_profiles': [], 'findings': [],
                'coverage': {}, 'lineage': {'source': data.source, 'source_period': cfg['period'], 'rule': cfg['aggregation']['rule'], 'group_by': cfg['aggregation']['group_by'], 'state_exposure_rule': RULES['aggregation'], 'members': []}}
        for identity, members in sorted(grouped.items(), key=lambda x: str(x[0])):
            w = {**members[0][0], 'series': list(identity[0])}
            a = aggregate_periods([v[1] for v in members], grain, cfg['aggregation']['rule']);b = aggregate_periods([v[2] for v in members], grain, cfg['aggregation']['rule'])
            row = row_result(w, a, b, cfg, grain);view['rows'].append(row);view['periods'].append({'training': a, 'evaluation': b});view['lineage']['members'].append([v[0]['series'] for v in members])
            for member in members:
                native = native_rows[row_key(member[0])]
                sides_a = [t['training']['side'] for t in native['thresholds']];sides_b = [t['training']['side'] for t in row['thresholds']]
                eval_a = [t['evaluation']['side'] for t in native['thresholds']];eval_b = [t['evaluation']['side'] for t in row['thresholds']]
                if native['sbc']['value'] != row['sbc']['value'] or sides_a != sides_b or eval_a != eval_b:
                    doc['comparison'].append({'source_view': 'native', 'source_series': native['series'], 'view_series': row['series'], 'model': row['model'], 'window': row['window'], 'horizon': row['horizon'], 'view': grain,
                        'source_sbc': native['sbc']['value'], 'view_sbc': row['sbc']['value'], 'source_threshold_sides': sides_a, 'view_threshold_sides': sides_b,
                        'source_evaluation_sides': eval_a, 'view_evaluation_sides': eval_b,
                        'reservation': 'separate generated views; units, eligibility and grouping may differ'})
        doc['views'][grain] = view
    for a, b in itertools.combinations(sorted(doc['views']), 2):
        other = {row_key(r): r for r in doc['views'][b]['rows']}
        for left in doc['views'][a]['rows']:
            right = other[row_key(left)]
            sides_a = [t['training']['side'] for t in left['thresholds']];sides_b = [t['training']['side'] for t in right['thresholds']]
            eval_a = [t['evaluation']['side'] for t in left['thresholds']];eval_b = [t['evaluation']['side'] for t in right['thresholds']]
            if left['sbc']['value'] != right['sbc']['value'] or sides_a != sides_b or eval_a != eval_b:
                doc['comparison'].append({'source_view': a, 'view': b, 'source_series': left['series'], 'view_series': right['series'], 'model': left['model'], 'window': left['window'], 'horizon': left['horizon'],
                    'source_sbc': left['sbc']['value'], 'view_sbc': right['sbc']['value'], 'source_threshold_sides': sides_a, 'view_threshold_sides': sides_b,
                    'source_evaluation_sides': eval_a, 'view_evaluation_sides': eval_b,
                    'reservation': 'separately generated views; eligibility and units may differ'})
    join_metrics(doc, cfg, Path(root))
    for i, r in enumerate(doc['rows']):
        states = r['duration']['states']
        doc['findings'].append({'id': f'panel-{i}', 'kind': 'observation', 'generator': 'rule:panel-v1', 'rule': 'panel_eligibility',
            'message': f"Series {r['series']}: {r['duration']['usable_observations']} usable training periods of {r['duration']['calendar_span']}; states {states}; unequal exposure {r['duration']['unequal_exposure']}.",
            'evidence': [{'path': f'rows.{i}.duration', 'value': r['duration']}], 'uncertainty': 'Measured under declared eligibility; meaning and missingness mechanism unknown.'})
    doc['findings'].append({'id': 'panel-process-question', 'kind': 'question', 'generator': 'rule:panel-v1', 'rule': 'panel_observation_process',
        'message': 'What is the observation process? Are unavailable measurements unrecorded or due to another mechanism, and do declared volume boundaries remain meaningful after aggregation?',
        'evidence': [{'path': 'coverage', 'value': doc['coverage']}], 'uncertainty': 'The table cannot establish meaning, cause or metric direction.'})
    return ProfilingResult(doc)


def panel_files(result):
    from .panel_view import html, markdown
    from .renderers import render_html, render_markdown
    d = result.document
    signal_rows = []
    for r in d['rows']:
        fields = flatten(r, compact=True)
        if set(d['configuration']['series']) & (set(fields) - {'series'}): raise ValueError('series key collides with generated CSV field')
        signal_rows.append({**fields, **dict(zip(d['configuration']['series'], r['series']))})
    files = {'panel.json': result.to_json(), 'panel.html': html(result), 'panel.md': markdown(result),
             'series-signals.csv': csv_text(signal_rows),
             'view-comparison.csv': csv_text([flatten(r) for r in d['comparison']]),
             'joined-signals.csv': csv_text(d['joined']), 'metric-disagreement.csv': csv_text([flatten(r) for r in d['disagreement']])}
    for grain, view in d['views'].items():
        for path, text in panel_files(ProfilingResult(view)).items(): files[f'views/{grain}/{path}'] = text
    for i, target in enumerate(d['target_profiles']):
        r = ProfilingResult(target['artifact']);prefix = f'targets/{i}/'
        files.update({prefix + 'guide-profile.json': r.to_json(), prefix + 'report.html': render_html(r), prefix + 'report.md': render_markdown(r)})
    return files


def validate_panel(d):
    def count(v): return type(v) is int and v >= 0
    def numeric(v): return type(v) in (int, float) and math.isfinite(v)
    def estimates(obj):
        if not isinstance(obj, dict): return
        if 'status' in obj and 'value' in obj:
            if obj['status'] not in {'computed', 'undefined', 'not estimable'} or not isinstance(obj.get('reason'), str): raise ValueError('invalid panel estimate status')
            if obj['status'] != 'computed' and obj['value'] is not None: raise ValueError('unavailable panel estimate must be null')
            if obj['status'] == 'computed' and not (numeric(obj['value']) or obj['value'] in ('smooth', 'erratic', 'intermittent', 'lumpy')): raise ValueError('invalid computed panel estimate')
        for v in obj.values():
            if isinstance(v, dict): estimates(v)
    if d.get('kind') != 'panel' or type(d.get('schema_version')) is not int or d['schema_version'] != 2: raise ValueError('panel requires artifact schema2')
    for name in ('source', 'configuration', 'rules', 'views', 'coverage'):
        if not isinstance(d.get(name), dict): raise ValueError('invalid panel ' + name)
    for name in ('rows', 'periods', 'comparison', 'joined', 'disagreement', 'target_profiles', 'findings'):
        if not isinstance(d.get(name), list): raise ValueError('invalid panel ' + name)
    if not d['rows'] or len(d['rows']) != len(d['periods']): raise ValueError('panel row/period alignment')
    if not isinstance(d['configuration'].get('series'), list) or not d['configuration']['series'] or any(not isinstance(x, str) for x in d['configuration']['series']): raise ValueError('invalid panel series roles')
    if any(not isinstance(d['source'].get(k), str) for k in ('origin', 'sha256')): raise ValueError('invalid panel source')
    if 'lineage' in d and not isinstance(d['lineage'], dict): raise ValueError('invalid panel lineage')
    for r, ps in zip(d['rows'], d['periods']):
        if not isinstance(r, dict) or not isinstance(r.get('series'), list) or any(not isinstance(x, (str, type(None))) for x in r['series']) or any(not isinstance(r.get(k), str) for k in ('model', 'window', 'period', 'train_start', 'train_end')): raise ValueError('invalid panel row key')
        for name in ('duration', 'amplitude', 'frequency', 'wavelength', 'sbc', 'noise', 'volumes'):
            if not isinstance(r.get(name), dict): raise ValueError('invalid panel dimension')
        if r['period'] not in {'day', 'week', 'month'} or len(r['series']) != len(d['configuration']['series']): raise ValueError('invalid panel row period/series')
        iso(r['train_start']);iso(r['train_end'])
        if iso(r['train_start']) > iso(r['train_end']): raise ValueError('invalid panel training bounds')
        if r.get('eval_start') is not None:
            if iso(r['eval_start']) <= iso(r['train_end']) or iso(r['eval_start']) > iso(r.get('eval_end')): raise ValueError('invalid panel evaluation bounds')
        elif r.get('eval_end') is not None: raise ValueError('invalid panel evaluation end')
        dur = r['duration']
        if any(not count(dur.get(k)) for k in ('calendar_span', 'usable_observations')) or not isinstance(dur.get('states'), dict) or any(k not in {'observed', 'missing', 'absent', 'closed'} or not count(v) for k, v in dur['states'].items()) or type(dur.get('unequal_exposure')) is not bool: raise ValueError('invalid panel duration counts')
        if not {'mean', 'zero_share', 'positive_mean', 'positive_cv2', 'dispersion_to_mean', 'mean_per_exposure', 'iqr'} <= r['amplitude'].keys(): raise ValueError('incomplete panel amplitude')
        if not {'poisson_mse', 'poisson_median_mae', 'nb2_mse', 'nb2_k'} <= r['noise'].keys(): raise ValueError('incomplete conditional noise floors')
        if not {'coverage', 'adi', 'positive_probability', 'longest_zero_run', 'longest_missing_run', 'mean_positive_gap', 'positive_gap_cv2'} <= r['frequency'].keys(): raise ValueError('incomplete panel frequency')
        for cycle in ('week', 'month', 'year'):
            item = r['wavelength'].get(cycle)
            if not isinstance(item, dict) or not count(item.get('complete_cycles')) or not isinstance(item.get('strength'), dict): raise ValueError('invalid seasonal panel estimate')
        for name in ('amplitude', 'frequency', 'wavelength', 'sbc', 'noise', 'duration'): estimates(r[name])
        if r['sbc'].get('value') not in {None, 'smooth', 'erratic', 'intermittent', 'lumpy'}: raise ValueError('invalid SBC class')
        if any(not count(r['frequency'].get(k)) for k in ('longest_zero_run', 'longest_missing_run', 'longest_absent_run', 'longest_unavailable_run', 'positive_gaps_used')): raise ValueError('invalid panel run counts')
        if not isinstance(r.get('thresholds'), list) or not isinstance(ps, dict): raise ValueError('invalid panel periods/thresholds')
        for kind in ('training', 'evaluation'):
            if not isinstance(ps.get(kind), list): raise ValueError('invalid panel calendar')
            for p in ps[kind]:
                if not isinstance(p, dict) or p.get('state') not in {'observed', 'missing', 'closed', 'absent'} or not isinstance(p.get('period'), str): raise ValueError('invalid panel period')
                iso(p['period'])
                if any(p.get(k) is not None and (not numeric(p[k]) or p[k] < 0) for k in ('value', 'exposure')) or type(p.get('partial', False)) is not bool: raise ValueError('invalid panel period value/exposure')
        state_counts = {s: sum(p['state'] == s for p in ps['training']) for s in ('observed', 'missing', 'closed', 'absent')}
        if dur['calendar_span'] != len(ps['training']) or dur['usable_observations'] != sum(usable(p) for p in ps['training']) or dur['states'] != state_counts: raise ValueError('panel duration/calendar mismatch')
        for t in r['thresholds']:
            if not isinstance(t, dict) or not isinstance(t.get('name'), str) or any(not numeric(t.get(k)) for k in ('value', 'per_days')) or any(not isinstance(t.get(k), dict) or t[k].get('side') not in {'below', 'above', 'at', 'unknown'} for k in ('training', 'evaluation')): raise ValueError('invalid panel threshold')
    for r in d['disagreement']:
        if not isinstance(r, dict) or any(not isinstance(r.get(k), str) for k in ('subset', 'metric_a', 'metric_b')) or any(not count(r.get(k)) for k in ('rows', 'series_count')) or not isinstance(r.get('spearman'), dict): raise ValueError('invalid metric disagreement')
        estimates(r['spearman'])
    if any(not isinstance(r, dict) for name in ('joined', 'comparison', 'findings') for r in d[name]): raise ValueError('invalid panel table rows')
    if d.get('metric_join') is not None and not isinstance(d['metric_join'], dict): raise ValueError('invalid panel join coverage')
    for key, v in d['views'].items():
        if key not in {'week', 'month'} or not isinstance(v, dict) or not isinstance(v.get('configuration'), dict) or v['configuration'].get('period') != key or v.get('views'): raise ValueError('invalid panel view key or nested view')
        validate_panel(v)
    for t in d['target_profiles']:
        if not isinstance(t, dict) or not isinstance(t.get('metric'), str) or not isinstance(t.get('artifact'), dict) or t['artifact'].get('kind') != 'profile' or not isinstance(t['artifact'].get('purpose'), dict) or t['artifact']['purpose'].get('target') != t['metric']: raise ValueError('invalid panel target profile')
        ProfilingResult(t['artifact'])
