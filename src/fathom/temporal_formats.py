"""Portable explicit local temporal readings. Never infer a date or convert an offset."""
from datetime import date,time
from functools import lru_cache
import re
import math

BUILTINS=('ISO','ISO_DATETIME','MON_D_Y','MDY','DMY','YEAR','TIME','DATETIME')
MONTHS=('january','february','march','april','may','june','july','august','september','october','november','december')
TOKENS={'Y':r'\d{4}','y':r'\d{2}','m':r'\d{1,2}','d':r'\d{1,2}','b':r'[A-Za-z]{3}','B':r'[A-Za-z]+','H':r'\d{1,2}','I':r'\d{1,2}','M':r'\d{2}','S':r'\d{2}','f':r'\d{1,6}','F':r'\d+','p':r'AM|PM','z':r'Z|[+-]\d{2}:?\d{2}'}

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
    keys=set(seen);dated=bool(keys&set('YymdbB'));clock=bool(keys&set('HIMSFfpz'))
    if dated:
        for choices,label in [(set('Yy'),'%Y or %y'),(set('mbB'),'%m or %b or %B'),({'d'},'%d')]:
            if len(keys&choices)!=1:raise ValueError('date_format requires exactly one '+label+' (use YEAR for year-only values)')
    if clock:
        if len(keys&set('HI'))!=1:raise ValueError('date_format clock requires exactly one %H or %I')
        if ('I' in keys)!=('p' in keys):raise ValueError('date_format %I requires %p, and %p requires %I')
        for token in ('f','F'):
            if token in keys and 'S' not in keys:raise ValueError('date_format %'+token+' requires %S')
        if {'f','F'} <= keys:raise ValueError('date_format %f and %F are mutually exclusive')
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


def from_parts(fields,fmt,has_date,has_clock,frame_rate=None):
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
    if 'F' in fields:
        raw=fields['F']
        integer=raw.lstrip('0') or '0'
        if len(integer)>16 or int(integer)>9007199254740991:raise ValueError('frame_not_safe_integer')
        frame=int(integer)
        if frame>=frame_rate:raise ValueError('frame_at_or_above_rate')
        out['fourth_field']={'kind':'frame','raw':raw,'frame':frame,'frame_rate':frame_rate}
        out['precision']='frame'
        out['canonical']+=' [frame '+str(frame)+']'
    if d:out['date']=d
    if clock:out.update(time=clock,hour=t.hour,minute=t.minute,second=t.second,microsecond=t.microsecond,fractional_digits=len(fields.get('f','')))
    if 'F' in fields:
        out.pop('microsecond',None);out.pop('fractional_digits',None)
    return out


def validate_declaration(hint=None,frame_rate=None):
    if hint is not None:validate_format(hint)
    frames=hint not in (None,*BUILTINS) and any(k=='token' and v=='F' for k,v in pattern_parts(hint))
    if frames:
        try:valid=type(frame_rate) in (int,float) and math.isfinite(frame_rate) and frame_rate>0
        except OverflowError:valid=False
        if not valid:raise ValueError('date_format %F requires a positive finite frame_rate')
    elif frame_rate is not None:raise ValueError('frame_rate requires date_format %F; TIME does not declare the fourth field')
    return frame_rate


def pattern_fields(value,hint):
    regex=''
    for kind,part in pattern_parts(hint):
        regex+=re.escape(part) if kind=='literal' else '(?P<'+part+'>'+TOKENS[part]+')'
    match=re.fullmatch(regex,value.strip(),re.I|re.ASCII)
    return match.groupdict() if match else None


def temporal_fault(value,hint=None,frame_rate=None):
    validate_declaration(hint,frame_rate)
    if hint not in (None,*BUILTINS) and isinstance(value,str):
        fields=pattern_fields(value,hint)
        if fields and 'F' in fields:
            raw=fields['F']
            integer=raw.lstrip('0') or '0'
            if len(integer)>16 or int(integer)>9007199254740991:return {'code':'frame_not_safe_integer','message':'Frame field exceeds the portable safe-integer range'}
            if int(integer)>=frame_rate:return {'code':'frame_at_or_above_rate','message':'Frame '+raw+' is at or above declared frame_rate','frame_rate':frame_rate}
    return None if parse_temporal(value,hint,frame_rate) else {'code':'format_mismatch','message':'Value does not match the declared format or field ranges'}


def parse_temporal(value,hint=None,frame_rate=None):
    """A local reading; invalid values return None, invalid patterns raise ValueError."""
    validate_declaration(hint,frame_rate)
    if not isinstance(value,str):
        if hint=='YEAR' and isinstance(value,int) and not isinstance(value,bool):value=str(value)
        else:return None
    text=value.strip()
    try:
        if hint is not None and hint not in BUILTINS:
            fields=pattern_fields(text,hint)
            return from_parts(fields,hint,bool(set(fields)&set('Yy')),bool(set(fields)&set('HI')),frame_rate) if fields else None
        if hint in (None,'DATETIME','ISO_DATETIME'):
            m=re.fullmatch(r'(?P<Y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})[ T](?P<H>\d{2}):(?P<M>\d{2})(?::(?P<S>\d{2})(?:\.(?P<f>\d{1,6}))?)?(?P<z>Z|[+-]\d{2}:?\d{2})?',text,re.I|re.ASCII)
            if m:return from_parts({k:v for k,v in m.groupdict().items() if v is not None},hint or 'ISO_DATETIME',True,True)
            if hint=='DATETIME':return None
        if hint in (None,'TIME'):
            m=re.fullmatch(r'(?P<h>\d{1,2}):(?P<M>\d{2}):(?P<S>\d{2}):(?P<fourth>\d+)\s*(?P<p>AM|PM)?',text,re.I|re.ASCII)
            if m:
                fields={('I' if m['p'] else 'H'):m['h'],'M':m['M'],'S':m['S']}
                if m['p']:fields['p']=m['p']
                out=from_parts(fields,'TIME',False,True)
                out['fourth_field']={'kind':'undeclared','raw':m['fourth']}
                out.pop('microsecond',None);out.pop('fractional_digits',None)
                return out
            m=re.fullmatch(r'(?P<H>\d{2}):(?P<M>\d{2})(?::(?P<S>\d{2})(?:\.(?P<f>\d{1,6}))?)?(?P<z>Z|[+-]\d{2}:?\d{2})?',text,re.I|re.ASCII)
            if not m:m=re.fullmatch(r'(?P<I>\d{1,2}):(?P<M>\d{2})(?::(?P<S>\d{2})(?:\.(?P<f>\d{1,6}))?)?\s*(?P<p>AM|PM)',text,re.I|re.ASCII)
            if m:return from_parts({k:v for k,v in m.groupdict().items() if v is not None},'TIME',False,True)
            if hint=='TIME':return None
        from .parsing import parse_date
        old=parse_date(text,hint)
        if old:return {**old,'kind':'date','canonical':old['date'],'clock_basis':'calendar','precision':old.get('precision','day')}
    except (ValueError,OverflowError):return None
    return None
