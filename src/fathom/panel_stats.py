"""Pure, training-only descriptors; no forecasting, imputation or domain inference."""
from collections import defaultdict
from datetime import date, timedelta
import math
import statistics as st


def estimate(value=None, status='computed', reason='', **context):
    if isinstance(value, float) and not math.isfinite(value):
        value, status, reason = None, 'not estimable', 'finite numerical range exceeded'
    return {'value': value, 'status': status, 'reason': reason, **context}


def ratio(a, b, reason='zero denominator'):
    return estimate(a / b) if b else estimate(status='undefined', reason=reason)


def usable(p):
    return (p['state'] == 'observed' and p.get('value') is not None
            and p.get('exposure') is not None and p['exposure'] > 0 and not p.get('partial', False))


def floor(d, grain):
    if grain == 'day': return d
    if grain == 'week': return d - timedelta(days=d.weekday())
    return d.replace(day=1)


def advance(d, grain):
    if grain == 'day': return d + timedelta(days=1)
    if grain == 'week': return d + timedelta(days=7)
    return date(d.year + (d.month == 12), d.month % 12 + 1, 1)


def calendar(first, last, grain):
    out = [];d = floor(first, grain)
    while d <= last:
        if len(out) >= 20000: raise ValueError('panel calendar exceeds 20000 periods')
        out.append(d);d = advance(d, grain)
    return out


def poisson_mae(mu):
    """Oracle integer-median MAE: normalized mode-centered Poisson mass summation."""
    if mu == 0: return estimate(0.0, median=0, model='Poisson', relative_mass_cutoff=1e-16)
    if not math.isfinite(mu) or mu < 0 or mu > 100000:
        return estimate(status='not estimable', reason='Poisson mean outside numerical cap 0..100000')
    mode = int(mu);mass = {mode: 1.0};p = 1.0
    # Relative masses avoid exp(-mu) underflow. Stop only after the decreasing tail.
    for k in range(mode, 0, -1):
        p *= k / mu;mass[k - 1] = p
        if p < 1e-16 and k < mode: break
    p = 1.0;k = mode
    while True:
        k += 1;p *= mu / k;mass[k] = p
        if p < 1e-16: break
        if k - mode > 100000: return estimate(status='not estimable', reason='Poisson summation cap')
    total = math.fsum(mass.values());cdf = 0.0;median = mode
    for k in sorted(mass):
        cdf += mass[k] / total
        if cdf >= .5:
            median = k;break
    return estimate(math.fsum(abs(k - median) * p for k, p in mass.items()) / total,
                    median=median, model='Poisson', relative_mass_cutoff=1e-16,
                    note='normalized truncated-mass approximation; no asserted error bound or parameter uncertainty')


def seasonal(periods, grain, cycle):
    groups = defaultdict(list)
    covered = 0
    if periods:
        first = date.fromisoformat(periods[0].get('covered_start', periods[0]['period']))
        last = date.fromisoformat(periods[-1]['covered_end']) if 'covered_end' in periods[-1] else advance(date.fromisoformat(periods[-1]['period']), grain) - timedelta(days=1)
        start = floor(first, cycle) if cycle != 'year' else first.replace(month=1, day=1)
        while start <= last:
            end = advance(start, cycle) if cycle != 'year' else date(start.year + 1, 1, 1)
            if start >= first and end - timedelta(days=1) <= last: covered += 1
            start = end
    if cycle == 'week' and grain != 'day' or cycle == 'month' and grain != 'day':
        return {'calendar_cycles_covered': covered, 'complete_cycles': 0, 'strength': estimate(status='not estimable', reason='native grain cannot resolve this cycle')}
    for p in periods:
        d = date.fromisoformat(p['period'])
        key = d.isocalendar()[:2] if cycle == 'week' else (d.year, d.month) if cycle == 'month' else (d.isocalendar().year if grain == 'week' else d.year)
        groups[key].append(p)
    complete = []
    for key, ps in sorted(groups.items()):
        if cycle == 'week': start = date.fromisocalendar(key[0], key[1], 1);end = start + timedelta(days=6)
        elif cycle == 'month': start = date(key[0], key[1], 1);end = advance(start, 'month') - timedelta(days=1)
        elif grain == 'week': start = date.fromisocalendar(key, 1, 1);end = date.fromisocalendar(key + 1, 1, 1) - timedelta(days=1)
        else: start = date(key, 1, 1);end = date(key, 12, 31)
        expected = [d.isoformat() for d in calendar(start, end, grain)]
        if [p['period'] for p in ps] == expected and all(usable(p) for p in ps): complete.append(ps)
    ncycles = len(complete)
    if ncycles < 3:
        return {'calendar_cycles_covered': covered, 'complete_cycles': ncycles, 'strength': estimate(status='not estimable', reason='fewer than three complete eligible calendar cycles')}
    phase = defaultdict(list)
    for ps in complete:
        for p in ps:
            d = date.fromisoformat(p['period'])
            key = d.weekday() if cycle == 'week' else d.day if cycle == 'month' else d.month if grain == 'month' else d.isocalendar().week if grain == 'week' else (d.month, d.day)
            phase[key].append(p['value'])
    supported = [vs for vs in phase.values() if len(vs) >= 2]
    values = [v for vs in supported for v in vs];n, k = len(values), len(supported)
    total = math.fsum((v - st.fmean(values)) ** 2 for v in values)
    if not total: strength = estimate(status='undefined', reason='zero variance')
    elif n <= k + 1: strength = estimate(status='not estimable', reason='insufficient residual degrees of freedom')
    else:
        within = math.fsum((v - st.fmean(vs)) ** 2 for vs in supported for v in vs)
        strength = estimate(max(0.0, min(1.0, 1 - within / total * (n - 1) / (n - k))),
                            phases=k, observations=n, omitted_singleton_phases=len(phase) - k,
                            note='adjusted in-sample phase explained variance; descriptive, not a significance test')
    return {'calendar_cycles_covered': covered, 'complete_cycles': ncycles, 'strength': strength}


def summarize(periods, grain):
    measured = [p for p in periods if usable(p)];x = [p['value'] for p in measured]
    positive = [v for v in x if v > 0];n = len(x);exposures = [p['exposure'] for p in measured]
    unequal = bool(exposures and any(not math.isclose(e, exposures[0], rel_tol=1e-12) for e in exposures))
    mean = st.fmean(x) if x else 0;posmean = st.fmean(positive) if positive else 0
    cv2 = ratio(st.pvariance([v / posmean for v in positive]) if positive else 0, 1 if positive else 0, 'no positive values')
    amp = {'mean': estimate(mean) if n else estimate(status='undefined', reason='no usable observations'),
           'zero_share': ratio(n - len(positive), n), 'positive_mean': estimate(posmean) if positive else estimate(status='undefined', reason='no positive values'),
           'positive_cv2': cv2, 'dispersion_to_mean': ratio(st.variance(x), mean) if n >= 2 else estimate(status='undefined', reason='fewer than two usable observations'),
           'mean_per_exposure': ratio(math.fsum(x), math.fsum(exposures))}
    def quantile(q):
        ordered = sorted(x);h = (len(ordered) - 1) * q;a = int(h);b = min(a + 1, len(ordered) - 1)
        return ordered[a] * (1 - h + a) + ordered[b] * (h - a)
    amp['iqr'] = estimate(quantile(.75) - quantile(.25)) if n else estimate(status='undefined', reason='no usable observations')
    zero_run = missing_run = longest_zero = longest_missing = 0;last_positive = None;gaps = []
    for i, p in enumerate(periods):
        if not usable(p):
            zero_run = 0;last_positive = None
            missing_run = missing_run + 1 if p['state'] in {'missing', 'absent'} else 0
        else:
            missing_run = 0;zero_run = zero_run + 1 if p['value'] == 0 else 0
            if p['value'] > 0:
                if last_positive is not None: gaps.append(i - last_positive)
                last_positive = i
        longest_zero = max(longest_zero, zero_run);longest_missing = max(longest_missing, missing_run)
    def longest_state(state):
        best = run = 0
        for p in periods:
            run = run + 1 if p['state'] == state else 0
            best = max(best, run)
        return best
    adi = ratio(n, len(positive), 'no positive periods')
    freq = {'coverage': ratio(n, len(periods)), 'adi': adi, 'positive_probability': ratio(len(positive), n),
            'observed_zero_periods': n - len(positive), 'observed_positive_periods': len(positive),
            'longest_zero_run': longest_zero, 'longest_missing_run': longest_state('missing'),
            'longest_absent_run': longest_state('absent'), 'longest_unavailable_run': longest_missing,
            'mean_positive_gap': estimate(st.fmean(gaps)) if gaps else estimate(status='undefined', reason='no uninterrupted positive gaps'),
            'positive_gap_cv2': ratio(st.pvariance(gaps), st.fmean(gaps) ** 2) if len(gaps) >= 2 else estimate(status='undefined', reason='fewer than two uninterrupted positive gaps'),
            'positive_gaps_used': len(gaps)}
    sbc = estimate(status='undefined', reason='no positive periods')
    if positive:
        sbc = estimate(('lumpy' if cv2['value'] >= .49 else 'intermittent') if adi['value'] >= 1.32 else ('erratic' if cv2['value'] >= .49 else 'smooth'),
                       rule='classic SBC: ADI >=1.32 and positive population CV2 >=0.49')
    reason = 'unequal exposure; comparable-exposure assumption not met' if unequal else 'no usable nonnegative integer counts' if not x or any(not float(v).is_integer() for v in x) else ''
    noise = {'assumption': 'model-conditional oracle estimates using training parameters; no fitted forecast or parameter uncertainty'}
    if reason:
        for key in ('poisson_mse', 'poisson_median_mae', 'nb2_k', 'nb2_mse'): noise[key] = estimate(status='not estimable', reason=reason)
    else:
        noise['poisson_mse'] = estimate(mean, model='Poisson', formula='lambda')
        noise['poisson_median_mae'] = poisson_mae(mean)
        variance = st.variance(x) if n >= 2 else 0
        if n >= 2 and mean > 0 and variance > mean:
            k = mean ** 2 / (variance - mean)
            noise['nb2_k'] = estimate(k, estimator='sample moments: mu^2/(sample variance-mu)')
            noise['nb2_mse'] = estimate(mean + mean ** 2 / k, model='NB2', formula='mu+mu^2/k')
        else:
            for key in ('nb2_k', 'nb2_mse'): noise[key] = estimate(status='not estimable', reason='no positive excess sample variance or fewer than two observations')
    wavelength = {cycle: seasonal(periods, grain, cycle) for cycle in ('week', 'month', 'year')}
    if unequal:
        sbc = estimate(status='not estimable', reason='unequal exposure')
        for item in wavelength.values(): item['strength'] = estimate(status='not estimable', reason='unequal exposure')
    known_exposure = math.fsum(p['exposure'] for p in periods if p['state'] != 'absent' and p.get('exposure') is not None and p['exposure'] >= 0)
    source_exposure = math.fsum(p.get('source_exposure_total', p.get('exposure') or 0) for p in periods if p['state'] != 'absent')
    return {'duration': {'calendar_span': len(periods), 'usable_observations': n, 'observed_exposure': known_exposure, 'usable_exposure': math.fsum(exposures),
                         'source_observed_exposure': source_exposure,
                         'states': {s: sum(p['state'] == s for p in periods) for s in ('observed', 'missing', 'closed', 'absent')}, 'unequal_exposure': unequal,
                         'regime_age': estimate(status='not estimable', reason='no changepoint rule declared in this slice')},
            'amplitude': amp, 'frequency': freq, 'wavelength': wavelength, 'sbc': sbc, 'noise': noise}
