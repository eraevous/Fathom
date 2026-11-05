"""Script-free panel reports derived only from the saved artifact."""
from html import escape
import json

from .palette import theme_css
from .presentation import formatted


def cell(value):
    if value is None: return '—'
    if isinstance(value, bool): return 'Yes' if value else 'No'
    if isinstance(value, (int, float)): return formatted(value)
    if isinstance(value, (list, dict)): return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def table(headers, rows, caption=''):
    cls = 'measures' if headers[:3] == ['Measure', 'Value', 'Status'] else 'facts' if headers == ['Measure', 'Value'] else 'review'
    return ('<div class="scroll"><table class="' + cls + '"><caption>' + escape(caption) + '</caption><thead><tr>'
            + ''.join('<th scope="col">' + escape(h) + '</th>' for h in headers) + '</tr></thead><tbody>'
            + ''.join('<tr>' + ''.join('<td>' + escape(cell(v)) + '</td>' for v in row) + '</tr>' for row in rows) + '</tbody></table></div>')


def measures(value, path=''):
    rows = []
    order = ('calendar_span', 'usable_observations', 'observed_exposure', 'usable_exposure', 'source_observed_exposure', 'states', 'unequal_exposure', 'regime_age',
             'mean', 'zero_share', 'positive_mean', 'positive_cv2', 'dispersion_to_mean', 'mean_per_exposure', 'iqr', 'week', 'month', 'year',
             'coverage', 'adi', 'positive_probability', 'observed_zero_periods', 'observed_positive_periods', 'longest_zero_run', 'longest_missing_run', 'longest_absent_run', 'longest_unavailable_run', 'mean_positive_gap', 'positive_gap_cv2', 'positive_gaps_used',
             'assumption', 'poisson_mse', 'poisson_median_mae', 'nb2_k', 'nb2_mse', 'training', 'evaluation')
    for key in sorted(value, key=lambda k: (order.index(k) if k in order else len(order), k)):
        item = value[key]
        label = (path + ('complete_eligible_cycles' if key == 'complete_cycles' else key)).replace('_', ' ')
        if isinstance(item, dict) and 'status' in item and 'value' in item:
            rows.append([label, item['value'], item['status'], item.get('reason') or item.get('note') or item.get('formula') or item.get('estimator') or ''])
        elif isinstance(item, dict): rows.extend(measures(item, label + ' / '))
        else: rows.append([label, item, '', ''])
    return rows


def html(result):
    d = json.loads(result.to_json())
    css = theme_css() + '''body{font:16px/1.5 system-ui,sans-serif;background:var(--surface);color:var(--ink);max-width:1140px;margin:auto;padding:24px 16px}
    h1{font-size:2rem}h2{border-bottom:2px solid var(--accent);padding-bottom:6px}h3{margin-bottom:8px}a{color:var(--link)}
    details{border:1px solid var(--border);background:var(--panel);padding:14px;margin:16px 0;border-radius:6px}summary{cursor:pointer;font-weight:600;overflow-wrap:anywhere}
    .scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}caption{text-align:left;font-weight:600;margin:8px 0}
    th,td{text-align:left;vertical-align:top;padding:7px 10px;border-bottom:1px solid var(--border);overflow-wrap:anywhere}th{background:var(--tint)}
    th{white-space:nowrap}.facts th:first-child,.facts td:first-child{min-width:130px;width:28%}
    .measures{min-width:520px;table-layout:fixed}.measures th:nth-child(1){width:31%}.measures th:nth-child(2){width:15%}.measures th:nth-child(3){width:20%}.measures th:nth-child(4){width:34%}
    .measures td:nth-child(2){white-space:nowrap;text-align:right}.measures td:nth-child(3){overflow-wrap:normal}.measures td{overflow-wrap:normal}
    .review td{overflow-wrap:normal}.review td:first-child{min-width:100px}
    td:nth-child(2){font-variant-numeric:tabular-nums}p{max-width:95ch}.muted{color:var(--muted)}.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}
    @media(max-width:800px){.cards{grid-template-columns:minmax(0,1fr)}body{padding:16px 12px}th,td{padding:6px}}
    @media print{details{break-inside:auto}.cards{display:block}}'''
    out = ['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
           '<title>Fathom panel signals</title><style>' + css + '</style><body><h1>Panel signals</h1>',
           '<p>Declared series and calendar. Every signal and model parameter uses <strong>training only</strong>. Evaluation contributes volume context only. Missing measurements, absent periods and closures are not zeros.</p>',
           table(['Measure', 'Value'], [['Signal rows', len(d['rows'])], ['Source', d['source'].get('origin')], ['Source SHA256', d['source'].get('sha256')],
                                       ['Native period', d['configuration'].get('period')], ['Aggregation rule', d.get('lineage', {}).get('rule', 'not applied')]], 'Dataset and provenance'),
           '<p>Unequal exposure is a separate flag. Comparable-exposure SBC, seasonal and noise estimates are withheld where it occurs. Noise floors are <strong>model-conditional oracle estimates</strong>, not fitted forecasts or a guaranteed bound.</p>']
    out.append('<details><summary>Declared column roles</summary>' + table(['Measure', 'Value'], [[k.replace('_', ' '), d['configuration'].get(k)] for k in ('series', 'time', 'value', 'period', 'exposure', 'observation_state')]) + '</details>')
    out.append('<p>Rule-generated observations (<code>rule:panel-v1</code>). Open a series/window for its four dimensions and evidence. Rows can repeat the same source periods.</p>')
    for i, r in enumerate(d['rows']):
        label = ' · '.join(str(x) for x in r['series']) + ' / ' + r['model'] + ' / ' + r['window']
        dur, freq = r['duration'], r['frequency'];states = dur['states']
        coverage = (f"{dur['usable_observations']:,}/{dur['calendar_span']:,} usable · {freq['observed_zero_periods']:,} zero · "
                    f"{states.get('missing', 0):,} missing · {states.get('absent', 0):,} absent · {states.get('closed', 0):,} closed")
        out.append('<details class="series-entry"><summary>' + escape(label) + ' — ' + escape(coverage) + (' · unequal exposure' if dur['unequal_exposure'] else '') + ' · SBC: ' + escape(str(r['sbc'].get('value') or r['sbc']['status'])) + '</summary>')
        out.append('<p>Training ' + escape(r['train_start']) + ' to ' + escape(r['train_end']) + '; evaluation ' + escape(str(r.get('eval_start') or 'not declared')) + ' to ' + escape(str(r.get('eval_end') or 'not declared')) + '.</p><div class="cards">')
        for dim in ('duration', 'amplitude', 'wavelength', 'frequency'):
            out.append('<section><h2>' + dim.title() + '</h2>' + table(['Measure', 'Value', 'Status', 'Reason / context'], measures(r[dim]), dim.title() + ' — training') + '</section>')
        out += ['</div><h3>Conditional noise floors</h3>', table(['Measure', 'Value', 'Status', 'Assumption / reason'], measures(r['noise'])),
                '<h3>Observed volume and declared boundaries</h3><p>Known quantity is an observed subtotal. Missing and partial coverage are not imputed; their known quantities remain in volume even when ineligible for signals.</p>',
                table(['Window', 'Known quantity', 'Known-value periods', 'Usable periods', 'Calendar periods', 'Calendar days', 'Status'],
                    [[window.title(), v['value'], v['known_value_periods'], v['usable_periods'], v['calendar_periods'], v['calendar_days'], v['status']] for window, v in r['volumes'].items()])]
        if r['thresholds']:
            for t in r['thresholds']:
                out.append(table(['Window', 'Observed volume', 'Normalized volume', 'Boundary', 'Side', 'Signed distance', 'Disagree'],
                    [[window.title(), r['volumes'][window]['value'], t[window]['value'], t['value'], t[window]['side'], t[window]['distance'], t['disagree']] for window in ('training', 'evaluation')],
                    t['name'] + ' — per ' + cell(t['per_days']) + ' calendar days'))
        out.append('<details><summary>Raw period/state evidence</summary>' + table(['Period', 'State', 'Value', 'Exposure', 'Partial', 'Constituent states'],
            [[p['period'], p['state'], p.get('value'), p.get('exposure'), p.get('partial', False), p.get('constituent_states')] for p in d['periods'][i]['training']], 'Training periods only') + '</details></details>')
    out.append('<h2>Metric join and disagreement</h2><p>Repeated models, windows and horizons are not independent evidence. Metric direction is undeclared; disagreement is not failure. Correlations use pairwise finite observations and average tied ranks.</p>')
    join = d.get('metric_join')
    if join:
        out.append(table(['Measure', 'Value'], [[k.replace('_', ' '), v] for k, v in join.items() if k in {'unmatched_signals_count', 'unmatched_metrics_count', 'horizon_expansion'}], 'Join coverage; unmatched keys retained'))
        for kind in ('unmatched_signals', 'unmatched_metrics'):
            keys = join['key_columns']
            out.append('<details><summary>' + escape(kind.replace('_', ' ')) + '</summary>' + table(keys, [r + [None] * (len(keys) - len(r)) for r in join[kind]]) + '</details>')
    elif d['configuration'].get('metrics'):
        out.append('<p>Metrics are joined to native signals only. No metric join is computed in this generated view, and no metric aggregation rule is inferred.</p>')
    else: out.append('<p>No metrics declared.</p>')
    if not d['configuration'].get('thresholds'): out.append('<p>Volume bands not computed: no volume boundaries declared.</p>')
    if d['disagreement']:
        out.append(table(['Subset', 'Metrics', 'Rows', 'Distinct series', 'Spearman', 'Status'],
            [[r['subset'], r['metric_a'] + ' / ' + r['metric_b'], r['rows'], r['series_count'], r['spearman']['value'], r['spearman']['status']] for r in d['disagreement']], 'Metric disagreement'))
    out.append('<h2>Rules and open questions</h2><details><summary>Exact rules and eligibility definitions</summary>' + table(['Rule', 'Definition'], sorted(d['rules'].items())) + '</details>')
    out.append('<p>What is the row meaning and observation process? Are unavailable measurements unrecorded, or is another mechanism involved? Metric direction remains a human declaration. Current-regime age is not estimable in this slice. Seasonal strength is descriptive adjusted phase variance; short histories are not evidence of absence. Generated mean views have changed units; do their volume boundaries remain meaningful?</p>')
    if d.get('lineage'): out.append('<details><summary>Aggregation lineage</summary>' + table(['Field', 'Value'], sorted(d['lineage'].items())) + '</details>')
    out.append('</body></html>')
    return '\n'.join(out) + '\n'


def markdown(result):
    from .panel import flatten
    d = json.loads(result.to_json());out = ['# Panel signals', '', 'Training-only descriptors. Conditional noise estimates are not fitted forecasts.', '', 'Repeated model/window/horizon rows are not independent; disagreement is not failure.', '']
    for r in d['rows']:
        out += ['## ' + ' / '.join(map(str, r['series'])) + ' / ' + r['model'] + ' / ' + r['window'], '']
        for dim in ('duration', 'amplitude', 'wavelength', 'frequency', 'sbc', 'noise', 'volumes', 'thresholds'):
            out += ['### ' + dim.title(), '', '| Measure | Value |', '| --- | --- |']
            value = r[dim] if isinstance(r[dim], dict) else {'declared': r[dim]}
            out += ['| ' + k.replace('|', '\\|') + ' | ' + cell(v).replace('|', '\\|').replace('\n', ' ') + ' |' for k, v in flatten(value).items()]
            out += ['']
    return '\n'.join(out) + '\n'
