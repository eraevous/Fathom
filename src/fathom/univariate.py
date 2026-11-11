"""Deterministic univariate evidence and chart specifications, without new pair methods."""

from collections import Counter
from datetime import date
import math
from pathlib import Path
import random
import re
import statistics

from .parsing import finite_number, parse_date, parse_temporal, MONTH_NAMES

PERCENTILES=(1,5,25,33,50,66,75,95,99)


BIN_RULE='sqrt(n) rounded up, capped at 10 (system default)'


WHOLE_BIN_RULE=('whole-number columns: one bar per value up to 16 values; beyond that, the best 16-value range '
                'with a sparse tail (at most 5% of rows) in a callout, else up to 16 equal whole-value bars (system default)')


def bin_rule(bins=None,whole=False):
    """Disclosed histogram bin rule; `bins` is the human `bins:` declaration (spec012).
    `whole` selects the whole-number rule (spec 028) for one chart."""
    if bins:return f'at most {bins} equal whole-value bins (declared in configuration)' if whole else f'{bins} equal-width bins (declared in configuration)'
    return WHOLE_BIN_RULE if whole else BIN_RULE


def report_bin_rule(bins=None):
    """Report-level disclosure covering both fractional and whole-number histograms."""
    return f'{bins} equal-width bins; whole-number columns use at most {bins} whole-value bins (declared in configuration)' if bins else BIN_RULE+'; '+WHOLE_BIN_RULE


def bin_count(n,lo,hi,bins=None):
    if hi==lo:return 1
    return bins if bins else min(10,max(1,math.ceil(math.sqrt(n))))


def stored(n,figures=6):
    """Stored-number rule (spec 008 FR-001): at least `figures` significant figures, never fewer than 10 decimals."""
    if n is None or not math.isfinite(n):return None
    if n==0:return n
    return round(n,max(10,figures-1-math.floor(math.log10(abs(n)))))


def geometry(n):
    """Scale-aware chart geometry (FR-002): 12 significant figures, so tiny charts keep their shape."""
    return stored(n,12)


def coefficient(n):
    """Dimensionless coefficients computed on normalized values (skewness, kurtosis, r, eta, V): 10 decimals,
    because anything smaller is floating-point noise, not a small-scale measurement (spec 008 FR-001)."""
    return round(n,10) if n is not None and math.isfinite(n) else None


safe=stored


def percentile(values,p,rule=None):
    if not values: return None
    ordered=sorted(values);position=(len(ordered)-1)*p/100
    lo=int(position);hi=min(lo+1,len(ordered)-1);w=position-lo
    scale=max(abs(ordered[lo]),abs(ordered[hi]),1)
    return (rule or stored)((ordered[lo]/scale*(1-w)+ordered[hi]/scale*w)*scale)


def raw_percentile(values,p):
    return percentile(values,p,geometry)


def common(counter,least=False,limit=10):
    return [{'value':v,'count':n} for v,n in sorted(counter.items(),key=lambda x:(x[1] if least else -x[1],x[0]))[:limit]]


def chart(kind,title,x,y,**data):
    return {'kind':kind,'title':title,'x_label':x,'y_label':y,**data}


def identity_and_samples(data,cfg,columns):
    names=[c['name'] for c in columns];n=len(data.frame)
    suggested=[]
    for term,pattern in [('identifiers/titles',r'(^id$|_id$|title|name|key)'),('amounts',r'(gross|amount|revenue|cost|price)'),('dates',r'(date|release)'),('categories',r'(category|genre|group|status)')]:
        matches=[name for name in names if re.search(pattern,name,re.I)]
        if matches: suggested.append(term+' ('+', '.join(matches[:5])+')')
    description=f"Schema sketch: {n} rows and {len(names)} columns"+('; names suggest '+', '.join(suggested) if suggested else '; domain '+('is unknown (row unit declared in the working record)' if cfg.get('row_unit') else 'and row unit are unknown'))+'. These readings are inferred, not domain facts.'
    dataset={'title':{'text':cfg.get('title') or Path(data.source['origin']).stem,'status':'human' if cfg.get('title') else 'inferred','generator':'human' if cfg.get('title') else 'rule:filename-v1'},
             'description':{'text':cfg.get('description') or description,'status':'human' if cfg.get('description') else 'inferred','generator':'human' if cfg.get('description') else 'rule:schema-sketch-v1'},
             'basis':{'filename':Path(data.source['origin']).name,'columns':names,'inferred_types':dict(sorted(Counter(c['inference']['type'] for c in columns).items()))}}
    raw=data.raw_rows if data.raw_rows is not None else data.frame.values.tolist()
    size,seed,limit=cfg['sample_rows'],cfg['sample_seed'],cfg['sample_text_limit'];k=min(n,size)
    def window(indices):
        result=[]
        for i in indices:
            values=[];truncated=0
            for v in raw[i]:
                if v is not None and len(v)>limit:
                    v=v[:limit]+'… [truncated]';truncated+=1
                values.append(v)
            result.append({'position':i+1,'values':values,'truncated_cells':truncated})
        return result
    return dataset,{'size':size,'seed':seed,'text_limit':limit,'columns':names,
                    'note':'Sample tables contain raw input values; windows can overlap; random rows are without replacement.',
                    'lexical_source':'original CSV cells' if data.raw_rows is not None else 'canonical cells; original blank lexemes unavailable',
                    'first':window(range(k)),'last':window(range(n-k,n)),'random':window(sorted(random.Random(seed).sample(range(n),k)))}


def numeric_profile(values,name,units,bins=None):
    nums=[n for v in values if (n:=finite_number(v)) is not None];n=len(nums)
    percentiles={str(p):percentile(nums,p) for p in PERCENTILES}
    skew=kurt=None
    if n>=2 and max(nums)!=min(nums):
        scale=max(abs(x) for x in nums) or 1;normalized=[x/scale for x in nums]
        mu=statistics.mean(normalized);sd=statistics.pstdev(normalized)
        if sd:
            skew=coefficient(statistics.mean(((x-mu)/sd)**3 for x in normalized))
            kurt=coefficient(statistics.mean(((x-mu)/sd)**4 for x in normalized)-3)
    counts=Counter(v for v in values if finite_number(v) is not None)
    stats={'finite':n,'zeros':{'count':sum(x==0 for x in nums),'share':sum(x==0 for x in nums)/n if n else None},
           'negatives':{'count':sum(x<0 for x in nums),'share':sum(x<0 for x in nums)/n if n else None},
           'integers':sum(x.is_integer() for x in nums),'non_integers':sum(not x.is_integer() for x in nums),
           'percentiles':percentiles,'skewness':skew,'excess_kurtosis':kurt,
           'skew_interpretation':'Undefined for constant/insufficient values.' if skew is None else ('Right tail pulls the mean upward.' if skew>1 else 'Left tail pulls the mean downward.' if skew<-1 else 'No strong tail asymmetry under this moment rule.'),
           'kurtosis_interpretation':'Undefined for constant/insufficient values.' if kurt is None else ('More tail weight than a normal reference; not a normality test.' if kurt>1 else 'No elevated tail weight under this moment rule; not a normality test.'),
           'most_common':common(counts),'least_common':common(counts,True),
           'share_denominator':'finite values','formatting':'Local currency/thousands/parenthesis parsing; symbols do not establish units or comparability.'}
    charts=[]
    if nums:
        lo,hi=min(nums),max(nums);declared=bins
        data,whole=histogram_bins(nums,declared)
        axis=f'{name} ({units or "recorded values; units unknown"})'
        charts=[chart('histogram',f'Distribution of {name}',axis,'Rows (count)',data=data,bin_rule=bin_rule(declared,bool(whole)),**whole),
                chart('box',f'Five-number view of {name}',axis,'Column',box={'min':geometry(lo),'q1':raw_percentile(nums,25),'median':raw_percentile(nums,50),'q3':raw_percentile(nums,75),'max':geometry(hi)})]
        cumulative=0;points=[]
        for x,count in sorted(Counter(nums).items()):
            cumulative+=count;points.append({'x':x,'cumulative':cumulative/n,'count':cumulative})
        omitted=max(0,len(points)-200)
        if omitted:points=[points[round(i*(len(points)-1)/199)] for i in range(200)]
        charts.append(chart('ecdf',f'Empirical cumulative distribution of {name}',axis,'Finite values at or below X (%)',points=points,omitted_points=omitted,n=n))
        positives=[x for x in nums if x>0]
        if len(positives)>=2 and len(set(positives))>1 and skew is not None and skew>=2:
            coverage={'positive':len(positives),'zeros':sum(x==0 for x in nums),'negatives':sum(x<0 for x in nums),'invalid':len(values)-n}
            charts.append(histogram([math.log10(x) for x in positives],f'Positive log distribution of {name}',axis+' (log scale)',scale='log10',coverage_counts=coverage,bins=declared))
            points=[];cumulative=0
            for value,count in sorted(Counter(positives).items()):
                cumulative+=count;points.append({'x':math.log10(value),'cumulative':cumulative/len(positives),'count':cumulative})
            omitted=max(0,len(points)-200)
            if omitted:points=[points[round(i*(len(points)-1)/199)] for i in range(200)]
            charts.append(chart('ecdf',f'Positive log ECDF of {name}',axis+' (log scale)','Positive values at or below X (%)',points=points,omitted_points=omitted,n=len(positives),scale='log10',coverage_counts=coverage))
    return stats,charts


def histogram(nums,title,x_label,bins=None,**metadata):
    # A log10 axis is never a whole-number scale, even when every value is a power of ten.
    data,whole=histogram_bins(nums,bins,allow_whole=metadata.get('scale')!='log10')
    metadata['bin_rule']=bin_rule(bins,bool(whole))
    return chart('histogram',title,x_label,'Values (count)',data=data,**metadata,**whole)


WHOLE_BARS=16      # default bar cap for whole-number charts: closest power of two under 32 (owner, 2026-11-11)
TAIL_SHARE=0.05    # a sparse tail: at most this share of rows outside the best WHOLE_BARS-value window
TAIL_ITEMS=6       # tail values listed one by one up to this many per side; beyond it, at most 4 ranges


def whole_runs(values,width,first=None,last=None):
    """Group whole ``values`` (a Counter) into inclusive runs of ``width`` from ``first`` to ``last``
    (default: the smallest and largest value present). Empty runs are kept."""
    first=min(values) if first is None else first;last=max(values) if last is None else last
    out=[]
    for start in range(first,last+1,width):
        stop=min(last,start+width-1)
        count=sum(c for v,c in values.items() if start<=v<=stop)
        out.append({'label':str(start) if start==stop else f'{start} to {stop}','low':start-.5,'high':stop+.5,'count':count})
    return out


def tail_items(values,side):
    """Sparse-tail callout items for one side: one per distinct value, or at most 4 non-empty ranges."""
    if not values:return []
    if len(values)<=TAIL_ITEMS:
        items=[{'label':str(v),'low':v-.5,'high':v+.5,'count':c} for v,c in sorted(values.items())]
    else:
        width=-(-(max(values)-min(values)+1)//4)
        items=[d for d in whole_runs(values,width) if d['count']]
    return [{**d,'side':side} for d in items]


def histogram_bins(nums,bins=None,allow_whole=True):
    """Histogram bins for one numeric series (spec 028).

    Returns ``(data, extra)``. ``data`` holds one dict per main-chart bin: ``label``
    (what the hover title, chart-values table and exports show), ``low``/``high`` (axis
    geometry) and ``count``. ``extra`` is merged into the chart dict.

    **Whole-number series** (every finite value has no fractional part: counts, mana
    values, string lengths) get whole-number bins: each holds a contiguous run of
    integers, labelled inclusively ("3" or "0 to 2"), so a label never names a value the
    data cannot take ("6 to 7.2"). Geometry sits on half-integers (2.5 to 5.5 for
    "3 to 5") so each bar is centred on its values. Membership is exact.

    Bar count for whole numbers: a declared ``bins:`` is a maximum, as before. Without a
    declaration the cap is WHOLE_BARS (16):

    1. a range of at most 16 values gets one bar per value;
    2. otherwise, if the best 16-value window holds all but a sparse tail (at most
       TAIL_SHARE of rows), the main chart shows that window one bar per value and the
       values outside it go to ``tail`` (drawn as a callout inset with its own scale);
    3. otherwise up to 16 equal whole-value bars cover the whole range.

    ``data`` plus ``tail`` always account for every value. Magnitudes above 2**53 (where
    every float is integral) and any series with a fractional value keep the original
    equal-width real-valued bins and ``.5g`` labels: genuine fractions are never
    rounded away. Stored values and statistics are untouched either way.
    """
    lo,hi=min(nums),max(nums);n=len(nums)
    # Above 2**53 every float is "whole", so integrality says nothing about the data there.
    if allow_whole and max(abs(lo),abs(hi))<=2**53 and all(float(x).is_integer() for x in nums):
        values=Counter(int(x) for x in nums);lo,hi=min(values),max(values);span=hi-lo+1
        cap=bins or WHOLE_BARS
        if span<=cap:
            return whole_runs(values,1),{'whole_number_bins':{'width':1}}
        if not bins:
            # Best window of `cap` consecutive values, scanning windows that start at a data value.
            keys=sorted(values);best=(-1,lo);j=0;inside=0
            for i,start in enumerate(keys):
                while j<len(keys) and keys[j]<=start+cap-1:inside+=values[keys[j]];j+=1
                if inside>best[0]:best=(inside,start)
                inside-=values[start]
            outside=n-best[0]
            if 0<outside<=TAIL_SHARE*n:
                first=min(best[1],hi-cap+1);last=first+cap-1
                core=Counter({v:c for v,c in values.items() if first<=v<=last})
                data=whole_runs(core,1,first,last)
                tail=tail_items(Counter({v:c for v,c in values.items() if v<first}),'low')+tail_items(Counter({v:c for v,c in values.items() if v>last}),'high')
                return data,{'whole_number_bins':{'width':1,'core':[first,last],'tail_rows':outside},'tail':tail}
        width=-(-span//cap)  # exact integer ceiling division
        return whole_runs(values,width,lo),{'whole_number_bins':{'width':width}}
    bins=bin_count(n,lo,hi,bins)
    # Normalized arithmetic avoids overflowing a finite but wide numeric range.
    scale=max(abs(lo),abs(hi),1);a,b=lo/scale,hi/scale
    edges=[(a+(b-a)*i/bins)*scale for i in range(bins+1)];counts=[0]*bins
    for x in nums:counts[min(bins-1,int((x/scale-a)/(b-a)*bins)) if b!=a else 0]+=1
    return [{'label':f'{edges[i]:.5g} to {edges[i+1]:.5g}','low':geometry(edges[i]),'high':geometry(edges[i+1]),'count':c} for i,c in enumerate(counts)],{}


def missingness_patterns(columns,rows):
    counts=Counter(tuple(c['name'] for c,v in zip(columns,row) if v is None) for row in rows)
    ordered=sorted(counts.items(),key=lambda x:(-x[1],x[0]));n=len(rows)
    missing_names={name for mask in counts for name in mask}
    names=[c['name'] for c in columns if c['name'] in missing_names]
    patterns=[{'missing':list(mask),'count':count,'share':count/n if n else None} for mask,count in ordered[:20]]
    data=[{'label':f'P{i+1}: '+(', '.join(p['missing'][:20]) or 'Complete rows')+(' …' if len(p['missing'])>20 else ''),'count':p['count'],'share':p['share']} for i,p in enumerate(patterns)]
    return {'columns':names[:20],'omitted_columns':max(0,len(names)-20),'patterns':patterns,'rows':n,
            'omitted_patterns':max(0,len(ordered)-20),'omitted_rows':sum(c for _,c in ordered[20:]),
            'chart':chart('bar','Exact row missingness patterns','Rows (count)','Columns missing together',data=data),
            'basis':'Canonical nulls only; exact row masks, not causal or within-group analysis.'}


def text_profile(raw,name,bins=None):
    values=[v for v in raw if v is not None];counts=Counter(values);n=len(values)
    blank={'empty':sum(v=='' for v in values),'whitespace':sum(bool(v) and not v.strip() for v in values),
           'tokens':sum(v.strip().casefold() in {'na','nan','none','null','blank','n/a'} for v in values),
           'unavailable_lexeme':sum(v is None for v in raw)}
    lengths=[len(v) for v in values];casing=Counter({'upper':0,'lower':0,'mixed':0,'uncased':0})
    chars,tokens=Counter(),Counter()
    for v in values:
        letters=''.join(c for c in v if c.isalpha())
        casing['uncased' if not letters else 'upper' if letters.isupper() else 'lower' if letters.islower() else 'mixed']+=1
        chars.update(c for c in v if not c.isalnum() and not c.isspace());tokens.update(re.findall(r'\w{2,}',v.casefold()))
    top=common(counts);rare=[{'value':v,'count':c} for v,c in sorted(counts.items(),key=lambda x:(x[1],x[0])) if c<=2 or (n and c/n<=.01)]
    stats={'raw_lexemes':n,'special_character_total':sum(chars.values()),'substring_total':sum(tokens.values()),'candidate_blanks':blank,'length':{'min':min(lengths) if lengths else None,'max':max(lengths) if lengths else None,'mean':safe(statistics.mean(lengths)) if lengths else None,'median':safe(statistics.median(lengths)) if lengths else None},
           'casing':dict(casing),'special_characters':common(chars),'common_substrings':common(tokens),'substring_basis':'case-folded word tokens, length>=2','special_character_basis':'character occurrences; whitespace excluded',
           'entropy_bits':safe(-sum((c/n)*math.log2(c/n) for c in counts.values())) if n else None,
           'top_n_coverage':{'n':10,'count':sum(x['count'] for x in top),'share':sum(x['count'] for x in top)/n if n else None},
           'rare_levels':rare[:20],'rare_level_count':len(rare),'most_common':top,'least_common':common(counts,True)}
    data=[{'label':x['value'] or '[empty string]','count':x['count'],'share':x['count']/n} for x in top]
    other=n-sum(x['count'] for x in top)
    if other:
        remainder='[Other values — remainder]'
        while remainder in counts:remainder+=' (aggregate)'
        data.append({'label':remainder,'count':other,'share':other/n,'is_other':True})
    charts=[chart('bar',f'Most common values of {name}','Values (count)','Value (top 10 + remainder)',data=data,coverage=sum(x['count'] for x in top)/n,denominator=n)] if top else []
    if lengths:charts.append(histogram(lengths,f'String lengths in {name}','Raw string length (characters)',bins=bins,measure='string_length'))
    return stats,charts


def calendar_profile(values,name,cfg,meta,parsed=None):
    year_precision=meta.get('date_format')=='YEAR'
    if parsed is None:parsed=[(v,p) for v in values if (p:=parse_date(v,meta.get('date_format'))) is not None]
    dates=[date.fromisoformat(p['date']) for _,p in parsed];n=len(dates);unique=sorted(set(dates))
    reference=cfg['context'].get('snapshot_date');ref=date.fromisoformat(reference) if reference else None
    periods=Counter(d.strftime('%Y-%m') for d in dates)
    chart_data=[{'label':k,'count':v} for k,v in sorted(periods.items())]
    omitted=max(0,len(chart_data)-60)
    if omitted:chart_data=chart_data[:30]+chart_data[-30:]
    series=[];period='month'
    if unique:
        first,last=unique[0].year*12+unique[0].month-1,unique[-1].year*12+unique[-1].month-1
        if last-first<=1200:
            series=[periods.get(f'{m//12:04}-{m%12+1:02}',0) for m in range(first,last+1)]
        else:
            period='year';years=Counter(d.year for d in dates);series=[years.get(y,0) for y in range(unique[0].year,unique[-1].year+1)]
    if unique and year_precision:
        period='year';years=Counter(d.year for d in dates);series=[years.get(y,0) for y in range(unique[0].year,unique[-1].year+1)]
    lag=None
    if len(series)>=3 and len(set(series[:-1]))>1 and len(set(series[1:]))>1:lag=coefficient(statistics.correlation(series[:-1],series[1:]))
    intervals=[(b-a).days for a,b in zip(unique,unique[1:])]
    gap_basis=statistics.median(intervals) if intervals else None
    gaps=[{'after':a.isoformat(),'before':b.isoformat(),'days':(b-a).days} for a,b in zip(unique,unique[1:]) if gap_basis and (b-a).days>3*gap_basis]
    stats={'valid':n,'invalid':len(values)-n,'earliest':min(dates).isoformat() if dates else None,'latest':max(dates).isoformat() if dates else None,
           'span_days':(max(dates)-min(dates)).days if dates else None,'parse_formats':dict(sorted(Counter(p['format'] for _,p in parsed).items())),
           'parse_basis':('human format override' if meta.get('date_format') else 'inferred local formats; numeric ambiguity defaults MDY')+('; date-times are profiled by calendar date, time of day is not analysed' if any(p['format']=='ISO_DATETIME' for _,p in parsed) else ''),
           'two_digit_years':sum(p['two_digit_year'] for _,p in parsed),'ambiguous_dates':sum(bool(p['alternatives']) for _,p in parsed),
           'parsed_examples':[{'raw':v,**p} for v,p in parsed[:10]],
           'two_digit_examples':[{'raw':v,**p} for v,p in parsed if p['two_digit_year']][:10],
           'ambiguous_examples':[{'raw':v,**p} for v,p in parsed if p['alternatives']][:10],
           'invalid_examples':[v for v in values if parse_date(v,meta.get('date_format')) is None][:10],
           'future_examples':[{'raw':v,**p} for v,p in parsed if (ref and date.fromisoformat(p['date'])>ref) or int(p['date'][:4])>2100][:10],'placeholder_dates':sum(d.isoformat() in {'1900-01-01','1970-01-01'} for d in dates),
           'after_reference':sum(d>ref for d in dates) if ref else None,'beyond_fixed_year_2100':sum(d.year>2100 for d in dates),
           'reference_date':reference,'weekday_counts':dict(zip(('Mon','Tue','Wed','Thu','Fri','Sat','Sun'),[sum(d.weekday()==i for d in dates) for i in range(7)])),
           'month_counts':dict(zip(MONTH_NAMES,[sum(d.month==i for d in dates) for i in range(1,13)])),
           'quarter_counts':{f'Q{i}':sum((d.month-1)//3+1==i for d in dates) for i in range(1,5)},'year_counts':dict(sorted(Counter(f'{d.year:04d}' if year_precision else str(d.year) for d in dates).items())),
           'large_gaps':gaps[:20],'omitted_gaps':max(0,len(gaps)-20),'gap_rule':'more than three times median distinct-date spacing',
           'lag1_period':period,'lag1_count_autocorrelation':lag,'lag1_basis':'consecutive periods including zeros; descriptive, not a stationarity test'}
    if year_precision:
        stats.update(precision='year',parse_basis='Declared YEAR; 1 January anchor only, not observed month/day',weekday_counts={},month_counts={},quarter_counts={},placeholder_dates=0)
    charts=[]
    if unique:
        days=(unique[-1]-unique[0]).days
        chart_period='year' if year_precision else 'day' if days<=60 else 'month' if days<=365*5 else 'year'
        if chart_period=='day':
            from datetime import timedelta
            observed=Counter(d.isoformat() for d in dates)
            chart_data=[{'label':(unique[0]+timedelta(days=i)).isoformat(),'count':observed.get((unique[0]+timedelta(days=i)).isoformat(),0)} for i in range(days+1)]
        elif chart_period=='month':
            chart_data=[{'label':f'{m//12:04}-{m%12+1:02}','count':periods.get(f'{m//12:04}-{m%12+1:02}',0)} for m in range(first,last+1)]
        else:
            years=Counter(d.year for d in dates);chart_data=[{'label':f'{y:04d}' if year_precision else str(y),'count':years.get(y,0)} for y in range(unique[0].year,unique[-1].year+1)]
        omitted=max(0,len(chart_data)-60)
        if omitted:chart_data=chart_data[:30]+chart_data[-30:]
        charts=[chart('time',f'Record counts over time for {name}',f'Calendar {chart_period} (parsed dates)','Rows (count)',data=chart_data,omitted_periods=omitted,period=chart_period)]
        for key,basis in ([] if year_precision else [('weekday_counts','weekday'),('month_counts','month')]):
            charts.append(chart('bar',f'{basis.capitalize()} counts for {name}','Parsed dates (count)',basis.capitalize(),data=[{'label':k.capitalize(),'count':v} for k,v in stats[key].items()],calendar=basis))
    return stats,charts


def temporal_profile(values,name,cfg,meta):
    from .temporal_profiles import intraday_profile
    parsed=[(v,p) for v in values if (p:=parse_temporal(v,meta.get('date_format'),meta.get('frame_rate'))) is not None]
    from .temporal_formats import BUILTINS,pattern_parts
    fmt=meta.get('date_format');custom=fmt is not None and fmt not in BUILTINS
    tokens={v for k,v in pattern_parts(fmt) if k=='token'} if custom else set()
    declared_clock=bool(tokens&set('HI')) or fmt in {'TIME','DATETIME','ISO_DATETIME'}
    declared_date=bool(tokens&set('Yy')) or fmt in {'DATETIME','ISO_DATETIME'}
    if not any('time' in p for _,p in parsed) and not declared_clock:
        return calendar_profile(values,name,cfg,meta)
    dated=[(v,p) for v,p in parsed if 'date' in p]
    stats,charts=calendar_profile(values,name,cfg,meta,dated)
    kinds={p['kind'] for _,p in parsed}
    stats.update(valid=len(parsed),invalid=len(values)-len(parsed),calendar_valid=len(dated),temporal_kind=next(iter(kinds)) if len(kinds)==1 else 'mixed' if kinds else 'time' if declared_clock and not declared_date else 'timestamp' if declared_clock else 'date',
                 parse_formats=dict(sorted(Counter(p['format'] for _,p in parsed).items())),parse_basis=('human format override' if meta.get('date_format') else 'inferred local formats')+'; written date and local time retained; no timezone conversion',
                 parsed_examples=[{'raw':v,**p} for v,p in parsed[:10]],invalid_examples=[v for v in values if parse_temporal(v,meta.get('date_format'),meta.get('frame_rate')) is None][:10])
    intraday,extra=intraday_profile(parsed,name,chart);stats['intraday']=intraday;charts+=extra
    from .temporal_formats import temporal_fault
    from .temporal_profiles import subsecond_profile
    stats['subsecond']=subsecond_profile(parsed)
    faults={}
    for value in values:
        fault=temporal_fault(value,meta.get('date_format'),meta.get('frame_rate'))
        if fault:
            bucket=faults.setdefault(fault['code'],{'count':0,'examples':[],'message':fault['message']})
            bucket['count']+=1
            if len(bucket['examples'])<10:bucket['examples'].append(value)
    stats['parse_faults']=faults
    if not dated:
        for key in ['earliest','latest','span_days','weekday_counts','month_counts','quarter_counts','year_counts','large_gaps','placeholder_dates','after_reference','beyond_fixed_year_2100']:
            stats[key]=[] if key=='large_gaps' else {} if key.endswith('_counts') else None
    return stats,charts


def enrich_columns(columns,rows,raw_rows,cfg,emit,findings):
    for i,col in enumerate(columns):
        name=col['name'];meta=cfg['columns'].get(name,{});typ=col['effective_type']
        values=[r[i] for r in rows if r[i] is not None];raw=[r[i] for r in raw_rows]
        if typ in {'numeric','latitude','longitude'}:stats,charts=numeric_profile(values,name,meta.get('units') or ('degrees (inferred)' if typ in {'latitude','longitude'} else None),cfg.get('bins'))
        elif typ=='temporal':stats,charts=temporal_profile(values,name,cfg,meta)
        else:stats,charts=text_profile(raw,name,cfg.get('bins'))
        role=meta.get('role');basis='human' if role else 'human (schema key)' if name in cfg['schema'].get('key',[]) else 'inferred from column name'
        if role is None:
            role='identifier' if name in cfg['schema'].get('key',[]) or re.search(r'(^id$|_id$|key|code|title|name)',name,re.I) else 'quantity' if re.search(r'(gross|amount|revenue|cost|price)',name,re.I) else None
        col['univariate']={'statistics':stats,'charts':charts,'role':role,'role_basis':basis if role else 'unknown','units':{'value':meta['units'],'generator':'human'} if meta.get('units') else None}
        if role=='identifier' or (typ not in {'numeric','latitude','longitude','temporal'} and len(values)>=5 and len(set(values))/len(values)>=.9):
            col['univariate']['top_n_suppression']='Identifier-like values; values rarely repeat.' if role=='identifier' else 'Values rarely repeat (at least 90% distinct among nonmissing values).'
            charts[:]=[c for c in charts if not (c['kind']=='bar' and 'coverage' in c)]
        def notice(rule,message,evidence,action=None,kind='observation'):
            fid=f'u-{i}-{rule}'
            emit(fid,kind,message,[{'path':f'columns.{i}.univariate','value':evidence}],
                 'Descriptive local rule; meanings and domain expectations require confirmation.','rule:univariate-v1',rule=rule,columns=[name])
            if action:emit(fid+'-review','action',action,[{'finding':fid}], 'Suggested review, not automatic correction.','rule:univariate-v1',rule=rule,columns=[name])
        if typ=='temporal':
            sub=stats.get('subsecond',{})
            if sub.get('undeclared_count'):
                notice('ambiguous_clock_fourth',f"{name}: {sub['undeclared_count']} clock value(s) have an undeclared fourth field: fraction or video frames? Hour, minute and second are profiled; the raw fourth field is excluded from sub-second statistics until declared.",sub,kind='question')
            frame_faults={k:v for k,v in stats.get('parse_faults',{}).items() if k.startswith('frame_')}
            if frame_faults:notice('temporal_frame_fault',f'{name}: '+ '; '.join(k+': '+str(v['count'])+' value(s); '+v['message'] for k,v in frame_faults.items()),frame_faults)
            bases=stats.get('intraday',{}).get('bases',[])
            if len(bases)>1:notice('temporal_clock_bases',f'{name}: {len(bases)} clock bases are kept separate; no timezone conversion or cross-basis ordering is applied.',{'bases':[b['basis'] for b in bases]},'Confirm the timezone/clock meaning before comparing instants across bases.')
            for rule,key,message in [('two_digit_year','two_digit_years','has two-digit years under a fixed 69 pivot; the century is ambiguous'),('ambiguous_date','ambiguous_dates','has ambiguous numeric month/day readings'),('placeholder_date','placeholder_dates','contains possible placeholder dates'),('future_date','after_reference','contains dates after the declared snapshot'),('far_future_date','beyond_fixed_year_2100','contains dates beyond the fixed year-2100 bound')]:
                if stats.get(key):notice(rule,f"{name}: {stats[key]} value(s) {message}.",stats,f'Confirm the original dates and format of {name}; no century or date is silently repaired.')
            if stats['large_gaps'] and not any(f.get('rule')=='temporal_gap' and name in f.get('columns',[]) for f in findings):
                notice('univariate_gap',f"{name} has {len(stats['large_gaps'])} unusually large observed date gap(s).",stats['large_gaps'],f'Check the collection schedule for {name} before assuming observations are missing.')
        if role=='identifier':
            counts=Counter(values);repeats=sum(n-1 for n in counts.values())
            if repeats:notice('repeated_identifier',f'{name}, read as identifier-like ({basis}), repeats {repeats} nonmissing value(s) beyond the first.',common(Counter({v:n for v,n in counts.items() if n>1})),f'Confirm whether repeated {name} values are expected for the row unit.')
        if typ=='numeric' and role=='quantity':
            nums=[x for v in values if (x:=finite_number(v)) is not None];positives=[x for x in nums if x>0];zeros=sum(x==0 for x in nums)
            if len(nums)>=5 and zeros and zeros/len(nums)<=.2 and positives and statistics.median(positives)>=100 and sum(x>=100 for x in nums)>=.8*(len(nums)-zeros):
                notice('implausible_zero',f'{name} has {zeros}/{len(nums)} zero values while the median positive value is {statistics.median(positives):.6g}; zero may be a code or a genuine quantity.',{'zeros':zeros,'finite':len(nums),'median_positive':statistics.median(positives)},f'Confirm what zero means in {name} before treating it as missing or measured.')
        if typ=='numeric' and stats['skewness'] is not None and abs(stats['skewness'])>=2 and not any(f.get('rule')=='skew' and name in f.get('columns',[]) for f in findings):
            notice('univariate_skew',f"{name}: {stats['skew_interpretation']}",{'skewness':stats['skewness'],'excess_kurtosis':stats['excess_kurtosis']})
