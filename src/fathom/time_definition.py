"""Stored-sample field evidence and an explicit, offline format-definition card."""
from html import escape
import json
import re

ROLES=[('literal','Literal / ignore (exact text)'),('Y','Year (4 digits)'),('y','Year (2 digits)'),('m','Month (number)'),('b','Month (abbreviation)'),('B','Month (full name)'),('d','Day'),('H','Hour (24-hour)'),('I','Hour (12-hour)'),('M','Minute'),('S','Second'),('f','Fraction (decimal)'),('F','Frame index'),('p','AM/PM'),('z','UTC offset')]


def lexical_fields(text):
    """Keep separators; signed offsets are a field only after a clock prefix."""
    fields=[];before='';i=0
    while i<len(text):
        offset=re.match(r'[+-][0-9]{2}:?[0-9]{2}',text[i:]) if ':' in text[:i] else None
        value=offset or re.match(r'[A-Za-z]+|[0-9]+',text[i:])
        if value:
            fields.append({'raw':value[0],'before':before});before='';i+=len(value[0])
        else:before+=text[i];i+=1
    return {'fields':fields,'trailing':before}


def definition_fields(samples):
    rows=[lexical_fields(s['raw']) for s in samples if not s.get('truncated') and isinstance(s['raw'],str)]
    if not rows:return {'fields':[],'trailing':'','aligned_samples':0,'total_samples':0}
    base=rows[0]
    aligned=[r for r in rows if len(r['fields'])==len(base['fields']) and [f['before'] for f in r['fields']]==[f['before'] for f in base['fields']] and r['trailing']==base['trailing']]
    for i,field in enumerate(base['fields']):
        values=[r['fields'][i]['raw'] for r in aligned];numeric=all(re.fullmatch('[0-9]+',v) and len(v)<=15 for v in values)
        ordered=sorted(values,key=int if numeric else str)
        field['evidence']={'min':int(ordered[0]) if numeric else ordered[0],'max':int(ordered[-1]) if numeric else ordered[-1],'numeric':numeric,'count':len(values)}
    return {**base,'aligned_samples':len(aligned),'total_samples':len(rows)}


def definition_pattern(definition,roles):
    if len(roles)!=len(definition['fields']):raise ValueError('Select one role for each sample field')
    result=''
    allowed={k for k,_ in ROLES}
    for f,role in zip(definition['fields'],roles):
        if role not in allowed:raise ValueError('Unknown time field role')
        result+=f['before'].replace('%','%%')+(f['raw'].replace('%','%%') if role=='literal' else '%'+role)
    return result+definition['trailing'].replace('%','%%')


def render_definition(index,picker):
    d=picker['definition'];out=[f'<details class="time-definition" data-definition="{index}"><summary>Define time fields</summary>',
        '<p>Choose what each field means, then Use this format. No roles are accepted automatically. Literal / ignore matches the sample text exactly, not a wildcard.</p>',
        '<p>'+str(d['aligned_samples'])+'/'+str(d['total_samples'])+' stored samples align with this field layout. Min/max describe aligned samples only; other layouts may fail the generated pattern.</p>',
        '<div class="table-scroll"><table class="definition-fields"><thead><tr><th>Sample field (in order)</th><th>Role</th><th>Observed min / max</th></tr></thead><tbody>']
    for j,f in enumerate(d['fields']):
        evidence=f['evidence'];hint=''
        if evidence['numeric']:
            maximum=evidence['max']
            hint=(' If frames: above 29 rules out common 24/25/30 fps, not higher rates.' if maximum>29 else ' If frames: max 23 or 29 fits some common rates; it establishes neither frames nor fractions.' if maximum in (23,29) else '')
        out.append('<tr><td><span class="muted">'+escape(f['before'])+'</span><code>'+escape(f['raw'])+'</code></td><td><label>Field '+str(j+1)+f' role <select data-time-role="{j}">'+''.join('<option value="'+k+'">'+escape(label)+'</option>' for k,label in ROLES)+'</select></label></td><td>'+escape(str(evidence['min']))+' / '+escape(str(evidence['max']))+'<small class="frame-hint">'+escape(hint)+'</small></td></tr>')
    out.append('</tbody></table></div><p class="definition-live" hidden><label>Frame rate (frames per second; declaration required for frame fields) <input data-definition-rate type="number" min="0" step="any"></label></p>'
               '<p>Generated pattern: <code class="definition-pattern">Choose field roles</code></p><p class="definition-result" aria-live="polite">With scripts off, use the token list below to declare a pattern in YAML.</p>'
               '<div class="definition-live" hidden><div class="table-scroll"><table class="definition-values"><thead><tr><th>Raw sample</th><th>Parsed value / named fault</th></tr></thead><tbody>')
    for sample in picker['samples']:out.append('<tr><td><code>'+escape(sample['raw'])+'</code></td><td class="definition-preview">Choose roles</td></tr>')
    out.append('</tbody></table></div><button type="button" data-use-definition disabled>Use this format</button></div>'
               '<details><summary>Field tokens and terminal fallback</summary><p>'+escape('; '.join(label+': %'+token for token,label in ROLES if token!='literal'))+'</p>'
               '<p><code>%F</code> is this portable grammar’s frame token, not POSIX’s date shorthand. <code>%f</code> is 1–6 decimal digits, even after a colon: 07 → .07 seconds. Frame indices are zero-based and must be below the declared rate.</p>'
               '<pre>columns:\n  COLUMN:\n    type: temporal\n    date_format: "%I:%M:%S:%F %p"\n    frame_rate: 24</pre>'
               '<p>For decimal fractions use <code>%f</code> and omit frame_rate. Run <code>guide profile DATA.csv --config fathom.yaml --out report</code>. Nothing is inferred from a sample maximum.</p></details></details>')
    return ''.join(out)


DEFINITION_JS='const TEMPORAL_ROLES='+json.dumps([k for k,_ in ROLES])+';'+r'''
function definitionPattern(definition,roles){
 if(roles.length!==definition.fields.length){throw Error('Select one role for each sample field');}
 const literal=s=>s.replace(/%/g,'%%');
 return definition.fields.map((f,i)=>{const role=roles[i];if(!TEMPORAL_ROLES.includes(role)){throw Error('Unknown time field role');}return literal(f.before)+(role==='literal'?literal(f.raw):'%'+role);}).join('')+literal(definition.trailing);
}
'''

DEFINITION_UI_JS=r'''
document.querySelectorAll('[data-definition]').forEach(box=>{
 const i=Number(box.dataset.definition),picker=schema.columns[i].temporal_picker,d=picker.definition;
 const card=box.closest('[data-picker]'),canonical=card.querySelector('[data-field="date_format"]'),canonicalRate=card.querySelector('[data-field="frame_rate"]');
 const rate=box.querySelector('[data-definition-rate]'),use=box.querySelector('[data-use-definition]');
 let draft=null;
 box.querySelectorAll('.definition-live').forEach(el=>{el.hidden=false;});
 function preview(){
  const roles=Array.from(box.querySelectorAll('[data-time-role]')).map(el=>el.value),frames=roles.includes('F');rate.parentElement.hidden=!frames;
  box.querySelectorAll('[data-time-role]').forEach(el=>{const hint=el.closest('tr').querySelector('.frame-hint');if(hint){hint.hidden=!['F','literal'].includes(el.value);}});
  const fps=frames&&rate.value!==''?Number(rate.value):null;
  let pattern=definitionPattern(d,roles),error='',matched=0;
  box.querySelector('.definition-pattern').textContent=pattern||'(no sample fields)';
  try{temporalDeclaration(pattern,fps);}catch(e){error=e.message;}
  const cells=box.querySelectorAll('.definition-preview');
  picker.samples.forEach((sample,j)=>{
   let p=null,fault=null;if(!error&&!sample.truncated){p=temporalParse(sample.raw,pattern,fps);if(!p){fault=temporalFault(sample.raw,pattern,fps);}}
   if(p){matched++;}
   cells[j].textContent=sample.truncated?'Truncated; excluded':error?'Invalid declaration':p?p.canonical+' ['+p.clock_basis+']':fault.code+': '+fault.message;
  });
  box.querySelector('.definition-result').textContent=error||matched+'/'+picker.denominator+' shown samples match; failures are retained, not repaired';
  draft=error?null:{pattern:pattern,rate:fps};use.disabled=!!error;
 }
 box.querySelectorAll('[data-time-role], [data-definition-rate]').forEach(el=>{el.addEventListener('input',preview);el.addEventListener('change',preview);});
 use.addEventListener('click',()=>{if(!draft){return;}canonicalRate.value=draft.rate===null?'':String(draft.rate);canonical.value=draft.pattern;
  canonicalRate.dispatchEvent(new Event('input',{bubbles:true}));canonical.dispatchEvent(new Event('input',{bubbles:true}));
  box.querySelector('.definition-result').textContent+='; format applied to YAML';
 });preview();
});
'''
