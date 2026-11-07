"""Stored-sample format picker shared by configure and liftoff; no I/O or network."""
from html import escape
import json
import re
from .temporal_formats import BUILTINS,TOKENS,MONTHS,parse_temporal,pattern_parts
from .time_definition import definition_fields,render_definition,DEFINITION_JS,DEFINITION_UI_JS


def picker_schema(doc,index,declared=None):
    c=doc['columns'][index];samples=[];seen=set();windows=doc.get('samples',{})
    for kind in ['first','last','random']:
        for row in windows.get(kind,[]):
            if row['position'] in seen:continue
            seen.add(row['position']);v=row['values'][index]
            if v is None:continue
            samples.append({'position':row['position'],'raw':v,'truncated':str(v).endswith('… [truncated]')})
            if len(samples)>=20:break
        if len(samples)>=20:break
    source='stored sample rows; at most 20 positions, repeats retained'
    if not samples:
        source='stored examples only; configured sample rows unavailable'
        samples=[{'position':None,'raw':v,'truncated':False} for v in c.get('examples',[])[:20]]
    valid=[s['raw'] for s in samples if not s['truncated']]
    formats=sorted([{'format':fmt,'matches':sum(parse_temporal(v,fmt) is not None for v in valid)} for fmt in BUILTINS],key=lambda f:(-f['matches'],f['format']))
    prefixes=[v.split(' ',1)[0].split('T',1)[0] for v in valid]
    candidate_prefix=any(parse_temporal(v,fmt) is not None for v in prefixes for fmt in ['MDY','DMY','ISO']) or any(re.fullmatch(r'\d{1,2}[/-]\d{1,2}',v) for v in prefixes)
    if not (declared or c['effective_type']=='temporal' or any(f['matches'] for f in formats) or candidate_prefix):return None
    ambiguity=[]
    for v in valid:
        short=re.match(r'^(\d{1,2})[/-](\d{1,2})(?:\D|$)',v)
        if short and 1<=int(short[1])<=12 and 1<=int(short[2])<=12 and int(short[1])!=int(short[2]):ambiguity.append(v)
        a,b=parse_temporal(v,'MDY'),parse_temporal(v,'DMY')
        if a and b and a['date']!=b['date'] and v not in ambiguity:ambiguity.append(v)
        # Custom date/time samples can carry the same ambiguous numeric prefix.
        prefix=v.split(' ',1)[0].split('T',1)[0]
        a,b=parse_temporal(prefix,'MDY'),parse_temporal(prefix,'DMY')
        if a and b and a['date']!=b['date'] and v not in ambiguity:ambiguity.append(v)
    resolved_fourth=declared not in (None,*BUILTINS) and any(k=='token' and v in {'f','F'} for k,v in pattern_parts(declared))
    return {'samples':samples,'formats':formats,'denominator':len(valid),'basis':source+'; match rate is displayed samples only; truncated cells excluded',
            'definition':definition_fields(samples),'fourth_ambiguity':[] if resolved_fourth else [v for v in valid if (parse_temporal(v,'TIME') or {}).get('fourth_field',{}).get('kind')=='undeclared'],'ambiguity':ambiguity,'available_note':f'{len(samples)} stored sample values available (10–20 shown when available)'}


# Pure functions also belong in YAML_JS so Node and the UI share the same contract.
PARSER_JS='const TEMPORAL_TOKENS='+json.dumps(TOKENS)+';const TEMPORAL_BUILTINS='+json.dumps(BUILTINS)+';const TEMPORAL_MONTHS='+json.dumps(MONTHS)+';'+r'''
function temporalParts(pattern){
 if(typeof pattern!=='string'||!pattern){throw Error('date_format must be a built-in name or a nonempty pattern');}
 let parts=[],keys=[];
 for(let i=0;i<pattern.length;i++){
  if(pattern[i]!=='%'){parts.push(['literal',pattern[i]]);continue;}
  let token=pattern.slice(i,i+2);i++;
  if(token==='%%'){parts.push(['literal','%']);continue;}
  if(token.length!==2||!Object.prototype.hasOwnProperty.call(TEMPORAL_TOKENS,token[1])){throw Error('unsupported date_format token '+token);}
  if(keys.includes(token[1])){throw Error('duplicate date_format token '+token);}
  keys.push(token[1]);parts.push(['token',token[1]]);
 }
 const has=chars=>keys.some(k=>chars.includes(k)),count=chars=>keys.filter(k=>chars.includes(k)).length;
 if(has('YymdbB')){for(const pair of [['Yy','%Y or %y'],['mbB','%m or %b or %B'],['d','%d']]){if(count(pair[0])!==1){throw Error('date_format requires exactly one '+pair[1]+' (use YEAR for year-only values)');}}}
 if(has('HIMSFfpz')){
  if(count('HI')!==1){throw Error('date_format clock requires exactly one %H or %I');}
  if(has('I')!==has('p')){throw Error('date_format %I requires %p, and %p requires %I');}
  for(const token of ['f','F']){if(has(token)&&!has('S')){throw Error('date_format %'+token+' requires %S');}}
  if(has('f')&&has('F')){throw Error('date_format %f and %F are mutually exclusive');}
 }
 if(!has('YymdbBHIMSFfpz')){throw Error('date_format requires date or clock tokens, such as %Y or %H');}
 return parts;
}
function temporalValidate(pattern){if(typeof pattern!=='string'){throw Error('date_format must be text');}if(!TEMPORAL_BUILTINS.includes(pattern)){temporalParts(pattern);}return pattern;}
function temporalDeclaration(fmt,rate){
 if(fmt!==null&&fmt!==undefined){temporalValidate(fmt);}
 const frames=fmt&&!TEMPORAL_BUILTINS.includes(fmt)&&temporalParts(fmt).some(p=>p[0]==='token'&&p[1]==='F');
 if(frames){if(typeof rate!=='number'||!Number.isFinite(rate)||rate<=0){throw Error('date_format %F requires a positive finite frame_rate');}}
 else if(rate!==null&&rate!==undefined){throw Error('frame_rate requires date_format %F; TIME does not declare the fourth field');}
 return rate;
}
function temporalEscape(s){return s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');}
function temporalReadParts(f,fmt,dated,clock,rate){
 const two=f.y!==undefined;let day=null,t=null,basis='calendar',precision='day';
 const pad=(n,size=2)=>String(n).padStart(size,'0');
 if(dated){
  let y=Number(f.Y===undefined?f.y:f.Y);if(two){y+=y>=69?1900:2000;}
  let m=f.m===undefined?TEMPORAL_MONTHS.findIndex(v=>(f.b===undefined?v:v.slice(0,3))===(f.b||f.B||'').toLowerCase())+1:Number(f.m),d=Number(f.d);
  let days=[31,(y%4===0&&(y%100!==0||y%400===0))?29:28,31,30,31,30,31,31,30,31,30,31];
  if(y<1||y>9999||m<1||m>12||d<1||d>days[m-1]){return null;}
  day=pad(y,4)+'-'+pad(m)+'-'+pad(d);
 }
 if(clock){
  let h=Number(f.H===undefined?f.I:f.H),m=Number(f.M||0),s=Number(f.S||0);
  if(f.I!==undefined){if(h<1||h>12){return null;}h=h%12+(f.p.toUpperCase()==='PM'?12:0);}
  if(h<0||h>23||m>59||s>59){return null;}
  const micro=(f.f||'').padEnd(6,'0');t=pad(h)+':'+pad(m)+':'+pad(s)+(Number(micro)?'.'+micro:'');basis='naive';
  if(f.z!==undefined){if(f.z.toUpperCase()==='Z'){basis='+00:00';}else{let z=f.z.replace(':','');if(Number(z.slice(1,3))>23||Number(z.slice(3,5))>59){return null;}basis=z[0]+z.slice(1,3)+':'+z.slice(3,5);}}
  precision=f.f!==undefined?'subsecond':f.S!==undefined?'second':f.M!==undefined?'minute':'hour';
 }
 let out={kind:day&&t?'timestamp':t?'time':'date',format:fmt,canonical:(day&&t?day+'T':day||'')+(t||'')+(t&&basis!=='naive'?basis:''),clock_basis:basis,precision:precision,two_digit_year:two,alternatives:[]};
 if(f.F!==undefined){
  const frame=Number(f.F);if((f.F.replace(/^0+/,'')||'0').length>16||!Number.isSafeInteger(frame)||frame>=rate){return null;}
  out.fourth_field={kind:'frame',raw:f.F,frame:frame,frame_rate:rate};out.precision='frame';out.canonical+=' [frame '+frame+']';
 }
 if(day){out.date=day;}if(t){out.time=t;out.hour=Number(t.slice(0,2));out.minute=Number(t.slice(3,5));out.second=Number(t.slice(6,8));out.microsecond=Number((f.f||'').padEnd(6,'0'));out.fractional_digits=(f.f||'').length;}if(f.F!==undefined){delete out.microsecond;delete out.fractional_digits;}return out;
}
function temporalFields(value,fmt){
 const parts=temporalParts(fmt);let keys=[],regex='';
 parts.forEach(p=>{if(p[0]==='literal'){regex+=temporalEscape(p[1]);}else{keys.push(p[1]);regex+='('+TEMPORAL_TOKENS[p[1]]+')';}});
 const m=new RegExp('^'+regex+'$','i').exec(value);if(!m){return null;}let f={};keys.forEach((k,i)=>{f[k]=m[i+1];});return f;
}
function temporalCustom(value,fmt,rate){const f=temporalFields(value,fmt);return f?temporalReadParts(f,fmt,('Y' in f)||('y' in f),('H' in f)||('I' in f),rate):null;}
function temporalFault(value,fmt,rate){
 temporalDeclaration(fmt,rate);
 if(fmt&&!TEMPORAL_BUILTINS.includes(fmt)&&typeof value==='string'){
  const f=temporalFields(value.trim(),fmt);
  if(f&&f.F!==undefined){
   if((f.F.replace(/^0+/,'')||'0').length>16||!Number.isSafeInteger(Number(f.F))){return {code:'frame_not_safe_integer',message:'Frame field exceeds the portable safe-integer range'};}
   if(Number(f.F)>=rate){return {code:'frame_at_or_above_rate',message:'Frame '+f.F+' is at or above declared frame_rate',frame_rate:rate};}
  }
 }
 return temporalParse(value,fmt,rate)?null:{code:'format_mismatch',message:'Value does not match the declared format or field ranges'};
}
function temporalParse(value,fmt,rate){
 temporalDeclaration(fmt,rate);
 if(fmt===null||fmt===undefined){
  for(const candidate of ['ISO_DATETIME','TIME','ISO','MON_D_Y','MDY','DMY']){let p=temporalParse(value,candidate);if(p){if(candidate==='MDY'){const other=temporalParse(value,'DMY');if(other&&other.date!==p.date){p.alternatives=[other.date];}}return p;}}return null;
 }
 if(typeof value!=='string'){return null;}value=value.trim();
 if(!TEMPORAL_BUILTINS.includes(fmt)){return temporalCustom(value,fmt,rate);}
 let m,out;
 if(fmt==='TIME'){
  m=/^(\d{1,2}):(\d{2}):(\d{2}):(\d+)\s*(AM|PM)?$/i.exec(value);
  if(m){let f={M:m[2],S:m[3]};f[m[5]?'I':'H']=m[1];if(m[5]){f.p=m[5];}out=temporalReadParts(f,'TIME',false,true);if(out){out.fourth_field={kind:'undeclared',raw:m[4]};delete out.microsecond;delete out.fractional_digits;}return out;}
  m=/^(\d{2}):(\d{2})(?::(\d{2})(?:\.(\d{1,6}))?)?(Z|[+-]\d{2}:?\d{2})?$/i.exec(value);
  if(m){let f={H:m[1],M:m[2]};['S','f','z'].forEach((k,i)=>{if(m[i+3]!==undefined){f[k]=m[i+3];}});return temporalReadParts(f,fmt,false,true);}
  m=/^(\d{1,2}):(\d{2})(?::(\d{2})(?:\.(\d{1,6}))?)?\s*(AM|PM)$/i.exec(value);
  if(!m){return null;}let f={I:m[1],M:m[2],p:m[5]};if(m[3]!==undefined){f.S=m[3];}if(m[4]!==undefined){f.f=m[4];}return temporalReadParts(f,fmt,false,true);
 }
 if(fmt==='DATETIME'||fmt==='ISO_DATETIME'){
  m=/^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2})(?:\.(\d{1,6}))?)?(Z|[+-]\d{2}:?\d{2})?$/i.exec(value);if(!m){return null;}
  let f={Y:m[1],m:m[2],d:m[3],H:m[4],M:m[5]};['S','f','z'].forEach((k,i)=>{if(m[i+6]!==undefined){f[k]=m[i+6];}});return temporalReadParts(f,fmt,true,true);
 }
 if(fmt==='YEAR'){if(!/^[0-9]{4}$/.test(value)){return null;}out=temporalReadParts({Y:value,m:'1',d:'1'},fmt,true,false);if(out){out.precision='year';}return out;}
 if(fmt==='ISO'){return /^\d{4}-\d{2}-\d{2}$/.test(value)?temporalCustom(value,'%Y-%m-%d')&&Object.assign(temporalCustom(value,'%Y-%m-%d'),{format:fmt}):null;}
 if(fmt==='MON_D_Y'){
  m=/^([A-Za-z]+)[\s-]+(\d{1,2})[,\s-]+(\d{2}|\d{4})$/.exec(value);if(!m){return null;}let f={d:m[2]};f[m[1].length===3?'b':'B']=m[1];f[m[3].length===2?'y':'Y']=m[3];return temporalReadParts(f,fmt,true,false);
 }
 m=/^(\d{1,2})[\/-](\d{1,2})[\/-](\d{2}|\d{4})$/.exec(value);if(!m){return null;}let f={m:m[fmt==='MDY'?1:2],d:m[fmt==='MDY'?2:1]};f[m[3].length===2?'y':'Y']=m[3];return temporalReadParts(f,fmt,true,false);
}
'''


PARSER_JS += DEFINITION_JS

def render_picker(index,column,control):
    p=column['temporal_picker'];out=[f'<article class="card format-picker" id="format-picker-{index}" data-picker="{index}"><h3>Format for <code>'+escape(column['name'])+'</code></h3>',
        '<p>'+escape(p['available_note']+'; '+p['basis'])+'</p>',control,
        f'<p class="format-live" hidden><label>Built-in formats (ranked by shown sample matches) <select data-format-choice="{index}"><option value="">Choose explicitly</option>'+''.join('<option value="'+escape(f['format'],quote=True)+'">'+escape(f['format'])+f" — {f['matches']}/{p['denominator']} samples</option>" for f in p['formats'])+'</select></label></p>',
        '<p>Examples: <code>%d/%m/%Y %H:%M</code> or <code>%H:%M:%S.%f</code>. Complete dates require year, month and day; UTC offsets stay as written.</p>',
        '<p class="format-result" aria-live="polite">Preview requires JavaScript; declare the chosen format in YAML.</p>']
    out.append(render_definition(index,p))
    if p.get('fourth_ambiguity'):out.append('<p class="format-ambiguity">Undeclared fourth clock field: fraction or frames? First three fields remain usable; declare %f or %F plus frame_rate. No sub-second meaning is guessed.</p>')
    if p['ambiguity']:out.append('<p class="format-ambiguity">Ambiguous day/month: '+escape(', '.join(p['ambiguity'][:3]))+'; MDY and DMY give different dates. Confirm the intended reading.</p>')
    out.append('<details><summary>Available formats and raw samples</summary><p>'+escape(', '.join(f['format']+f" {f['matches']}/{p['denominator']}" for f in p['formats']))+'</p></details><div class="table-scroll"><table><thead><tr><th>Row</th><th>Raw sample</th><th>Parsed local value</th></tr></thead><tbody>')
    for sample in p['samples']:out.append('<tr><td>'+str(sample['position'] or 'example')+'</td><td class="literal-data"><code>'+escape(str(sample['raw']))+'</code></td><td class="format-preview">'+('Truncated; not counted' if sample['truncated'] else 'Choose a format')+'</td></tr>')
    return ''.join(out)+'</tbody></table></div><noscript><p>Formats and samples above work offline. Edit <code>columns: {COLUMN: {type: temporal, date_format: FORMAT}}</code> in YAML, then run <code>guide profile DATA.csv --config fathom.yaml --out report</code>.</p></noscript></article>'


UI_JS=r'''
document.querySelectorAll('[data-picker]').forEach(card=>{
 let i=Number(card.dataset.picker),p=schema.columns[i].temporal_picker,input=card.querySelector('[data-field="date_format"]'),select=card.querySelector('[data-format-choice]'),rateInput=card.querySelector('[data-field="frame_rate"]');
 card.querySelector('.format-live').hidden=false;
 function preview(){let matched=0,error='',fmt=input.value,rate=rateInput.value===''?null:Number(rateInput.value),outputs=card.querySelectorAll('.format-preview');
  rateInput.parentElement.hidden=rateInput.value===''&&!fmt.includes('%F');
  try{temporalDeclaration(fmt||null,rate);}catch(e){error=e.message;}
  p.samples.forEach((s,j)=>{let value=null;if(fmt&&!error&&!s.truncated){value=temporalParse(s.raw,fmt,rate);}if(value){matched++;}outputs[j].textContent=s.truncated?'Truncated; not counted':error?'Invalid pattern':!fmt?'Choose a format':value?value.canonical+' ['+value.clock_basis+']'+(value.fourth_field&&value.fourth_field.kind==='undeclared'?' — fourth field undeclared; excluded from sub-second statistics':''):temporalFault(s.raw,fmt,rate).code;});
  card.querySelector('.format-result').textContent=error||(!fmt?'No format declared; suggestions are not applied':matched+'/'+p.denominator+' shown samples match; no timezone conversion');
 }
 select.addEventListener('change',()=>{rateInput.value='';rateInput.dispatchEvent(new Event('input',{bubbles:true}));input.value=select.value;input.dispatchEvent(new Event('input',{bubbles:true}));});
 rateInput.addEventListener('input',preview);
 input.addEventListener('input',()=>{select.value=TEMPORAL_BUILTINS.includes(input.value)?input.value:'';preview();});preview();
});
'''

UI_JS += DEFINITION_UI_JS
