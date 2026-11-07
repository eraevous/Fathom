"""Portable explicit local temporal readings. Never infer a date or convert an offset."""
from datetime import date,time
from functools import lru_cache
import re

BUILTINS=('ISO','ISO_DATETIME','MON_D_Y','MDY','DMY','YEAR','TIME','DATETIME')
MONTHS=('january','february','march','april','may','june','july','august','september','october','november','december')
TOKENS={'Y':r'\d{4}','y':r'\d{2}','m':r'\d{1,2}','d':r'\d{1,2}','b':r'[A-Za-z]{3}','B':r'[A-Za-z]+','H':r'\d{1,2}','I':r'\d{1,2}','M':r'\d{2}','S':r'\d{2}','f':r'\d{1,6}','p':r'AM|PM','z':r'Z|[+-]\d{2}:?\d{2}'}

@lru_cache(maxsize=128)
def pattern_parts(pattern):
    if not isinstance(pattern,str) or not pattern:raise ValueError('date_format must be a built-in name or a nonempty pattern')
    parts=[];seen=[];i=0
    while i<len(pattern):
        if pattern[i]!='%':parts.append(('literal',pattern[i]));i+=1;continue
        token=pattern[i:i+2];i+=2
        if token=='%%':parts.append(('literal','%'));continue
        if len(token)!=2 or token[1] not in TOKENS:raise ValueError('unsupported date_format token '+token)
        if token[1] in seen:raise ValueError('duplicate date_format token '+token)
        seen.append(token[1]);parts.append(('token',token[1]))
    keys=set(seen);dated=bool(keys&set('YymdbB'));clock=bool(keys&set('HIMSfpz'))
    if dated:
        for choices,label in [(set('Yy'),'%Y or %y'),(set('mbB'),'%m or %b or %B'),({'d'},'%d')]:
            if len(keys&choices)!=1:raise ValueError('date_format requires exactly one '+label+' (use YEAR for year-only values)')
    if clock:
        if len(keys&set('HI'))!=1:raise ValueError('date_format clock requires exactly one %H or %I')
        if ('I' in keys)!=('p' in keys):raise ValueError('date_format %I requires %p, and %p requires %I')
        if 'f' in keys and 'S' not in keys:raise ValueError('date_format %f requires %S')
    if not dated and not clock:raise ValueError('date_format requires date or clock tokens, such as %Y or %H')
    return tuple(parts)


def validate_format(pattern):
    if not isinstance(pattern,str):raise ValueError('date_format must be text')
    if pattern not in BUILTINS:pattern_parts(pattern)
    return pattern


def offset_label(value):
    if value is None:return 'naive'
    if value.upper()=='Z':return '+00:00'
    text=value.replace(':','');h,m=int(text[1:3]),int(text[3:5])
    if h>23 or m>59:raise ValueError('invalid UTC offset')
    return text[0]+f'{h:02d}:{m:02d}'


def from_parts(fields,fmt,has_date,has_clock):
    two='y' in fields;d=None;t=None
    if has_date:
        y=int(fields.get('Y',fields.get('y',0)))
        if two:y+=1900 if y>=69 else 2000
        month=fields.get('m')
        if month is None:
            name=fields.get('b',fields.get('B','')).casefold()
            month=next((i+1 for i,m in enumerate(MONTHS) if name==(m[:3] if 'b' in fields else m)),0)
        d=date(y,int(month),int(fields['d'])).isoformat()
    basis='calendar';precision='day';clock=None
    if has_clock:
        h=int(fields.get('H',fields.get('I',0)))
        if 'I' in fields:
            if not 1<=h<=12:raise ValueError('invalid12-hour clock')
            h=h%12+(12 if fields['p'].upper()=='PM' else 0)
        t=time(h,int(fields.get('M',0)),int(fields.get('S',0)),int(fields.get('f','0').ljust(6,'0')))
        clock=t.isoformat();basis=offset_label(fields.get('z'));precision='subsecond' if 'f' in fields else 'second' if 'S' in fields else 'minute' if 'M' in fields else 'hour'
    kind='timestamp' if d and clock else 'time' if clock else 'date'
    canonical=(d+'T' if d and clock else d or '')+(clock or '')+(basis if clock and basis!='naive' else '')
    out={'kind':kind,'format':fmt,'canonical':canonical,'clock_basis':basis,'precision':precision,'two_digit_year':two,'alternatives':[]}
    if d:out['date']=d
    if clock:out.update(time=clock,hour=t.hour,minute=t.minute,second=t.second,microsecond=t.microsecond,fractional_digits=len(fields.get('f','')))
    return out


def parse_temporal(value,hint=None):
    """A local reading; invalid values return None, invalid patterns raise ValueError."""
    if hint is not None:validate_format(hint)
    if not isinstance(value,str):
        if hint=='YEAR' and isinstance(value,int) and not isinstance(value,bool):value=str(value)
        else:return None
    text=value.strip()
    try:
        if hint is not None and hint not in BUILTINS:
            parts=pattern_parts(hint);regex='';keys=[]
            for kind,part in parts:
                if kind=='literal':regex+=re.escape(part)
                else:keys.append(part);regex+='(?P<'+part+'>'+TOKENS[part]+')'
            m=re.fullmatch(regex,text,re.I)
            return from_parts(m.groupdict(),hint,bool(set(keys)&set('Yy')),bool(set(keys)&set('HI'))) if m else None
        if hint in (None,'DATETIME','ISO_DATETIME'):
            m=re.fullmatch(r'(?P<Y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})[ T](?P<H>\d{2}):(?P<M>\d{2})(?::(?P<S>\d{2})(?:\.(?P<f>\d{1,6}))?)?(?P<z>Z|[+-]\d{2}:?\d{2})?',text,re.I)
            if m:return from_parts({k:v for k,v in m.groupdict().items() if v is not None},hint or 'ISO_DATETIME',True,True)
            if hint=='DATETIME':return None
        if hint in (None,'TIME'):
            m=re.fullmatch(r'(?P<H>\d{2}):(?P<M>\d{2})(?::(?P<S>\d{2})(?:\.(?P<f>\d{1,6}))?)?(?P<z>Z|[+-]\d{2}:?\d{2})?',text,re.I)
            if not m:m=re.fullmatch(r'(?P<I>\d{1,2}):(?P<M>\d{2})(?::(?P<S>\d{2})(?:\.(?P<f>\d{1,6}))?)?\s*(?P<p>AM|PM)',text,re.I)
            if m:return from_parts({k:v for k,v in m.groupdict().items() if v is not None},'TIME',False,True)
            if hint=='TIME':return None
        from .parsing import parse_date
        old=parse_date(text,hint)
        if old:return {**old,'kind':'date','canonical':old['date'],'clock_basis':'calendar','precision':old.get('precision','day')}
    except (ValueError,OverflowError):return None
    return None
