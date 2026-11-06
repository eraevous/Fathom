"""Local intraday counts partitioned by declared/observed offset basis."""
from collections import Counter
from datetime import date


def intraday_profile(parsed,name,chart):
    timed=[p for _,p in parsed if 'time' in p];bases=[];charts=[]
    for basis in sorted({p['clock_basis'] for p in timed}):
        ps=[p for p in timed if p['clock_basis']==basis]
        hours={f'{h:02d}':sum(p['hour']==h for p in ps) for h in range(24)}
        minutes={f'{m:02d}':sum(p['minute']==m for p in ps) for m in range(60)}
        seconds={f'{s:02d}':sum(p['second']==s for p in ps) for s in range(60)}
        weekdays=('Mon','Tue','Wed','Thu','Fri','Sat','Sun')
        matrix={day:{f'{h:02d}':sum('date' in p and date.fromisoformat(p['date']).weekday()==i and p['hour']==h for p in ps) for h in range(24)} for i,day in enumerate(weekdays)}
        bases.append({'basis':basis,'count':len(ps),'earliest':min(p['time'] for p in ps),'latest':max(p['time'] for p in ps),
                      'hour_counts':hours,'minute_counts':minutes,'second_counts':seconds,'precision_counts':dict(sorted(Counter(p['precision'] for p in ps).items())),
                      'weekday_hour_counts':matrix if any('date' in p for p in ps) else {}})
        charts.append(chart('bar',f'Hour of day for {name} — {basis} (written local clock)','Rows (count)','Hour of day',data=[{'label':h,'count':n} for h,n in hours.items()]))
    return {'basis':'written local clocks; naive and each UTC offset kept separate; no conversion; time-only values have no date','bases':bases},charts



def subsecond_profile(parsed):
    """No unresolved fourth field contributes a fractional or frame measurement."""
    ps=[p for _,p in parsed]
    unknown=[p['fourth_field']['raw'] for p in ps if p.get('fourth_field',{}).get('kind')=='undeclared']
    fractions=[p['microsecond'] for p in ps if p.get('fractional_digits',0)>0]
    frames=[p['fourth_field'] for p in ps if p.get('fourth_field',{}).get('kind')=='frame']
    return {'undeclared_count':len(unknown),'undeclared_examples':unknown[:10],
            'exclusion_reason':'Undeclared fourth field may be fractional seconds or frames; retained as written and excluded from sub-second statistics. Declare %f or %F plus frame_rate.',
            'fraction_count':len(fractions),'fraction_min_microsecond':min(fractions) if fractions else None,'fraction_max_microsecond':max(fractions) if fractions else None,
            'frame_count':len(frames),'frame_groups':[{'frame_rate':rate,'count':sum(f['frame_rate']==rate for f in frames),'min':min(f['frame'] for f in frames if f['frame_rate']==rate),'max':max(f['frame'] for f in frames if f['frame_rate']==rate)} for rate in sorted({f['frame_rate'] for f in frames})],
            'frame_basis':'Declared frame indices/rates only; no frame-to-microsecond or drop-frame conversion.'}
