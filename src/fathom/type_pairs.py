"""Type-suited descriptive measures for relationships the existing ranking already selected (spec027).

Standard library only. Nothing here selects, ranks or gates a pair: the screening measure in target.py
and the budget in profiler.rank_pairs decide which pairs exist. This module classifies each selected pair
into one of the five type pairs in docs/vision.md and describes it. No p-values.
"""

from collections import Counter, defaultdict
import math
import statistics

from .presentation import formatted
from .target import CATEGORY, NUMERIC, WARNING, association, cell, geometry_percentile
from .univariate import coefficient, percentile, safe

PAIR_TYPES = ('numeric×numeric', 'category×numeric', 'binary×numeric', 'category×category', 'binary×binary')
CAP = 10
NEAR_ZERO = 0.1
GAP = 0.2
BINARY_RULE = ('A column is binary when its non-missing values, parsed for its effective type, have exactly two distinct '
               'values in the whole column (0/1 and other two-valued numbers, true/false and two-level categories). '
               'Levels are in sort order (numeric order for numbers); the second is the index level. Level order carries '
               'no domain meaning. A binary column paired with a category of three or more levels is read as category×category.')
WORDING_RULE = ('Wording only, not a test or strength band: a headline magnitude below 0.1 is worded "near zero (no notable '
                'association)". Headline: max(|Pearson r|, |Spearman rho|); square root of rank eta-squared; |rank-biserial|; '
                "bias-corrected Cramer's V; |phi|. Independent columns can exceed 0.1 in small samples; no action is selected from it.")
DISAGREEMENT_RULE = ('Rank and linear measures disagree when |Spearman rho| and |Pearson r| differ by at least 0.2, or have '
                     'opposite signs while both are at least 0.1 in absolute value (wording cut, not a test).')
BASIS = ('Descriptive complete-case summaries of one snapshot; not causal; no p-values. Selection and ranking are unchanged: '
         'these measures describe pairs the screening measure already selected.')


# ------------------------------------------------------------------ formulas

def average_ranks(values):
    """1-based ranks; tied values share the average of the positions they occupy."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def spearman(xs, ys):
    """Spearman rho: Pearson correlation of average tied ranks; None when either side has one rank."""
    rx, ry = average_ranks(list(xs)), average_ranks(list(ys))
    if len(rx) < 2 or len(set(rx)) < 2 or len(set(ry)) < 2:
        return None
    return statistics.correlation(rx, ry)


def rank_biserial(first, second):
    """Glass rank-biserial r = 2(mean rank of second - mean rank of first)/n = P(second>first) - P(second<first)."""
    ranks = average_ranks(list(first) + list(second))
    n1, n = len(first), len(first) + len(second)
    return 2 * (math.fsum(ranks[n1:]) / (n - n1) - math.fsum(ranks[:n1]) / n1) / n


def kruskal_wallis(groups):
    """Tie-corrected Kruskal-Wallis H and rank eta-squared (H - k + 1)/(n - k); descriptive only."""
    values = [v for g in groups for v in g]
    n, k = len(values), len(groups)
    ranks = average_ranks(values)
    sums, start = [], 0
    for g in groups:
        sums.append(math.fsum(ranks[start:start + len(g)]))
        start += len(g)
    ties = math.fsum(t ** 3 - t for t in Counter(values).values())
    correction = 1 - ties / (n ** 3 - n) if n > 1 else 0
    if correction <= 0:
        return None, None
    h = (12 / (n * (n + 1)) * math.fsum(s * s / len(g) for s, g in zip(sums, groups)) - 3 * (n + 1)) / correction
    h = max(0.0, h)
    return h, ((h - k + 1) / (n - k) if n > k else None)


def chi_square(table):
    n = sum(map(sum, table))
    rows = [sum(r) for r in table]
    cols = [sum(c) for c in zip(*table)]
    return n, math.fsum((table[i][j] - rows[i] * cols[j] / n) ** 2 / (rows[i] * cols[j] / n)
                        for i in range(len(rows)) for j in range(len(cols)) if rows[i] and cols[j])


def cramers_v_corrected(table):
    """Bergsma (2013) bias-corrected Cramer's V; None when the corrected dimensions leave nothing to compare."""
    r, c = len(table), len(table[0])
    n, chi = chi_square(table)
    if n < 2:
        return None
    phi2 = max(0.0, chi / n - (r - 1) * (c - 1) / (n - 1))
    rt, ct = r - (r - 1) ** 2 / (n - 1), c - (c - 1) ** 2 / (n - 1)
    denominator = min(rt - 1, ct - 1)
    return min(1.0, math.sqrt(phi2 / denominator)) if denominator > 0 else None


def two_by_two(a, b, c, d):
    """a=(row2,col2) b=(row2,col1) c=(row1,col2) d=(row1,col1); Haldane-Anscombe +0.5 for the odds ratio only."""
    zero = 0 in (a, b, c, d)
    oa, ob, oc, od = (x + 0.5 for x in (a, b, c, d)) if zero else (a, b, c, d)
    margins = (a + b) * (c + d) * (a + c) * (b + d)
    return {'odds_ratio': oa * od / (ob * oc),
            'odds_ratio_correction': 'Haldane-Anscombe: 0.5 added to every cell because a cell is zero' if zero else 'none',
            'risk_difference': a / (a + b) - c / (c + d) if a + b and c + d else None,
            'phi': (a * d - b * c) / math.sqrt(margins) if margins else None}


# ------------------------------------------------------------------ classification and enrichment

def plain(value):
    return int(value) if isinstance(value, float) and value.is_integer() and abs(value) < 2 ** 53 else value


def label(value):
    return formatted(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else str(value)


def role_of(column, values):
    levels = sorted(set(values))
    if len(levels) == 2:
        return {'column': column['name'], 'role': 'binary', 'levels': [plain(v) for v in levels]}
    return {'column': column['name'], 'role': 'numeric' if column['effective_type'] in NUMERIC else 'category'}


def pair_type(left, right):
    roles = {left['role'], right['role']}
    if roles == {'numeric'}:
        return 'numeric×numeric'
    if roles == {'binary'}:
        return 'binary×binary'
    if 'numeric' in roles:
        return 'binary×numeric' if 'binary' in roles else 'category×numeric'
    return 'category×category'


def group_rows(groups):
    out = []
    for level, values in groups:
        q1, q3 = percentile(values, 25, lambda x: x), percentile(values, 75, lambda x: x)
        out.append({'value': plain(level), 'n': len(values), 'median': percentile(values, 50), 'q1': safe(q1), 'q3': safe(q3),
                    'iqr': safe(q3 - q1), 'mean': safe(statistics.mean(values))})
    return out


def capped_table(cases, row_column, column_column):
    rows, cols = Counter(x for x, _ in cases), Counter(y for _, y in cases)

    def shown(counter):
        top = sorted(counter, key=lambda v: (-counter[v], v))[:CAP]
        return sorted(top)
    rl, cl = shown(rows), shown(cols)
    ri, ci = {v: i for i, v in enumerate(rl)}, {v: i for i, v in enumerate(cl)}
    other_r, other_c = len(rows) - len(rl), len(cols) - len(cl)
    counts = [[0] * (len(cl) + bool(other_c)) for _ in range(len(rl) + bool(other_r))]
    for x, y in cases:
        counts[ri.get(x, len(rl))][ci.get(y, len(cl))] += 1
    return {'row_column': row_column, 'column_column': column_column, 'row_levels': [plain(v) for v in rl],
            'column_levels': [plain(v) for v in cl], 'counts': counts, 'other_row_levels': other_r,
            'other_column_levels': other_c, 'shown_cap': CAP,
            'basis': 'Rows are the left column, columns the right column. At most 10 levels per side are shown (most frequent, '
                     'then sort order), remaining levels are summed in a final "other levels" row/column. Measures use the full table.'}


def full_table(cases, rl=None, cl=None):
    rl, cl = rl or sorted({x for x, _ in cases}), cl or sorted({y for _, y in cases})
    counts = Counter(cases)
    return [[counts[x, y] for y in cl] for x in rl]


def heat_chart(pair, table, n, total_rows):
    rows = [label(v) for v in table['row_levels']] + ([f"other {table['other_row_levels']} levels"] if table['other_row_levels'] else [])
    cols = [label(v) for v in table['column_levels']] + ([f"other {table['other_column_levels']} levels"] if table['other_column_levels'] else [])
    return {'kind': 'heat_table', 'title': 'Type pair: ' + pair['left'] + ' × ' + pair['right'], 'x_label': pair['right'],
            'y_label': pair['left'], 'row_labels': rows, 'column_labels': cols, 'counts': table['counts'], 'n': n,
            'total_rows': total_rows, 'note': 'Counts of complete cases; the bar in each cell is that cell’s share of its row. Descriptive, not causal.'}


def box_chart(pair, groups, n, total_rows, group_name, value_name):
    data = [{'label': label(level), 'n': len(values), 'excluded_nonpositive': 0,
             'box': {k: geometry_percentile(values, p) for k, p in [('min', 0), ('q1', 25), ('median', 50), ('q3', 75), ('max', 100)]}}
            for level, values in groups]
    return {'kind': 'group_box', 'title': 'Type pair: ' + value_name + ' by ' + group_name, 'x_label': value_name,
            'y_label': group_name, 'x_scale': 'linear', 'data': data, 'n': n, 'total_rows': total_rows, 'plotted': n,
            'omitted_nonpositive': 0, 'note': WARNING}


def describe(pair, rows, columns):
    index = {c['name']: i for i, c in enumerate(columns)}
    li, ri = index[pair['left']], index[pair['right']]
    lc, rc = columns[li], columns[ri]
    lv = [cell(r[li], lc['effective_type']) for r in rows]
    rv = [cell(r[ri], rc['effective_type']) for r in rows]
    left, right = role_of(lc, [v for v in lv if v is not None]), role_of(rc, [v for v in rv if v is not None])
    kind = pair_type(left, right)
    cases = [(x, y) for x, y in zip(lv, rv) if x is not None and y is not None]
    n = len(cases)
    out = {'pair_type': kind, 'roles': [left, right], 'binary_rule': BINARY_RULE, 'n': n, 'basis': BASIS, 'measures': {}}
    screening = pair.get('association', {})
    m = out['measures']
    if kind == 'numeric×numeric':
        r = pair['statistics'].get('pearson_r', screening.get('value'))
        rho = spearman([x for x, _ in cases], [y for _, y in cases])
        rho = coefficient(rho) if rho is not None else None
        m.update(pearson_r=r, spearman_rho=rho)
        if rho is None:
            m['spearman_rho_status'] = 'undefined: one side has a single distinct rank'
        gap = coefficient(abs(rho) - abs(r)) if rho is not None and r is not None else None
        m.update(rank_linear_gap=gap, disagreement=bool(gap is not None and (abs(gap) >= GAP or (rho * r < 0 and min(abs(rho), abs(r)) >= NEAR_ZERO))),
                 disagreement_rule=DISAGREEMENT_RULE)
        magnitude = max(abs(v) for v in (r, rho) if v is not None) if (r, rho) != (None, None) else None
        out['chart'] = {'kind': 'target_chart', 'title': 'Target: ' + pair['left'] + ' × ' + pair['right'],
                        'note': 'Scatter: the existing target chart for this pair (up to 200 evenly spaced points).'}
    elif kind in ('category×numeric', 'binary×numeric'):
        gside = 0 if left['role'] != 'numeric' else 1
        gcol, vcol = (lc, rc) if gside == 0 else (rc, lc)
        grouped = defaultdict(list)
        for x, y in cases:
            g, v = (x, y) if gside == 0 else (y, x)
            grouped[g].append(v)
        groups = sorted(grouped.items())
        out['groups'] = group_rows(groups)
        if kind == 'category×numeric':
            eta = screening.get('value') if screening.get('measure') == 'Correlation ratio eta' else (association('categorical', 'numeric', [(g, v) for g, vs in groups for v in vs]) or {}).get('value')
            h, e2 = kruskal_wallis([vs for _, vs in groups])
            m.update(eta=eta, kruskal_wallis_h=safe(h), eta_squared_h=coefficient(e2), groups_k=len(groups))
            magnitude = math.sqrt(max(0.0, e2)) if e2 is not None else None
        else:
            (ref, first), (idx, second) = groups
            rb = rank_biserial(first, second)
            m.update(rank_biserial=coefficient(rb), index_level=plain(idx), reference_level=plain(ref),
                     median_difference=safe(percentile(second, 50, lambda x: x) - percentile(first, 50, lambda x: x)),
                     mean_difference=safe(statistics.mean(second) - statistics.mean(first)))
            magnitude = abs(rb)
        # The existing target chart is already a grouped box when the numeric column is the target.
        if gside == 0 and rc['effective_type'] in NUMERIC and lc['effective_type'] in CATEGORY:
            out['chart'] = {'kind': 'target_chart', 'title': 'Target: ' + pair['left'] + ' × ' + pair['right'],
                            'note': 'Grouped box: the existing target chart for this pair.'}
        else:
            out['chart'] = box_chart(pair, groups, n, len(rows), gcol['name'], vcol['name'])
    else:
        table = full_table(cases, left.get('levels') if kind == 'binary×binary' else None, right.get('levels') if kind == 'binary×binary' else None)
        out['table'] = capped_table(cases, pair['left'], pair['right'])
        if kind == 'binary×binary':
            (d, c), (b, a) = table
            m.update({k: (coefficient(v) if k in ('risk_difference', 'phi') else safe(v) if k == 'odds_ratio' else v)
                      for k, v in two_by_two(a, b, c, d).items()})
            m.update(index_levels=[left['levels'][1], right['levels'][1]], reference_levels=[left['levels'][0], right['levels'][0]])
            magnitude = abs(m['phi']) if m['phi'] is not None else None
        else:
            v = screening.get('value') if screening.get('measure') == "Cramer's V" else (association('categorical', 'categorical', cases) or {}).get('value')
            vc = cramers_v_corrected(table)
            m.update(cramers_v=v, cramers_v_bias_corrected=coefficient(vc), rows_k=len(table), columns_k=len(table[0]))
            magnitude = vc
        out['chart'] = heat_chart(pair, out['table'], n, len(rows))
    out['wording'] = {'magnitude': coefficient(magnitude) if magnitude is not None else None,
                      'near_zero': bool(magnitude is not None and magnitude < NEAR_ZERO), 'rule': WORDING_RULE}
    return out


def enrich_pairs(rows, columns, pairs):
    """Add `type_pair` to each selected relationship; missingness-by-group pairs are quality contrasts, not type pairs."""
    for pair in pairs:
        if pair['method'] != 'missingness_by_group' and 'association' in pair:
            pair['type_pair'] = describe(pair, rows, columns)


# ------------------------------------------------------------------ wording

def q(value):
    return "'" + label(value) + "'"


def f3(value):
    return 'undefined' if value is None else format(value, '.3f')


def message(pair, tp):
    left, right, m, n = pair['left'], pair['right'], tp['measures'], formatted(tp['n'])
    near = tp['wording']['near_zero']
    quiet = ' Magnitude near zero: no notable association under the disclosed wording rule (not a test of independence).'
    kind = tp['pair_type']
    if kind == 'numeric×numeric':
        text = f"{left} × {right} ({kind}, complete n {n}): Pearson r {f3(m['pearson_r'])}; Spearman rho {f3(m['spearman_rho'])}."
        if near:
            text += quiet
        elif m['spearman_rho'] is not None:
            text += f" Higher {left} tends to go with {'higher' if m['spearman_rho'] > 0 else 'lower'} {right} (rank order)."
        if m['disagreement']:
            text += ' Rank and linear measures disagree: a monotone but non-linear pattern, or a few influential values.'
    elif kind in ('category×numeric', 'binary×numeric'):
        groups = {g['value']: g for g in tp['groups']}
        gname, vname = (left, right) if tp['roles'][0]['role'] != 'numeric' else (right, left)
        if kind == 'binary×numeric':
            idx, ref = groups[m['index_level']], groups[m['reference_level']]
            text = (f"{vname} by {gname} ({kind}, complete n {n}): {gname} {q(idx['value'])} n {idx['n']}, median {label(idx['median'])}; "
                    f"{gname} {q(ref['value'])} n {ref['n']}, median {label(ref['median'])}; difference in medians {label(m['median_difference'])}; "
                    f"difference in means {label(m['mean_difference'])}; rank-biserial {f3(m['rank_biserial'])}.")
            if near:
                text += quiet
            else:
                text += f" Values of {vname} tend to be {'higher' if m['rank_biserial'] > 0 else 'lower'} when {gname} is {q(idx['value'])}."
        else:
            text = (f"{vname} across {m['groups_k']} groups of {gname} ({kind}, complete n {n}): eta {f3(m['eta'])}; "
                    f"Kruskal-Wallis H {label(m['kruskal_wallis_h'])}; rank eta-squared η²H {f3(m['eta_squared_h'])}.")
            if near:
                text += quiet
            else:
                lo = min(tp['groups'], key=lambda g: (g['median'], label(g['value'])))
                hi = max(tp['groups'], key=lambda g: (g['median'], label(g['value'])))
                text += f" Group medians run from {label(lo['median'])} in {q(lo['value'])} to {label(hi['median'])} in {q(hi['value'])}."
    elif kind == 'binary×binary':
        (l1, r1), (l2, r2) = m['reference_levels'], m['index_levels']
        corrected = '' if m['odds_ratio_correction'] == 'none' else ' (Haldane-Anscombe 0.5 correction: a cell is zero)'
        text = (f"{left} × {right} ({kind}, complete n {n}): odds ratio {label(m['odds_ratio'])}{corrected} for {right} {q(r2)} "
                f"with {left} {q(l2)} against {q(l1)}; risk difference {f3(m['risk_difference'])} (share of {right} {q(r2)} among "
                f"{left} {q(l2)} minus among {q(l1)}); phi {f3(m['phi'])}.")
        if near:
            text += quiet
        elif m['risk_difference'] is not None:
            text += f" {right} {q(r2)} is {'more' if m['risk_difference'] > 0 else 'less'} common when {left} is {q(l2)}."
    else:
        text = (f"{left} × {right} ({kind}, complete n {n}, {m['rows_k']} by {m['columns_k']} levels): Cramer's V {f3(m['cramers_v'])}; "
                f"bias-corrected V {f3(m['cramers_v_bias_corrected'])}.")
        text += quiet if near else f" Shares of {right} levels differ across {left} levels; see the table."
    return text + ' Descriptive, not causal.'


MEASURE_LABELS = [('pearson_r', 'Pearson r'), ('spearman_rho', 'Spearman rho'), ('rank_linear_gap', '|rho| minus |r|'),
                  ('eta', 'eta (correlation ratio)'), ('kruskal_wallis_h', 'Kruskal-Wallis H (descriptive)'),
                  ('eta_squared_h', 'rank eta-squared η²H'), ('groups_k', 'groups'), ('rank_biserial', 'rank-biserial r'),
                  ('median_difference', 'difference in medians (index minus reference)'),
                  ('mean_difference', 'difference in means (index minus reference)'), ('cramers_v', "Cramer's V"),
                  ('cramers_v_bias_corrected', "bias-corrected Cramer's V"), ('rows_k', 'row levels'), ('columns_k', 'column levels'),
                  ('odds_ratio', 'odds ratio'), ('risk_difference', 'risk difference'), ('phi', 'phi')]


def measure_lines(tp):
    m, lines = tp['measures'], []
    for key, name in MEASURE_LABELS:
        if key in m:
            value = m[key]
            lines.append(name + ': ' + ('undefined' if value is None else label(value) if isinstance(value, int) or key in ('kruskal_wallis_h', 'odds_ratio', 'median_difference', 'mean_difference') else format(value, '.3f')))
    if 'index_level' in m:
        lines.append('index level: ' + q(m['index_level']) + '; reference level: ' + q(m['reference_level']))
    if 'index_levels' in m:
        lines.append('index levels: ' + ', '.join(q(v) for v in m['index_levels']) + '; reference levels: ' + ', '.join(q(v) for v in m['reference_levels']))
    if m.get('odds_ratio_correction', 'none') != 'none':
        lines.append('odds ratio correction: ' + m['odds_ratio_correction'])
    if m.get('disagreement'):
        lines.append('rank and linear measures disagree')
    return lines


def tree(f, tp):
    names = f.get('columns', [])
    children = measure_lines(tp) + ['group ' + q(g['value']) + ': n ' + formatted(g['n']) + ', median ' + label(g['median'])
                                    for g in tp.get('groups', [])] + ['complete cases: ' + formatted(tp['n'])]
    children.append('magnitude near zero: no notable association (wording rule)' if tp['wording']['near_zero'] else 'headline magnitude: ' + f3(tp['wording']['magnitude']))
    children.append('descriptive, not causal')
    return {'text': tp['pair_type'] + ': ' + ' × '.join(names), 'children': children}


def tables(pair):
    """Report tables for one selected pair's type-pair block."""
    tp = pair['type_pair']
    out = [{'caption': 'Type pair: ' + tp['pair_type'] + ' — descriptive, complete n ' + formatted(tp['n']),
            'headers': ['Measure', 'Value'], 'rows': [line.split(': ', 1) for line in measure_lines(tp) if ': ' in line]
            + [['Roles', '; '.join(r['column'] + ': ' + r['role'] + (' (' + ', '.join(label(v) for v in r['levels']) + ')' if 'levels' in r else '') for r in tp['roles'])],
               ['Wording', ('near zero (no notable association)' if tp['wording']['near_zero'] else 'headline magnitude ' + f3(tp['wording']['magnitude'])) + '. ' + tp['wording']['rule']]],
            'numeric': []}]
    if 'groups' in tp:
        out.append({'caption': 'Per-group summary (complete cases)', 'headers': ['Group', 'n', 'Median', 'Q1', 'Q3', 'IQR', 'Mean'],
                    'rows': [[label(g['value'])] + [formatted(g[k]) for k in ('n', 'median', 'q1', 'q3', 'iqr', 'mean')] for g in tp['groups']],
                    'numeric': [1, 2, 3, 4, 5, 6]})
    if 'table' in tp:
        t = tp['table']
        cols = [label(v) for v in t['column_levels']] + ([f"other {t['other_column_levels']} levels"] if t['other_column_levels'] else [])
        rows = [label(v) for v in t['row_levels']] + ([f"other {t['other_row_levels']} levels"] if t['other_row_levels'] else [])
        out.append({'caption': 'Counts: ' + t['row_column'] + ' (rows) by ' + t['column_column'] + ' (columns). ' + t['basis'],
                    'headers': [t['row_column']] + cols, 'rows': [[r] + [formatted(v) for v in counts] for r, counts in zip(rows, t['counts'])],
                    'numeric': list(range(1, len(cols) + 1))})
    return out


# ------------------------------------------------------------------ validation

def validate_type_pair(tp):
    def count(v): return type(v) is int and v >= 0
    def scalar(v): return v is None or type(v) in (int, float, str, bool)
    if (not isinstance(tp, dict) or tp.get('pair_type') not in PAIR_TYPES or not count(tp.get('n'))
            or not isinstance(tp.get('measures'), dict) or any(not scalar(v) and not isinstance(v, list) for v in tp['measures'].values())):
        raise ValueError('invalid type pair')
    roles = tp.get('roles')
    if (not isinstance(roles, list) or len(roles) != 2
            or any(not isinstance(r, dict) or r.get('role') not in {'numeric', 'category', 'binary'} or not isinstance(r.get('column'), str) for r in roles)):
        raise ValueError('invalid type pair roles')
    w = tp.get('wording')
    if not isinstance(w, dict) or type(w.get('near_zero')) is not bool or not isinstance(w.get('rule'), str):
        raise ValueError('invalid type pair wording')
    if 'groups' in tp and (not isinstance(tp['groups'], list) or len(tp['groups']) > 20
                           or any(not isinstance(g, dict) or not count(g.get('n')) for g in tp['groups'])):
        raise ValueError('invalid type pair groups')
    if 'table' in tp:
        t = tp['table']
        if not isinstance(t, dict) or not isinstance(t.get('counts'), list) or any(not isinstance(t.get(k), list) or len(t[k]) > CAP for k in ('row_levels', 'column_levels')):
            raise ValueError('invalid type pair table')
        width = len(t['column_levels']) + bool(t.get('other_column_levels'))
        if len(t['counts']) != len(t['row_levels']) + bool(t.get('other_row_levels')) or any(not isinstance(r, list) or len(r) != width or not all(count(v) for v in r) for r in t['counts']):
            raise ValueError('invalid type pair table counts')
    chart = tp.get('chart')
    if chart is not None and (not isinstance(chart, dict) or chart.get('kind') not in {'target_chart', 'group_box', 'heat_table'}):
        raise ValueError('invalid type pair chart')
