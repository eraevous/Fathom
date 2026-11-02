"""Local syntax/range checks, not allocation, ownership or sensitive-data classification."""

from collections import Counter
import ipaddress
import re
from urllib.parse import urlsplit

from .parsing import finite_number, parse_date

SPECIAL_TYPES={'phone','email','url','latitude','longitude'}


def host_valid(host):
    try:ipaddress.ip_address(host);return True
    except ValueError:pass
    return bool(host and len(host)<=253 and '.' in host and all(re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?',part) for part in host.split('.')))


def email_domain(value):
    if value.count('@')!=1:return None
    local,domain=value.rsplit('@',1)
    if not local or len(local)>64 or local.startswith('.') or local.endswith('.') or '..' in local:return None
    if not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+",local) or not host_valid(domain):return None
    return domain.casefold()


def url_domain(value):
    try:
        parsed=urlsplit(value)
        if parsed.scheme.casefold() not in {'http','https'} or not parsed.hostname or any(c.isspace() for c in value):return None
        if parsed.port is not None and not 1<=parsed.port<=65535:return None
        return parsed.hostname.casefold() if host_valid(parsed.hostname) else None
    except ValueError:return None


def phone_digits(value):
    if not re.fullmatch(r'\+?[0-9().\s-]+',value):return None
    digits=''.join(c for c in value if c.isdigit())
    return digits if 7<=len(digits)<=15 else None


def infer_special(values,name):
    key=name.casefold().replace('-','_')
    for typ,pattern in [('latitude',r'(^|_)(lat|latitude)($|_)'),('longitude',r'(^|_)(lon|lng|longitude)($|_)'),('email',r'email|e_mail'),('url',r'url|website|web_site'),('phone',r'phone|telephone|mobile')]:
        if re.search(pattern,key):return typ,'Column name suggests this special type; recognition is inferred and does not establish domain meaning.'
    if len(values)>=3:
        for typ,check in [('email',email_domain),('url',url_domain),('phone',phone_digits)]:
            # Plain numeric measurements alone are not enough to infer a phone number.
            score=sum(bool(check(v)) and (typ!='phone' or (any(c in v for c in '+()-') and parse_date(v) is None)) for v in values)
            if score/len(values)>=.8:return typ,'At least 80% of >=3 observed strings match the local special-format rule; alternatives remain possible.'
    return None


def enrich_special(columns,rows,emit):
    for i,col in enumerate(columns):
        typ=col['effective_type']
        if typ not in SPECIAL_TYPES:continue
        name=col['name'];values=[r[i] for r in rows if r[i] is not None]
        invalid=[];placeholders=[];tests=[];domains=Counter()
        for value in values:
            if typ=='phone':
                digits=phone_digits(value)
                if not digits:invalid.append(value)
                elif len(set(digits))==1:placeholders.append(value)
            elif typ=='email':
                domain=email_domain(value)
                if domain is None:invalid.append(value)
                else:
                    domains[domain]+=1
                    local=value.rsplit('@',1)[0].casefold()
                    if re.fullmatch(r'(test|dummy|sample)(?:[+._-]?\d+)?',local) or domain in {'test.com','test.test'}:tests.append(value)
            elif typ=='url':
                domain=url_domain(value)
                if domain is None:invalid.append(value)
                else:domains[domain]+=1
            else:
                number=finite_number(value);bound=90 if typ=='latitude' else 180
                if number is None or not -bound<=number<=bound:invalid.append(value)
        policy={'phone':'Optional leading + and common punctuation; 7..15 digits; no regional allocation or extensions.',
                'email':'Practical unquoted ASCII local part and dotted host; no existence/deliverability lookup.',
                'url':'HTTP(S) structure and host/port syntax only; no DNS/access/content lookup.',
                'latitude':'Independent range [-90,90], degrees inferred unless supplied; no coordinate-system verification.',
                'longitude':'Independent range [-180,180], degrees inferred unless supplied; no coordinate-system verification.'}[typ]
        stats={'policy':policy,'valid':len(values)-len(invalid),'invalid':len(invalid),'invalid_examples':list(dict.fromkeys(invalid))[:5],
               'placeholders':len(placeholders),'placeholder_examples':list(dict.fromkeys(placeholders))[:5],
               'test_values':len(tests),'test_examples':list(dict.fromkeys(tests))[:5],
               'domains':[{'value':d,'count':n} for d,n in sorted(domains.items(),key=lambda x:(-x[1],x[0]))[:10]],
               'recognition':'human override' if col['override'] else 'inferred','generator':'rule:special-v1'}
        col['special']=stats
        if domains:col['univariate']['charts'].append({'kind':'bar','title':f'Most common {typ} domains in {name}','x_label':'Values (count)','y_label':'Domain','data':[{'label':d['value'],'count':d['count']} for d in stats['domains']]})
        for rule,count,examples,message in [('special_invalid',len(invalid),stats['invalid_examples'],'do not match the local syntax/range policy'),('phone_placeholder',len(placeholders),stats['placeholder_examples'],'match repeated-digit placeholder patterns'),('test_email',len(tests),stats['test_examples'],'match test-like address patterns')]:
            if not count:continue
            fid=f's-{i}-{rule}'
            emit(fid,'observation',f'{name}: {count}/{len(values)} nonmissing values {message}.',
                 [{'path':f'columns.{i}.special','value':{'count':count,'nonmissing':len(values),'examples':examples,'policy':policy}}],
                 'Local format/range evidence only; inferred type/units may be wrong and existence is not checked.','rule:special-v1',rule=rule,columns=[name])
            if rule in {'phone_placeholder','test_email'}:
                emit(fid+'-hypothesis','hypothesis',f'The flagged values in {name} may be placeholders or test entries.',[{'finding':fid}],
                     'Pattern matching is not confirmation of a fake or unusable value.','rule:special-v1',rule=rule,columns=[name])
            emit(fid+'-review','action',f'Confirm the type, units and flagged values in {name}; do not correct them automatically.',[{'finding':fid}],
                 'Review suggestion, not a verified defect or a sensitive-data classification.','rule:special-v1',rule=rule,columns=[name])
