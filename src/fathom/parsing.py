"""Local, explicit parses; raw values and ambiguous readings remain available."""

from datetime import date
import math
import re

MONTH_NAMES = ('january','february','march','april','may','june','july','august','september','october','november','december')
MONTH_LOOKUP = {name:i+1 for i,name in enumerate(MONTH_NAMES)} | {name[:3]:i+1 for i,name in enumerate(MONTH_NAMES)}
DATE_FORMATS = {'ISO','MON_D_Y','MDY','DMY'}


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
    if not isinstance(value,str): return None
    text=value.strip(); two=False; alternatives=[]
    try:
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}',text) and hint in (None,'ISO'):
            parsed=date.fromisoformat(text); fmt='ISO'
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
