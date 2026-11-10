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
BINARY_RULE = ('A column is binary when its values in the complete cases of the pair, parsed for its effective type, have '
               'exactly two distinct values (0/1 and other two-valued numbers, true/false and two-level categories). '
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
    if len(rx) < 3 or len(set(rx)) < 2 or len(set(ry)) < 2:
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


def kruskal_wallis_status(groups):
    """kruskal_wallis plus a reason for each value that is not estimable."""
    values = [v for g in groups for v in g]
    h, e2 = kruskal_wallis(groups)
    reasons = {}
    if h is None:
        reasons['kruskal_wallis_h'] = 'not estimable: all values tie, so the tie correction is zero'
    if e2 is None:
        reasons['eta_squared_h'] = (reasons['kruskal_wallis_h'] if h is None
                                    else 'not estimable: complete n is not greater than the number of groups')
    return h, e2, reasons


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


def cramers_v_corrected_status(table):
    n = sum(map(sum, table))
    value = cramers_v_corrected(table)
    if value is not None:
        return value, None
    return None, ('not estimable: fewer than two complete cases' if n < 2 else
                  'not estimable: the bias-corrected dimensions leave no comparison (min(corrected rows, corrected columns) - 1 is not positive)')


def two_by_two(a, b, c, d):
    """a=(row2,col2) b=(row2,col1) c=(row1,col2) d=(row1,col1); Haldane-Anscombe +0.5 for the odds ratio only."""
    zero = 0 in (a, b, c, d)
    oa, ob, oc, od = (x + 0.5 for x in (a, b, c, d)) if zero else (a, b, c, d)
    margins = (a + b) * (c + d) * (a + c) * (b + d)
    if not margins:
        # Any empty row or column margin: neither the odds ratio, the risk difference nor phi compares anything.
        reason = 'not estimable: a row or column of the 2x2 table is empty'
        return {'odds_ratio': None, 'odds_ratio_status': reason, 'odds_ratio_correction': 'none',
                'risk_difference': None, 'risk_difference_status': reason, 'phi': None, 'phi_status': reason}
    return {'odds_ratio': oa * od / (ob * oc),
            'odds_ratio_correction': 'Haldane-Anscombe: 0.5 added to every cell because a cell is zero' if zero else 'none',
            'risk_difference': a / (a + b) - c / (c + d), 'phi': (a * d - b * c) / math.sqrt(margins)}


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
            'omitted_nonpositive': 0, 'note': WARNING, 'values_format': 'display'}


def describe(pair, rows, columns):
    index = {c['name']: i for i, c in enumerate(columns)}
    li, ri = index[pair['left']], index[pair['right']]
    lc, rc = columns[li], columns[ri]
    lv = [cell(r[li], lc['effective_type']) for r in rows]
    rv = [cell(r[ri], rc['effective_type']) for r in rows]
    cases = [(x, y) for x, y in zip(lv, rv) if x is not None and y is not None]
    # Roles use complete cases only, so a level seen only where the partner is missing cannot create an empty group.
    left, right = role_of(lc, [x for x, _ in cases]), role_of(rc, [y for _, y in cases])
    kind = pair_type(left, right)
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
            m['spearman_rho_status'] = ('not estimable: fewer than three complete cases' if n < 3
                                        else 'undefined: one side has a single distinct rank')
        gap = coefficient(abs(rho) - abs(r)) if rho is not None and r is not None else None
        m.update(rank_linear_gap=gap, disagreement=bool(gap is not None and (abs(gap) >= GAP or (rho * r < 0 and min(abs(rho), abs(r)) >= NEAR_ZERO))),
                 disagreement_rule=DISAGREEMENT_RULE)
        magnitude = max(abs(v) for v in (r, rho) if v is not None) if n >= 3 and (r, rho) != (None, None) else None
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
            h, e2, reasons = kruskal_wallis_status([vs for _, vs in groups])
            e2 = max(0.0, e2) if e2 is not None else None
            m.update({k + '_status': v for k, v in reasons.items()})
            m.update(eta=eta, kruskal_wallis_h=safe(h), eta_squared_h=coefficient(e2), groups_k=len(groups),
                     eta_squared_h_basis='(H - k + 1)/(n - k), clipped at 0: negative values (below chance expectation) are stored as 0.')
            magnitude = math.sqrt(e2) if e2 is not None else None
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
            m.update({k: (coefficient(v) if k in ('risk_difference', 'phi') else safe(v) if k == 'odds_ratio' and v is not None else v)
                      for k, v in two_by_two(a, b, c, d).items()})
            m.update(index_levels=[left['levels'][1], right['levels'][1]], reference_levels=[left['levels'][0], right['levels'][0]])
            magnitude = abs(m['phi']) if m['phi'] is not None else None
        else:
            v = screening.get('value') if screening.get('measure') == "Cramer's V" else (association('categorical', 'categorical', cases) or {}).get('value')
            vc, reason = cramers_v_corrected_status(table)
            if reason:
                m['cramers_v_bias_corrected_status'] = reason
            m.update(cramers_v=v, cramers_v_bias_corrected=coefficient(vc), rows_k=len(table), columns_k=len(table[0]))
            magnitude = vc
        out['chart'] = heat_chart(pair, out['table'], n, len(rows))
    for key in MEASURE_KEYS:
        if key in m and m[key] is None and key + '_status' not in m:
            m[key + '_status'] = STATUS_FALLBACK.get(key, 'not estimable from these complete cases')
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
    return 'undefined' if value is None else formatted(value)


def message(pair, tp):
    left, right, m, n = pair['left'], pair['right'], tp['measures'], formatted(tp['n'])
    near = tp['wording']['near_zero']
    quiet = ' Magnitude near zero: no notable association under the disclosed wording rule (not a test of independence).'
    if tp['wording']['magnitude'] is None:
        near, quiet = True, ' Headline magnitude not estimable; no direction is stated.'
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
                    f"Kruskal-Wallis H {'undefined' if m['kruskal_wallis_h'] is None else label(m['kruskal_wallis_h'])}; rank eta-squared η²H {f3(m['eta_squared_h'])}.")
            if near:
                text += quiet
            else:
                lo = min(tp['groups'], key=lambda g: (g['median'], label(g['value'])))
                hi = max(tp['groups'], key=lambda g: (g['median'], label(g['value'])))
                text += f" Group medians run from {label(lo['median'])} in {q(lo['value'])} to {label(hi['median'])} in {q(hi['value'])}."
    elif kind == 'binary×binary':
        (l1, r1), (l2, r2) = m['reference_levels'], m['index_levels']
        corrected = '' if m['odds_ratio_correction'] == 'none' else ' (Haldane-Anscombe 0.5 correction: a cell is zero)'
        text = (f"{left} × {right} ({kind}, complete n {n}): odds ratio {'not estimable' if m['odds_ratio'] is None else label(m['odds_ratio'])}{corrected} for {right} {q(r2)} "
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


STATUS_FALLBACK = {'rank_linear_gap': 'not estimable: Spearman rho or Pearson r is undefined',
                   'pearson_r': 'undefined: the screening Pearson r is not available',
                   'eta': 'undefined: the correlation ratio is not available (constant values)',
                   'cramers_v': "undefined: Cramer's V is not available (one level on a side)"}
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
            lines.append(name + ': ' + (m.get(key + '_status', 'not estimable') if value is None else label(value)))
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
               ['Wording', 'near zero (no notable association)' if tp['wording']['near_zero'] else 'headline magnitude ' + f3(tp['wording']['magnitude'])]],
            'numeric': []}]
    if 'groups' in tp:
        out.append({'caption': 'Per-group summary (complete cases)', 'headers': ['Group', 'n', 'Median', 'Q1', 'Q3', 'IQR', 'Mean'],
                    'rows': [[label(g['value'])] + [formatted(g[k]) for k in ('n', 'median', 'q1', 'q3', 'iqr', 'mean')] for g in tp['groups']],
                    'numeric': [1, 2, 3, 4, 5, 6]})
    return out


def notes(pair):
    """Disclosures shown under the measure table (kept out of table cells so narrow screens stay readable).
    Counts are not repeated here: the heat table's chart values carry them."""
    tp = pair['type_pair']
    out = ['Wording rule: ' + tp['wording']['rule']]
    t = tp.get('table')
    if t and (t['other_row_levels'] or t['other_column_levels']):
        out.append('Capped table: ' + t['basis'])
    return out


# ------------------------------------------------------------------ validation

NUMBER_MEASURES = {
    'numeric×numeric': ('pearson_r', 'spearman_rho', 'rank_linear_gap'),
    'category×numeric': ('eta', 'kruskal_wallis_h', 'eta_squared_h'),
    'binary×numeric': ('rank_biserial', 'median_difference', 'mean_difference'),
    'category×category': ('cramers_v', 'cramers_v_bias_corrected'),
    'binary×binary': ('odds_ratio', 'risk_difference', 'phi'),
}
OTHER_MEASURES = {
    'numeric×numeric': {'disagreement': bool, 'disagreement_rule': str},
    'category×numeric': {'groups_k': int, 'eta_squared_h_basis': str},
    'binary×numeric': {},
    'category×category': {'rows_k': int, 'columns_k': int},
    'binary×binary': {'odds_ratio_correction': str, 'index_levels': list, 'reference_levels': list},
}
MEASURE_KEYS = sorted({k for keys in NUMBER_MEASURES.values() for k in keys})
CHART_KINDS = {'numeric×numeric': {'target_chart'}, 'category×numeric': {'target_chart', 'group_box'},
               'binary×numeric': {'target_chart', 'group_box'}, 'category×category': {'heat_table'}, 'binary×binary': {'heat_table'}}


def _fail(what):
    raise ValueError('invalid type pair ' + what)


def _check_chart(chart, kind):
    def text(*keys): return all(isinstance(chart.get(k), str) for k in keys)
    def count(v): return type(v) is int and v >= 0
    def num(v): return type(v) in (int, float) and math.isfinite(v)
    if not isinstance(chart, dict) or chart.get('kind') not in CHART_KINDS[kind]:
        _fail('chart kind')
    if chart['kind'] == 'target_chart':
        if not text('title', 'note'):
            _fail('target chart reference')
        return
    if not text('title', 'x_label', 'y_label', 'note') or not count(chart.get('n')) or not count(chart.get('total_rows')) or chart['n'] > chart['total_rows']:
        _fail('chart fields')
    if chart['kind'] == 'group_box':
        data = chart.get('data')
        if chart.get('x_scale') not in {'linear', 'log10'} or not isinstance(data, list) or not 1 <= len(data) <= 20:
            _fail('grouped box')
        for row in data:
            box = row.get('box') if isinstance(row, dict) else None
            if (not isinstance(row, dict) or not isinstance(row.get('label'), str) or not count(row.get('n')) or not count(row.get('excluded_nonpositive'))
                    or not isinstance(box, dict) or any(not num(box.get(k)) for k in ('min', 'q1', 'median', 'q3', 'max'))
                    or [box[k] for k in ('min', 'q1', 'median', 'q3', 'max')] != sorted(box[k] for k in ('min', 'q1', 'median', 'q3', 'max'))):
                _fail('grouped box row')
        return
    rows, cols, counts = chart.get('row_labels'), chart.get('column_labels'), chart.get('counts')
    if (not isinstance(rows, list) or not isinstance(cols, list) or not all(isinstance(v, str) for v in rows + cols)
            or not 1 <= len(rows) <= CAP + 1 or not 1 <= len(cols) <= CAP + 1 or not isinstance(counts, list) or len(counts) != len(rows)
            or any(not isinstance(r, list) or len(r) != len(cols) or not all(count(v) for v in r) for r in counts)):
        _fail('heat table')



def validate_type_pair(tp):
    """Full per-kind shape, so a saved artifact that validates can always be rendered."""
    def count(v): return type(v) is int and v >= 0
    def num(v): return type(v) in (int, float) and math.isfinite(v)
    def level(v): return type(v) in (int, float, str)
    if not isinstance(tp, dict) or tp.get('pair_type') not in PAIR_TYPES or not count(tp.get('n')):
        _fail('kind or n')
    kind = tp['pair_type']
    if any(not isinstance(tp.get(k), str) for k in ('binary_rule', 'basis')):
        _fail('disclosures')
    roles = tp.get('roles')
    if (not isinstance(roles, list) or len(roles) != 2
            or any(not isinstance(r, dict) or r.get('role') not in {'numeric', 'category', 'binary'} or not isinstance(r.get('column'), str) for r in roles)
            or any((r['role'] == 'binary') != ('levels' in r) for r in roles)
            or any(r['role'] == 'binary' and (not isinstance(r['levels'], list) or len(r['levels']) != 2 or not all(level(v) for v in r['levels'])) for r in roles)):
        _fail('roles')
    if pair_type(*roles) != kind:
        _fail('kind does not match roles')
    m = tp.get('measures')
    if not isinstance(m, dict):
        _fail('measures')
    for key in NUMBER_MEASURES[kind]:
        if key not in m or not (m[key] is None or num(m[key])):
            _fail('measure ' + key)
        if m[key] is None and not isinstance(m.get(key + '_status'), str):
            _fail('measure ' + key + ' is null without a status reason')
    for key, typ in OTHER_MEASURES[kind].items():
        if type(m.get(key)) is not typ:
            _fail('measure ' + key)
    if kind == 'binary×numeric' and (not level(m.get('index_level')) or not level(m.get('reference_level'))):
        _fail('binary levels')
    w = tp.get('wording')
    if (not isinstance(w, dict) or type(w.get('near_zero')) is not bool or not isinstance(w.get('rule'), str)
            or not (w.get('magnitude') is None or num(w['magnitude']))):
        _fail('wording')
    grouped = kind in ('category×numeric', 'binary×numeric')
    if grouped != ('groups' in tp):
        _fail('groups presence')
    if grouped and (not isinstance(tp['groups'], list) or not 1 <= len(tp['groups']) <= 20
                    or any(not isinstance(g, dict) or not level(g.get('value')) or not count(g.get('n'))
                           or any(not num(g.get(k)) for k in ('median', 'q1', 'q3', 'iqr', 'mean')) for g in tp['groups'])):
        _fail('groups')
    tabled = kind in ('category×category', 'binary×binary')
    if tabled != ('table' in tp):
        _fail('table presence')
    if tabled:
        t = tp['table']
        if (not isinstance(t, dict) or any(not isinstance(t.get(k), str) for k in ('row_column', 'column_column', 'basis'))
                or any(not isinstance(t.get(k), list) or not 1 <= len(t[k]) <= CAP or not all(level(v) for v in t[k]) for k in ('row_levels', 'column_levels'))
                or any(not count(t.get(k)) for k in ('other_row_levels', 'other_column_levels', 'shown_cap')) or not isinstance(t.get('counts'), list)):
            _fail('table')
        width = len(t['column_levels']) + bool(t['other_column_levels'])
        if len(t['counts']) != len(t['row_levels']) + bool(t['other_row_levels']) or any(not isinstance(r, list) or len(r) != width or not all(count(v) for v in r) for r in t['counts']):
            _fail('table counts')
    if 'chart' not in tp:
        _fail('chart missing')
    _check_chart(tp['chart'], kind)
