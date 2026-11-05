"""Local, explicit parses; raw values and ambiguous readings remain available."""

from datetime import date
from numbers import Integral
import math
import re

MONTH_NAMES = ('january','february','march','april','may','june','july','august','september','october','november','december')
MONTH_LOOKUP = {name:i+1 for i,name in enumerate(MONTH_NAMES)} | {name[:3]:i+1 for i,name in enumerate(MONTH_NAMES)}
DATE_FORMATS = {'ISO','ISO_DATETIME','MON_D_Y','MDY','DMY','YEAR'}


def finite_number(value):
    if not isinstance(value,str): return None
    text=value.strip()
    try:
        n=float(text)
        return n if math.isfinite(n) else None
    except (ValueError,OverflowError): pass
    negative=text.startswith('(') and text.endswith(')')
    if negative: text=text[1:-1].strip()
    text=re.sub(r'^([+-]?)\s*[$€£]\s*',r'\1',text)
    if ',' in text:
        if not re.fullmatch(r'[+-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?',text): return None
        text=text.replace(',','')
    if not re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?',text): return None
    try:
        n=float(text)*(-1 if negative else 1)
        return n if math.isfinite(n) else None
    except (ValueError,OverflowError): return None


def parse_date(value, hint=None):
    if hint=='YEAR':
        if isinstance(value,Integral) and not isinstance(value,bool):value=str(value)
        if not isinstance(value,str) or not re.fullmatch(r'[0-9]{4}',value.strip()):return None
        try:parsed=date(int(value.strip()),1,1)
        except ValueError:return None
        return {'date':parsed.isoformat(),'format':'YEAR','precision':'year','two_digit_year':False,'alternatives':[]}
    if not isinstance(value,str): return None
    text=value.strip(); two=False; alternatives=[]
    try:
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}',text) and hint in (None,'ISO'):
            parsed=date.fromisoformat(text); fmt='ISO'
        elif hint in (None,'ISO_DATETIME') and (match:=re.fullmatch(r'(\d{4}-\d{2}-\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?',text)):
            # Calendar date of a strict ISO date-time; the time of day is not profiled.
            if int(match[2])>23 or int(match[3])>59 or int(match[4] or 0)>59: return None
            parsed=date.fromisoformat(match[1]); fmt='ISO_DATETIME'
        elif hint in (None,'MON_D_Y') and (match:=re.fullmatch(r'([A-Za-z]+)[\s-]+(\d{1,2})[,\s-]+(\d{2}|\d{4})',text)):
            month=MONTH_LOOKUP.get(match[1].casefold())
            if month is None: return None
            year=int(match[3]);two=len(match[3])==2
            if two: year+=1900 if year>=69 else 2000
            parsed=date(year,month,int(match[2]));fmt='MON_D_Y'
        elif hint in (None,'MDY','DMY') and (match:=re.fullmatch(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2}|\d{4})',text)):
            a,b,year=int(match[1]),int(match[2]),int(match[3]);two=len(match[3])==2
            if two: year+=1900 if year>=69 else 2000
            options=[]
            for fmt,month,day in [('MDY',a,b),('DMY',b,a)]:
                try: options.append((fmt,date(year,month,day)))
                except ValueError: pass
            if hint: options=[x for x in options if x[0]==hint]
            if not options: return None
            fmt,parsed=options[0]
            alternatives=sorted({v.isoformat() for _,v in options if v!=parsed})
        else: return None
        return {'date':parsed.isoformat(),'format':fmt,'two_digit_year':two,'alternatives':alternatives}
    except (ValueError,OverflowError): return None


def parse_datetime(value):
    """Strict ISO date or date-time -> (datetime, has_time); used for row-level time checks only."""
    from datetime import datetime
    if not isinstance(value,str): return None
    text=value.strip()
    match=re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?',text)
    if not match: return None
    try:
        return datetime(*(int(x) for x in match.groups(default='0'))), match[4] is not None
    except (ValueError,OverflowError): return None


def temporal_failure(values, hint=None, supported_formats=None):
    """Diagnose a wholly failed declaration; never apply another parse implicitly."""
    values=[v for v in values if v is not None]
    if not values or any(parse_date(v,hint) is not None for v in values):return None
    supported=DATE_FORMATS if supported_formats is None else supported_formats
    tried=[hint] if hint else sorted(supported-{'YEAR'})
    counts={fmt:sum(parse_date(v,fmt) is not None for v in values) for fmt in sorted(supported)}
    best=max(counts.values(),default=0)
    return {'nonmissing':len(values),'formats_tried':tried,'format_matches':counts,
            'suggested_formats':[fmt for fmt,n in counts.items() if n==best and best>0],
            'best_matches':best,'selection':'greatest supported-format parse count; ties retained; no fallback applied'}


def temporal_failure_message(name, failure, include_advice=True):
    text=f"{name}: all {failure['nonmissing']} nonmissing values failed temporal parsing. Formats tried: "+', '.join(failure['formats_tried'])+'. '
    choices=failure['suggested_formats']
    if choices:
        text+='Nearest supported format'+('s' if len(choices)>1 else '')+': '+', '.join(choices)+f" ({failure['best_matches']}/{failure['nonmissing']} match). "
        if include_advice:text+=('After confirming meaning, explicitly declare date_format: '+choices[0]+'. ' if len(choices)==1 else 'Choose the intended date_format explicitly. ')
    else:text+='No supported format matches; check the declared type and original values. '
    return text+'No fallback was applied.'
