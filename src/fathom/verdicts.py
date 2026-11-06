"""Presentation of existing evidence; no analysis selection or verdict rules."""
from html import escape
from .presentation import formatted


def gate_text(g):
    if g.get('status')!='computed':return g['measure']+': not estimable ('+g.get('reason','no comparison')+')'
    return (g['measure']+' gap '+formatted(g['gap'])+(' ≥ ' if g['marked'] else ' < ')+
            ('SD ' if g['measure']=='mean' else '')+formatted(g['threshold'])+' → '+('marked' if g['marked'] else 'not marked'))


def skew_text(g):
    if not g:return 'Strong-skew gate evidence unavailable in this saved artifact.'
    relation=' ≥ ' if g['moment_passed'] else ' < '
    disp=' ≥ ' if g['displacement_passed'] else ' < '
    return (f"n {g['n']} ≥ 8; |skew| {formatted(g['skew'])}"+relation+'2; |mean−median| '+
            formatted(g['displacement_ratio'])+'·'+g['reference']+disp+'½'+g['reference']+' → '+
            ('strongly skewed' if g['marked'] else 'not strongly skewed')+'.')


def key_findings(d):
    """Stable coverage slots; existing pair rank/order is retained, never recomputed."""
    findings=d.get('findings',[]);out=[];seen=set()
    def add(message,ref,status='automated',finding=None):
        if len(out)<5 and ref not in seen:
            out.append({'message':message,'ref':ref,'status':status,**({'finding':finding} if finding is not None else {})});seen.add(ref)
    lift=d.get('liftoff',{})
    for f in lift.get('automated_findings',[]):
        if f['kind']=='observation':add(f['message'],f['id'],finding=f);break
    rank={(r['left'],r['right']):r['rank'] for r in d.get('selection',{}).get('ranked',[]) if r.get('selected')}
    pairs=[f for f in findings if f.get('rule')=='selected_relation' and f['kind']=='observation']
    pairs.sort(key=lambda f:rank.get(tuple(f.get('columns',[])),10**9))
    if pairs:
        for f in pairs[:2]:add(f['message'],f['id'],finding=f)
    for f in findings:
        if f.get('rule')=='target_group_contrast' and f['kind']=='observation':add(f['message'],f['id'],finding=f);break
    series=[(s,False,'temporal-structure') for e in d.get('time_series',{}).get('series',[]) for s in e.get('groups',[])]
    for i,p in enumerate(lift.get('previews',{}).get('time_series',[])):
        series.extend((s,True,f'lift-series-detail-{i}') for s in p['result'].get('groups',[]))
    cycles=[];gaps=[]
    for s,conditional,ref in series:
        prefix=('If you declare event counts by ' if conditional else 'Declared series by ')+s['time']+': '
        for g in s['granularities']:
            c=g['wavelength']['values']
            for lag in c.get('dominant_lags',[]):
                if lag['lag']>=2 and c.get('family_band') is not None and abs(lag['acf'])>c['family_band']:
                    cycles.append((prefix+f"{lag['lag']} {g['granularity']} cycle (ACF {formatted(lag['acf'])}, family gate {formatted(c['family_band'])}).",ref,conditional))
            missing=g['no_recorded_event_periods'] if s['mode']=='events' else g['missing_periods']
            if missing:gaps.append((prefix+f"{missing:,} {g['granularity']} periods "+('with no recorded event (counted as zero; observation unknown).' if s['mode']=='events' else 'missing observations.'),ref,conditional))
    for items,suffix in [(cycles,'cycle'),(gaps,'gaps')]:
        if items:
            message,ref,cond=items[0];add(message,ref+'#'+suffix,'provisional' if cond else 'automated')
    for f in findings:
        if f['kind']=='observation' and f.get('rule') not in {'dataset_summary','selected_relation','target_group_contrast'} and f['id'] not in {'duplicates','overview','shape'}:
            add(f['message'],f['id'],finding=f)
    return out


def headlines_html(d):
    items=key_findings(d)
    from .finding_view import finding_tree,html_tree
    tag='li' if len(items)>=3 else 'div'
    body=''.join('<'+tag+'>'+html_tree(finding_tree(i.get('finding',{'id':i['ref'],'kind':'observation','message':i['message'],'evidence':[]}),d),[c['name'] for c in d.get('columns',[])],styled=False)+' <a href="#'+escape(i['ref'].split('#')[0],quote=True)+'">Evidence</a></'+tag+'>' for i in items)
    return '<section id="key-findings"><h2>Key findings</h2>'+('<ul>'+body+'</ul>' if len(items)>=3 else body or '<p>No matching headline evidence; this is not a quality verdict.</p>')+'</section>'



def inline_rule(f):
    if f['kind']!='observation':return ''
    for e in f.get('evidence',[]):
        value=e.get('value')
        if isinstance(value,dict):
            if value.get('gates'):return '; '.join(gate_text(g) for g in value['gates'])
            if isinstance(value.get('rule'),str):return value['rule']
    return f.get('gate','')
