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
