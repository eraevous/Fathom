"""`guide configure`: a self-contained HTML page that writes a Fathom YAML config (spec012).

The page is built from an ordinary profile (no new analysis). One JSON control schema is
embedded in the page; the YAML generator exists twice, in JavaScript (in the page) and in
Python (`config_yaml`), following the same rules so tests can round-trip without a browser.
The page carries inline JavaScript by design; reports stay script-free.
"""

from collections import Counter
import hashlib
import json
import re
from html import escape
from pathlib import Path

from .presentation import categorical_hint
from .config import BINS_RANGE, OPTIONAL_SECTIONS, validate_config
from .models import TYPES
from .parsing import DATE_FORMATS, parse_date, parse_datetime, parse_temporal
from .rows import RULES as ROW_RULES
from .timeseries import DEFAULT_LAG, GRAINS, MIN_N, TOP_N, undeclared
from .univariate import BIN_RULE
from .temporal_formats import validate_format,validate_declaration
from .temporal_picker import picker_schema,render_picker,PARSER_JS,UI_JS as PICKER_UI_JS
from .palette import theme_css
from .temporal_view import TEMPORAL_CSS
from .renderers import KIND_CSS

CONTROLLED_COLUMN_KEYS = ("type", "date_format", "frame_rate", "exclude_from_target")
TEXT_KEYS = ("question", "row_unit")
INT_KNOBS = {"pair_budget": (5, 0, 20), "sample_rows": (20, 0, 100), "bins": (None, *BINS_RANGE)}
CONTROLLED_KEYS = (*TEXT_KEYS, "target", *INT_KNOBS, "sections", "intervals", "time_series")
KEY_ORDER = ["title", "description", "question", "row_unit", "generating_process", "missingness_mechanism",
             "target", "group_by", "pair_budget", "sample_rows", "sample_seed", "sample_text_limit",
             "bins", "sections", "intervals", "time_series", "columns"]
COLUMN_KEY_ORDER = ["type", "date_format", "frame_rate", "exclude_from_target", "role", "units", "meaning"]
NESTED_KEY_ORDER = ["start", "end", "time", "value", "by", "granularities", "max_lag", "top_n"]
RESERVED = {"y", "yes", "n", "no", "true", "false", "on", "off", "null", "~"}
SUGGEST_SHARE = 0.8
MAX_INTERVAL_PAIRS = 10
MAX_SERIES_SUGGESTIONS = 12
TS_GRANULARITIES = ["auto", *GRAINS]
TS_PASSTHROUGH = ("max_lag", "top_n")  # kept from --config, not offered as controls

FIXED_RULES = [
    {"name": "Target group contrast (numeric)", "rule": "group mean versus rest marked only when the gap is >= the overall population SD of the target", "source": "FT-TA-R1@2 (implements FT-R7@2)"},
    {"name": "Target group contrast (rates, missing share)", "rule": "absolute gap >= 30 percentage points", "source": "FT-TA-R1@2 (implements FT-R7@2)"},
    {"name": "Date parsing", "rule": "two-digit years pivot at 69; ambiguous numeric dates read MDY unless date_format is declared; alternatives kept", "source": "FT-UNI-R1@2 (spec003)"},
    *({"name": "Row structure: " + k.replace("_", " "), "rule": v, "source": "FT-ROW2-R1@2"} for k, v in ROW_RULES.items()),
]
def loader_knows(key: str) -> bool:
    """Whether the installed config loader accepts a top-level key (checked at generation time)."""
    try:
        validate_config({key: None})
        return True
    except ValueError as exc:
        return not str(exc).startswith("config must be a mapping with keys")


EXTENSION_POINTS = [
    {"key": "time_series.max_lag, time_series.top_n", "status": "Not offered: the defaults apply (max_lag " + ", ".join(f"{v} by {k}" for k, v in DEFAULT_LAG.items())
     + f", 52 weeks when the span allows; top_n {TOP_N} groups). Declare them directly in YAML; values from --config are kept."},
    {"key": "time_series for other columns", "status": f"Only temporal columns with at least {MIN_N} distinct periods and numeric columns that are not identifier-like "
     "are offered (the same rule as the report's time-series question). Any other series may be declared directly in YAML."},
    {"key": "exclude (drop a column)", "status": "Not offered: removing a column from profiling would suppress its findings. Use exclude_from_target to keep a column out of target comparisons."},
]


def pct(part: int, whole: int) -> str:
    if not whole: return "0%"
    if part == whole: return "100%"
    return f"{min(part / whole * 100, 99.9):.1f}%"


def build_schema(doc: dict, frame, raw_config: dict | None) -> dict:
    """The control schema: observable facts and suggestions only; no relevance language."""
    raw = dict(raw_config or {})
    rows = doc["overview"]["rows"]
    columns, candidates, temporal = [], [], []
    for i, c in enumerate(doc["columns"]):
        values = [v for v in frame.iloc[:, i].tolist() if v is not None]
        populated = c["count"] - c["missing"]
        typ = c["effective_type"]
        facts = [f"{pct(populated, rows)} populated", f"{c['distinct']} distinct"]
        if categorical_hint(c): facts.append(categorical_hint(c))
        formats = ((c.get("univariate") or {}).get("statistics") or {}).get("parse_formats") if typ == "temporal" else None
        if formats:
            facts.append("parsed date formats: " + ", ".join(f"{k} {v}" for k, v in formats.items()))
        suggestions = []
        if typ != "temporal" and values:
            counts = {fmt: sum(parse_temporal(v, fmt) is not None for v in values) for fmt in sorted(DATE_FORMATS)}
            best = max(counts.values())
            tied = [f for f, n in counts.items() if n == best]
            if best >= SUGGEST_SHARE * len(values):
                reason = f"{best} of {len(values)} nonmissing values ({pct(best, len(values))}) parse as {' or '.join(tied)}"
                suggestions.append({"key": "type", "value": "temporal", "reason": reason})
                if len(tied) == 1:
                    suggestions.append({"key": "date_format", "value": tied[0], "reason": reason})
                else:
                    facts.append("date format ambiguous between " + " and ".join(tied) + "; declare one")
        columns.append({"name": c["name"], "inferred_type": c["inference"]["type"], "effective_type": typ,
                        "override": bool(c.get("override")), "facts": facts, "suggestions": suggestions})
        pick=picker_schema(doc,i,(raw.get('columns',{}).get(c['name']) or {}).get('date_format'))
        if pick:columns[-1]['temporal_picker']=pick
        if typ in {"numeric", "categorical", "boolean"} and populated and not (typ != "numeric" and c["distinct"] == populated):
            candidates.append({"column": c["name"], "reason": f"{typ}; {pct(populated, rows)} populated; {c['distinct']} distinct"})
        if typ == "temporal":
            iso = sum(parse_datetime(v) is not None for v in values)
            temporal.append((c["name"], iso))
    intervals = []
    for a, (sa, ia) in enumerate(temporal):
        for sb, ib in temporal[a + 1:]:
            for start, end in ((sa, sb), (sb, sa)):
                if len(intervals) < 2 * MAX_INTERVAL_PAIRS:
                    intervals.append({"start": start, "end": end, "reason": f"both columns temporal; strict ISO values: {sa} {ia}/{rows}, {sb} {ib}/{rows} (interval checks measure strict ISO only); direction is your declaration"})
    names = [c["name"] for c in columns]
    series, by_options = series_suggestions(doc, frame, raw, names), [c["name"] for c in columns if c["effective_type"] in {"categorical", "boolean"}]
    base = {k: v for k, v in raw.items() if k not in CONTROLLED_KEYS and k != "columns"}
    raw_columns = raw.get("columns") or {}
    base_columns = {n: {k: v for k, v in raw_columns[n].items() if k not in CONTROLLED_COLUMN_KEYS}
                    for n in names if isinstance(raw_columns.get(n), dict)}
    initial = {"question": raw.get("question"), "row_unit": raw.get("row_unit"), "target": raw.get("target"),
               **{k: raw.get(k) for k in INT_KNOBS},
               "sections": {k: (raw.get("sections") or {}).get(k, True) for k in sorted(OPTIONAL_SECTIONS)},
               "intervals": [[i["start"], i["end"]] for i in raw.get("intervals") or []],
               "time_series": [{"time": i["time"], "value": i.get("value"), "by": i.get("by"), "granularities": list(i.get("granularities") or []),
                                **{k: i[k] for k in TS_PASSTHROUGH if i.get(k) is not None}} for i in raw.get("time_series") or []],
               "columns": {n: {k: raw_columns[n][k] for k in CONTROLLED_COLUMN_KEYS if k in raw_columns.get(n, {})} for n in names if isinstance(raw_columns.get(n), dict)}}
    return {"schema_version": 1, "kind": "fathom-configure",
            "dataset": {"file": Path(doc["source"]["origin"]).name, "sha256": doc["source"]["sha256"],
                        "rows": rows, "columns": len(names)},
            "types": sorted(TYPES), "date_formats": sorted(DATE_FORMATS),
            "columns": columns, "target_candidates": candidates, "interval_suggestions": intervals,
            "series_suggestions": series, "by_options": by_options, "ts_granularities": TS_GRANULARITIES,
            "knobs": {k: {"default": d, "min": lo, "max": hi} for k, (d, lo, hi) in INT_KNOBS.items()},
            "bin_rule_default": BIN_RULE,
            "sections": [{"key": k, "title": OPTIONAL_SECTIONS[k], "default": True} for k in sorted(OPTIONAL_SECTIONS)],
            "fixed_rules": FIXED_RULES,
            "extension_points": EXTENSION_POINTS,
            "base": base, "base_columns": base_columns, "initial": initial,
            "key_order": KEY_ORDER, "column_key_order": COLUMN_KEY_ORDER, "nested_key_order": NESTED_KEY_ORDER, "reserved": sorted(RESERVED)}


def series_suggestions(doc: dict, frame, raw: dict, names: list) -> list:
    """Time-series declarations offered unticked, by the report's own undeclared-series rule (spec011), with observable reasons."""
    q = undeclared(frame.values.tolist(), doc["columns"], validate_config(raw, names))
    if not q: return []
    out = []
    for t in q["temporal_columns"]:
        seen = f"{t['column']} is temporal with {t['distinct_periods']:,} distinct {t['granularity']}s (at least {MIN_N}: the report's time-series question rule)"
        out.append({"time": t["column"], "value": None, "reason": seen + "; value null counts rows per period"})
        for v in q["numeric_columns"]:
            out.append({"time": t["column"], "value": v, "reason": seen + f"; {v} is numeric and not identifier-like; its values are summed per period"})
    return out[:MAX_SERIES_SUGGESTIONS]


# ---- YAML generation (mirrored exactly by YAML_JS) ----

def strip_ws(s: str) -> str:
    return re.sub(r"^[ \t\n\r]+|[ \t\n\r]+$", "", s)


def config_document(schema: dict, sel: dict) -> dict:
    out = {k: v for k, v in schema["base"].items()}
    for k in TEXT_KEYS:
        v = sel.get(k)
        if isinstance(v, str) and strip_ws(v): out[k] = strip_ws(v)
    names = [c["name"] for c in schema["columns"]]
    if isinstance(sel.get("target"), str) and sel["target"] in names: out["target"] = sel["target"]
    for k, knob in schema["knobs"].items():
        v = sel.get(k)
        if type(v) is int and knob["min"] <= v <= knob["max"]: out[k] = v
    sections = {s["key"]: False for s in schema["sections"] if (sel.get("sections") or {}).get(s["key"]) is False}
    if sections: out["sections"] = sections
    intervals = [{"start": a, "end": b} for a, b in sel.get("intervals") or [] if a in names and b in names and a != b]
    if intervals: out["intervals"] = intervals
    if "time_series_suggestions" in schema:
        offered = {c["column"] for c in schema["time_series_suggestions"]}
        series = []
        for item in sel.get("time_series") or []:
            time, value, grains = item.get("time"), item.get("value"), item.get("granularities", ["auto"])
            if time in offered and (value is None or value in schema["series_value_options"] and value != time) and isinstance(grains, list) and grains and all(g in ("auto","hour","day","week","month","year") for g in grains):
                series.append({"time": time, "value": value, "granularities": grains})
        if series: out["time_series"] = series
    else:
        series = []
        for item in sel.get("time_series") or []:
            t, v, b = item.get("time"), item.get("value"), item.get("by")
            if t not in names or (v is not None and v not in names): continue
            if b is not None and b not in names: b = None
            if len({t, v, b} - {None}) != len([x for x in (t, v, b) if x is not None]): continue
            entry = {"time": t, "value": v}
            if b is not None: entry["by"] = b
            grains = [g for g in schema["ts_granularities"] if g in (item.get("granularities") or [])]
            if grains: entry["granularities"] = grains
            for k in TS_PASSTHROUGH:
                if type(item.get(k)) is int: entry[k] = item[k]
            series.append(entry)
        if series: out["time_series"] = series
    columns = {}
    for n in names:
        chosen = (sel.get("columns") or {}).get(n) or {}
        entry = {}
        if chosen.get("type") in schema["types"]: entry["type"] = chosen["type"]
        if chosen.get("date_format"): entry["date_format"] = validate_format(chosen["date_format"])
        rate=chosen.get('frame_rate')
        validate_declaration(chosen.get('date_format') or None,rate)
        if rate is not None:entry['frame_rate']=rate
        if chosen.get("exclude_from_target") is True: entry["exclude_from_target"] = True
        for k, v in (schema["base_columns"].get(n) or {}).items(): entry[k] = v
        if entry: columns[n] = entry
    if columns: out["columns"] = columns
    return out


def yaml_string(s: str) -> str:
    out = ['"']
    for ch in s:
        o = ord(ch)
        if ch == '"': out.append('\\"')
        elif ch == "\\": out.append("\\\\")
        elif 0x20 <= o <= 0x7E: out.append(ch)
        elif o <= 0xFFFF: out.append("\\u%04x" % o)
        else: out.append("\\U%08x" % o)
    return "".join(out) + '"'


def yaml_key(k: str, schema: dict) -> str:
    return k if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", k) and k.lower() not in schema["reserved"] else yaml_string(k)


def yaml_scalar(v) -> str:
    if v is None: return "null"
    if v is True: return "true"
    if v is False: return "false"
    if type(v) is int: return str(v)
    if isinstance(v, str): return yaml_string(v)
    if isinstance(v, dict): return "{}"
    if isinstance(v, list): return "[]"
    raise ValueError("configure emits only text, integers, booleans and null")


def ordered_keys(keys: list, path: list, schema: dict) -> list:
    if path == ["columns"]: return list(keys)
    order = schema["column_key_order"] if len(path) == 2 and path[0] == "columns" else schema["key_order"] if not path else schema["nested_key_order"]
    return sorted(keys, key=lambda k: (order.index(k) if k in order else len(order), k))


def yaml_lines(value, indent: int, path: list, schema: dict) -> list:
    pad, lines = " " * indent, []
    if isinstance(value, dict):
        for k in ordered_keys(list(value), path, schema):
            v = value[k]
            if isinstance(v, (dict, list)) and v:
                lines.append(pad + yaml_key(k, schema) + ":")
                lines += yaml_lines(v, indent + 2, path + [k], schema)
            else:
                lines.append(pad + yaml_key(k, schema) + ": " + yaml_scalar(v))
    else:
        for item in value:
            if isinstance(item, (dict, list)) and item:
                sub = yaml_lines(item, indent + 2, path + ["[]"], schema)
                sub[0] = pad + "- " + sub[0][indent + 2:]
                lines += sub
            else:
                lines.append(pad + "- " + yaml_scalar(item))
    return lines


def yaml_digest(text: str) -> str:
    """sha256 of the exact UTF-8 bytes the page's Download produces (mirrored by sha256Hex in YAML_JS)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def config_yaml(schema: dict, sel: dict) -> str:
    doc = config_document(schema, sel)
    return "\n".join(yaml_lines(doc, 0, [], schema)) + "\n" if doc else "{}\n"


YAML_JS = PARSER_JS + r"""
function own(o,k){return o!=null&&Object.prototype.hasOwnProperty.call(o,k)?o[k]:undefined;}
function stripWs(s){return s.replace(/^[ \t\n\r]+|[ \t\n\r]+$/g,'');}
function configDocument(schema,sel){
  var out={};
  Object.keys(schema.base).forEach(function(k){out[k]=schema.base[k];});
  ['question','row_unit'].forEach(function(k){var v=sel[k];if(typeof v==='string'&&stripWs(v)){out[k]=stripWs(v);}});
  var names=schema.columns.map(function(c){return c.name;});
  if(typeof sel.target==='string'&&names.indexOf(sel.target)>=0){out.target=sel.target;}
  Object.keys(schema.knobs).forEach(function(k){var v=sel[k],kn=schema.knobs[k];if(typeof v==='number'&&Number.isInteger(v)&&kn.min<=v&&v<=kn.max){out[k]=v;}});
  var sections={},any=false;
  schema.sections.forEach(function(s){if(own(sel.sections,s.key)===false){sections[s.key]=false;any=true;}});
  if(any){out.sections=sections;}
  var intervals=(sel.intervals||[]).filter(function(p){return names.indexOf(p[0])>=0&&names.indexOf(p[1])>=0&&p[0]!==p[1];}).map(function(p){return {start:p[0],end:p[1]};});
  if(intervals.length){out.intervals=intervals;}
  if(schema.time_series_suggestions){
    var offered=schema.time_series_suggestions.map(function(c){return c.column;});
    var series=(sel.time_series||[]).map(function(item){
      var grains=own(item,'granularities');
      return {time:own(item,'time'),value:own(item,'value'),granularities:grains===undefined?['auto']:grains};
    }).filter(function(item){return offered.indexOf(item.time)>=0&&(item.value==null||(schema.series_value_options.indexOf(item.value)>=0&&item.value!==item.time))&&Array.isArray(item.granularities)&&item.granularities.length&&item.granularities.every(function(g){return ['auto','hour','day','week','month','year'].indexOf(g)>=0;});}).map(function(item){return {time:item.time,value:item.value==null?null:item.value,granularities:item.granularities};});
    if(series.length){out.time_series=series;}
  }
  else{
  var series=[];
  (sel.time_series||[]).forEach(function(item){
    var t=own(item,'time'),v=own(item,'value'),b=own(item,'by');
    if(v===undefined){v=null;} if(b===undefined){b=null;}
    if(names.indexOf(t)<0||(v!==null&&names.indexOf(v)<0)){return;}
    if(b!==null&&names.indexOf(b)<0){b=null;}
    var used=[t,v,b].filter(function(x){return x!==null;});
    if(used.filter(function(x,i){return used.indexOf(x)===i;}).length!==used.length){return;}
    var entry={time:t,value:v};
    if(b!==null){entry.by=b;}
    var g=own(item,'granularities')||[],grains=schema.ts_granularities.filter(function(x){return g.indexOf(x)>=0;});
    if(grains.length){entry.granularities=grains;}
    ['max_lag','top_n'].forEach(function(k){var x=own(item,k);if(typeof x==='number'&&Number.isInteger(x)){entry[k]=x;}});
    series.push(entry);
  });
  if(series.length){out.time_series=series;}
  }
  var columns=new Map();
  names.forEach(function(n){
    var chosen=own(sel.columns,n)||{},entry={},extra=own(schema.base_columns,n)||{};
    if(schema.types.indexOf(chosen.type)>=0){entry.type=chosen.type;}
    if(chosen.date_format){entry.date_format=temporalValidate(chosen.date_format);}
    temporalDeclaration(chosen.date_format||null,chosen.frame_rate);
    if(chosen.frame_rate!==undefined&&chosen.frame_rate!==null){entry.frame_rate=chosen.frame_rate;}
    if(chosen.exclude_from_target===true){entry.exclude_from_target=true;}
    Object.keys(extra).forEach(function(k){entry[k]=extra[k];});
    if(Object.keys(entry).length){columns.set(n,entry);}
  });
  if(columns.size){out.columns=columns;}
  return out;
}
function yamlString(s){
  var out='"';
  for(var ch of s){var o=ch.codePointAt(0);
    if(ch==='"'){out+='\\"';}else if(ch==='\\'){out+='\\\\';}
    else if(o>=0x20&&o<=0x7e){out+=ch;}
    else if(o<=0xffff){out+='\\u'+o.toString(16).padStart(4,'0');}
    else{out+='\\U'+o.toString(16).padStart(8,'0');}}
  return out+'"';
}
function yamlKey(k,schema){return (/^[A-Za-z_][A-Za-z0-9_]*$/.test(k)&&schema.reserved.indexOf(k.toLowerCase())<0)?k:yamlString(k);}
function isMap(v){return v instanceof Map||(v!==null&&typeof v==='object'&&!Array.isArray(v));}
function size(v){return v instanceof Map?v.size:Array.isArray(v)?v.length:Object.keys(v).length;}
function yamlScalar(v){
  if(v===null||v===undefined){return 'null';}
  if(v===true){return 'true';} if(v===false){return 'false';}
  if(typeof v==='number'){return String(v);} if(typeof v==='string'){return yamlString(v);}
  return Array.isArray(v)?'[]':'{}';
}
function orderedKeys(keys,path,schema){
  if(path.length===1&&path[0]==='columns'){return keys;}
  var order=(path.length===2&&path[0]==='columns')?schema.column_key_order:(path.length===0?schema.key_order:schema.nested_key_order);
  function rank(k){var i=order.indexOf(k);return i<0?order.length:i;}
  return keys.slice().sort(function(a,b){return rank(a)-rank(b)||(a<b?-1:a>b?1:0);});
}
function yamlLines(value,indent,path,schema){
  var pad=' '.repeat(indent),lines=[];
  if(isMap(value)){
    var keys=value instanceof Map?Array.from(value.keys()):Object.keys(value);
    orderedKeys(keys,path,schema).forEach(function(k){
      var v=value instanceof Map?value.get(k):value[k];
      if(v!==null&&typeof v==='object'&&size(v)){lines.push(pad+yamlKey(k,schema)+':');lines=lines.concat(yamlLines(v,indent+2,path.concat([k]),schema));}
      else{lines.push(pad+yamlKey(k,schema)+': '+yamlScalar(v));}
    });
  } else {
    value.forEach(function(item){
      if(item!==null&&typeof item==='object'&&size(item)){var sub=yamlLines(item,indent+2,path.concat(['[]']),schema);sub[0]=pad+'- '+sub[0].slice(indent+2);lines=lines.concat(sub);}
      else{lines.push(pad+'- '+yamlScalar(item));}
    });
  }
  return lines;
}
function sha256Hex(text){
  var b=Array.from(new TextEncoder().encode(text)),K=[],H=[],i,j,p=2,n=0;
  function frac(x){return (x-Math.floor(x))*4294967296|0;}
  while(n<64){for(j=2;j*j<=p;j++){if(p%j===0){break;}}if(j*j>p){if(n<8){H[n]=frac(Math.pow(p,1/2));}K[n]=frac(Math.pow(p,1/3));n++;}p++;}
  var len=b.length*8;b.push(0x80);while(b.length%64!==56){b.push(0);}
  for(i=7;i>=0;i--){b.push(i>3?0:(len>>>(i*8))&255);}
  function r(x,c){return (x>>>c)|(x<<(32-c));}
  for(i=0;i<b.length;i+=64){
    var w=[],a=H.slice(),t;
    for(j=0;j<64;j++){
      if(j<16){w[j]=(b[i+4*j]<<24)|(b[i+4*j+1]<<16)|(b[i+4*j+2]<<8)|b[i+4*j+3];}
      else{var s0=r(w[j-15],7)^r(w[j-15],18)^(w[j-15]>>>3),s1=r(w[j-2],17)^r(w[j-2],19)^(w[j-2]>>>10);w[j]=(w[j-16]+s0+w[j-7]+s1)|0;}
      var S1=r(a[4],6)^r(a[4],11)^r(a[4],25),ch=(a[4]&a[5])^(~a[4]&a[6]),t1=(a[7]+S1+ch+K[j]+w[j])|0;
      var S0=r(a[0],2)^r(a[0],13)^r(a[0],22),mj=(a[0]&a[1])^(a[0]&a[2])^(a[1]&a[2]),t2=(S0+mj)|0;
      a=[(t1+t2)|0,a[0],a[1],a[2],(a[3]+t1)|0,a[4],a[5],a[6]];
    }
    for(j=0;j<8;j++){H[j]=(H[j]+a[j])|0;}
  }
  return H.map(function(x){return (x>>>0).toString(16).padStart(8,'0');}).join('');
}
function configYaml(schema,sel){var doc=configDocument(schema,sel);return size(doc)?yamlLines(doc,0,[],schema).join('\n')+'\n':'{}\n';}
"""

UI_JS = r"""
(function(){
var schema=JSON.parse(document.getElementById('fathom-schema').textContent);
var init=schema.initial,origin={},touched={};
function $(sel,root){return Array.prototype.slice.call((root||document).querySelectorAll(sel));}
function key(el){return el.getAttribute('data-key');}
function colName(el){return schema.columns[Number(el.getAttribute('data-col'))].name;}
function asInt(el){var t=stripWs(el.value);if(t===''){return null;}if(!/^-?[0-9]+$/.test(t)){return NaN;}return Number(t);}
function selections(){
  var sel={question:null,row_unit:null,target:null,pair_budget:null,sample_rows:null,bins:null,sections:Object.create(null),intervals:[],time_series:[],columns:Object.create(null)};
  $('[data-text]').forEach(function(el){sel[el.getAttribute('data-text')]=el.value;});
  var t=document.getElementById('target');sel.target=t.value===''?null:schema.target_options[Number(t.value)];
  $('[data-int]').forEach(function(el){var v=asInt(el);sel[el.getAttribute('data-int')]=(v===null||isNaN(v))?null:v;});
  $('[data-section]').forEach(function(el){sel.sections[el.getAttribute('data-section')]=el.checked;});
  $('[data-interval]').forEach(function(el){if(el.checked){var p=schema.interval_options[Number(el.getAttribute('data-interval'))];sel.intervals.push([p.start,p.end]);}});
  if(schema.time_series_options){
  sel.time_series=[];
  $('[data-series]').forEach(function(el){if(el.checked){var i=Number(el.getAttribute('data-series')),p=schema.time_series_options[i],v=document.querySelector('[data-series-value="'+i+'"]').value,g=document.querySelector('[data-series-grain="'+i+'"]').value;sel.time_series.push({time:p.column,value:v===''?null:schema.series_value_options[Number(v)],granularities:[g]});}});
  }else{
  $('[data-series]').forEach(function(el){if(el.checked){var i=el.getAttribute('data-series'),p=schema.series_options[Number(i)],item={time:p.time,value:p.value,by:seriesBy(i)};
    item.granularities=$('[data-series-grain="'+i+'"]').filter(function(g){return g.checked;}).map(function(g){return g.getAttribute('data-grain');});
    Object.keys(p.extra||{}).forEach(function(k){item[k]=p.extra[k];});sel.time_series.push(item);}});
  }
  $('[data-col]').forEach(function(el){var n=colName(el),f=el.getAttribute('data-field');if(!own(sel.columns,n)){sel.columns[n]=Object.create(null);}
    if(f==='exclude_from_target'){if(el.checked){sel.columns[n].exclude_from_target=true;}}else if(el.value!==''){sel.columns[n][f]=f==='frame_rate'?Number(el.value):el.value;}});
  return sel;
}
function seriesBy(i){var b=document.querySelector('[data-series-by="'+i+'"]');return b.value===''?null:schema.by_options[Number(b.value)];}
function seriesIndex(el){var a=['data-series','data-series-by','data-series-grain'].filter(function(n){return el.hasAttribute(n);})[0];return a?Number(el.getAttribute(a)):null;}
function valueOf(el){return el.type==='checkbox'?el.checked:el.value;}
function typedValue(el){if(el.hasAttribute('data-int')){var v=asInt(el);return v===null?null:isNaN(v)?el.value:v;}return valueOf(el);}
function stateOf(el){
  var k=key(el),v=valueOf(el),d=el.getAttribute('data-default');
  if(origin[k]==='suggested'&&String(v)===el.getAttribute('data-suggested')){return 'suggested';}
  if(el.hasAttribute('data-initial')&&String(v)===el.getAttribute('data-initial')&&String(v)!==d){return 'existing config';}
  if(String(v)===d){return 'default';}
  return 'selected';
}
function manifest(){
  var controls=$('[data-key]').filter(function(el){return el.tagName!=='OUTPUT';}).map(function(el){
    var item={control:el.getAttribute('data-label'),value:el.id==='target'?selections().target:typedValue(el),state:stateOf(el)};
    if(el.hasAttribute('data-interval')){var p=schema.interval_options[Number(el.getAttribute('data-interval'))];item.interval={start:p.start,end:p.end};}
    if(schema.time_series_options&&el.hasAttribute('data-series')){var i=Number(el.getAttribute('data-series'));var sv=document.querySelector('[data-series-value="'+i+'"]').value;item.series={time:schema.time_series_options[i].column,value:sv===''?null:schema.series_value_options[Number(sv)],granularity:document.querySelector('[data-series-grain="'+i+'"]').value};}
    if(schema.time_series_options&&el.hasAttribute('data-series-value')){var si=Number(el.getAttribute('data-series-value'));item.time=schema.time_series_options[si].column;item.value=el.value===''?null:schema.series_value_options[Number(el.value)];}
    if(schema.time_series_options&&el.hasAttribute('data-series-grain')){item.time=schema.time_series_options[Number(el.getAttribute('data-series-grain'))].column;}
    if(el.hasAttribute('data-col')){item.column=colName(el);}
    var si=seriesIndex(el);if(!schema.time_series_options&&si!==null){var sp=schema.series_options[si];item.series={time:sp.time,value:sp.value};if(el.hasAttribute('data-series-by')){item.value=seriesBy(si);}}
    if(item.state==='suggested'){item.suggestion_reason=el.getAttribute('data-reason');}
    return item;});
  var y='';
  try{y=configYaml(schema,selections());}catch(e){return {status:'invalid configuration',error:e.message};}
  return {kind:'fathom-config-manifest',advisory:'Provenance of each control on the configure page. Advisory only: Fathom does not read this file, and it is not an audit certificate; it records what the page showed, not what anyone verified.',
          yaml_sha256:sha256Hex(y),yaml_sha256_basis:'sha256 of the exact UTF-8 bytes of the downloaded '+schema.yaml_filename,
          dataset:schema.dataset,controls:controls};
}
function refresh(){
  var bad=[];
  $('[data-int]').forEach(function(el){var v=asInt(el),kn=schema.knobs[el.getAttribute('data-int')];if(v!==null&&(isNaN(v)||v<kn.min||v>kn.max)){bad.push(el.getAttribute('data-label')+' must be an integer from '+kn.min+' to '+kn.max+'; not emitted');}});
  $('[data-key]').forEach(function(el){if(el.tagName==='OUTPUT'){return;}var o=document.querySelector('output[data-for="'+key(el)+'"]');if(o){o.textContent=stateOf(el);o.className='state '+stateOf(el).replace(' ','-');}});
  var y='';
  try{y=configYaml(schema,selections());}catch(e){bad.push(e.message+'; YAML not emitted');}
  document.getElementById('copy').disabled=bad.length>0;
  document.getElementById('download').setAttribute('aria-disabled',String(bad.length>0));
  document.getElementById('yaml').textContent=y;
  document.getElementById('warnings').textContent=bad.join('; ');
  if(bad.length){document.getElementById('download').removeAttribute('href');}else{document.getElementById('download').href='data:application/yaml;charset=utf-8,'+encodeURIComponent(y);}
  document.getElementById('manifest').href='data:application/json;charset=utf-8,'+encodeURIComponent(JSON.stringify(manifest(),null,2)+'\n');
}
$('[data-key]').forEach(function(el){if(el.tagName==='OUTPUT'){return;}
  el.addEventListener('input',function(){origin[key(el)]=(el.type==='checkbox'&&el.hasAttribute('data-suggested'))?'suggested':'selected';var s=document.querySelector('[data-accept="'+key(el)+'"]');if(s){s.checked=false;}refresh();});
  el.addEventListener('change',function(){origin[key(el)]=origin[key(el)]||'selected';refresh();});});
$('[data-accept]').forEach(function(box){box.addEventListener('change',function(){
  var target=document.querySelector('[data-key="'+box.getAttribute('data-accept')+'"]');
  if(box.checked){target.value=target.getAttribute('data-suggested');origin[key(target)]='suggested';}
  else{target.value=target.getAttribute('data-default');origin[key(target)]='selected';}
  refresh();});});
document.getElementById('copy').addEventListener('click',function(){
  var y=document.getElementById('yaml').textContent;
  if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(y);}
  else{var r=document.createRange();r.selectNodeContents(document.getElementById('yaml'));var s=window.getSelection();s.removeAllRanges();s.addRange(r);document.execCommand('copy');}
});
PICKER_SETUP
refresh();
})();
"""

UI_JS=UI_JS.replace('PICKER_SETUP',PICKER_UI_JS)

CSS = theme_css() + KIND_CSS + TEMPORAL_CSS + """:root{--bg:var(--surface);--fg:var(--ink);--line:var(--border);--card:var(--panel);--sug:var(--kind-hypothesis);--sel:var(--kind-observation)}
body{font:15px/1.5 system-ui,sans-serif;background:var(--bg);color:var(--fg);max-width:1180px;margin:auto;padding:24px 16px}
h1{font-size:32px;margin:0 0 4px}h2{border-bottom:2px solid var(--accent);padding-bottom:6px;margin-top:32px}
section{margin-bottom:24px}.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:16px}
.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;background:var(--card)}th,td{padding:7px 9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
td{overflow-wrap:anywhere}small,.muted{color:var(--muted)}select,input[type=text],input[type=number]{font:inherit;max-width:100%;background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:4px;padding:3px 5px}
input[type=text]{width:100%;box-sizing:border-box}.state{display:inline-block;font-size:12px;padding:1px 7px;border-radius:10px;border:1px solid var(--line);color:var(--muted)}
.state.suggested{color:var(--sug);border-color:var(--sug)}.state.selected,.state.existing-config{color:var(--sel);border-color:var(--sel)}
.sug{color:var(--sug);font-size:13px}pre{background:var(--card);border:1px solid var(--line);padding:12px;overflow-x:auto;white-space:pre}
.bar{position:sticky;top:0;background:var(--bg);padding:8px 0;z-index:1}button,a.btn{display:inline-block;margin-bottom:6px;font:inherit;background:var(--tint);color:var(--link);border:0;border-radius:4px;padding:6px 12px;margin-right:8px;text-decoration:none;cursor:pointer}
.legend span{margin-right:10px}#warnings{color:var(--kind-question)}
.format-picker{margin-top:16px;min-width:0}.format-picker h3{font-size:1.1rem}.format-picker table{min-width:520px}.format-picker td{overflow-wrap:anywhere}.format-live[hidden]{display:none}@media(max-width:600px){.format-picker table{min-width:0!important;table-layout:fixed}.format-picker td,.format-picker th{padding:7px 4px;overflow-wrap:anywhere}.format-picker th:first-child{width:36px}.format-picker code{overflow-wrap:anywhere;white-space:normal}}.cols select{width:100%}.facts{min-width:150px}.sug small{display:block}.grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(260px,360px);gap:24px;align-items:start}@media(max-width:860px){.grid{grid-template-columns:minmax(0,1fr)}}
.yaml-pane{position:sticky;top:12px}
.time-definition table{width:100%;table-layout:fixed}.time-definition .definition-fields th:first-child{width:18%}.time-definition .definition-fields th:nth-child(2){width:40%}.time-definition .definition-values th:first-child{width:45%}.time-definition td,.time-definition th{white-space:normal;overflow-wrap:anywhere}.time-definition select{width:100%;min-width:0}.time-definition .definition-pattern{white-space:pre-wrap;overflow-wrap:anywhere}
article.finding{background:var(--panel);border-left:3px solid var(--soft-border);padding:8px 14px;margin:10px 0}article p{margin:5px 0}details{margin:10px 0}summary{cursor:pointer;color:var(--link)}a{color:var(--link)}.chart svg{max-width:100%;height:auto}.num{text-align:right;font-variant-numeric:tabular-nums}.table-scroll{overflow-x:auto}.review-table{max-width:100%}#brief{margin-bottom:48px}.axis-captions p{margin:3px 0}svg text{font:13px system-ui,sans-serif}
.series{border-top:1px solid var(--line);padding-top:4px}.series:first-of-type{border-top:0}.sub{margin:4px 0 4px 24px}.sub label{margin-right:6px}.sub label.g{white-space:nowrap}
"""


def json_for_script(value) -> str:
    """JSON safe inside <script type=application/json>: no '<', '>' or '&' survive literally."""
    text = json.dumps(value, ensure_ascii=True, sort_keys=False, separators=(",", ":"))
    return text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def attr(value) -> str:
    return escape(str(value), quote=True)


def control_attrs(k: str, label: str, default, initial=None, suggested=None, reason=None) -> str:
    out = f' data-key="{attr(k)}" data-label="{attr(label)}" data-default="{attr(default)}"'
    if initial is not None: out += f' data-initial="{attr(initial)}"'
    if suggested is not None: out += f' data-suggested="{attr(suggested)}" data-reason="{attr(reason)}"'
    return out


def state(k: str) -> str:
    return f' <output class="state" data-for="{attr(k)}">default</output>'


def render_page(schema: dict, brief: str | None = None, download_name: str = "fathom.yaml") -> str:
    from .report_style import style_html, STYLE_CSS, NAV_SCRIPT
    from .time_definition import definition_fields
    # Saved spec022 Liftoff configurations have samples but no field-card schema.
    # Derive the additive view on a copy; never mutate a loaded artifact.
    schema={**schema,'columns':[{**c,'temporal_picker':{**c['temporal_picker'],'definition':c['temporal_picker'].get('definition') or definition_fields(c['temporal_picker']['samples'])}} if c.get('temporal_picker') else c for c in schema['columns']]}
    init, ds = schema["initial"], schema["dataset"]
    # Option lists are indexed so names never travel through attribute values the script trusts.
    target_options = [c["column"] for c in schema["target_candidates"]]
    if init.get("target") and init["target"] not in target_options: target_options.append(init["target"])
    interval_options = [dict(i) for i in schema["interval_suggestions"]]
    for a, b in init["intervals"]:
        if not any(i["start"] == a and i["end"] == b for i in interval_options):
            interval_options.append({"start": a, "end": b, "reason": "declared in the existing configuration"})
    series_options, matched = [dict(o) for o in schema["series_suggestions"]], set()
    for item in init["time_series"]:
        i = next((j for j, o in enumerate(series_options) if (o["time"], o["value"]) == (item["time"], item["value"]) and j not in matched), None)
        if i is None:
            series_options.append({"time": item["time"], "value": item["value"], "reason": "declared in the existing configuration"}); i = len(series_options) - 1
        matched.add(i)
        series_options[i]["initial"] = {"by": item["by"], "granularities": item["granularities"]}
        series_options[i]["extra"] = {k: item[k] for k in TS_PASSTHROUGH if k in item}
    by_options = list(schema["by_options"])
    for item in init["time_series"]:
        if item["by"] is not None and item["by"] not in by_options: by_options.append(item["by"])
    schema = {**schema, "target_options": target_options, "interval_options": interval_options, "series_options": series_options, "by_options": by_options}
    schema["yaml_filename"] = download_name
    if "time_series_suggestions" in schema: schema["time_series_options"] = schema["time_series_suggestions"]
    h = ['<h1>Configure Fathom</h1><p class="muted">Builds a YAML configuration for <code>guide profile --config</code> from a profile of <b>'
         + escape(ds["file"]) + '</b> (' + f'{ds["rows"]:,} rows, {ds["columns"]:,} columns' + '; sha256 ' + escape(ds["sha256"][:12])
         + '…). Nothing here changes the data or runs new analysis. Every value starts at the system default; suggestions are shown with their observable reason and apply only when you tick them.</p>',
         '<p class="legend"><span class="state">default</span> what Fathom does with no config <span class="state suggested">suggested</span> ticked by you from the profile <span class="state selected">selected</span> set by you <span class="state existing-config">existing config</span> from --config</p>',
         '<div class="grid"><div>']
    if brief is not None:
        h[0] = h[0].replace('<h1>Configure Fathom</h1>', '<h2 id="configurations">Configurations</h2>')
        h.insert(0, brief)
    # Purpose
    h.append('<section><h2>Question and row unit</h2><div class="card">')
    for k, label, default_text in (("question", "Question", "none declared (documentation and QA fallback)"), ("row_unit", "Row unit", "unknown (not declared)")):
        iv = init.get(k) or ""
        h.append(f'<p><label>{label} <small>default: {escape(default_text)}</small>{state(k)}<br><input type="text" data-text="{k}" value="{attr(iv)}"'
                 + control_attrs(k, k, "", iv if iv else None) + '></label></p>')
    h.append('</div></section>')
    # Target
    h.append('<section><h2>Target</h2><div class="card"><p class="muted">Candidates are listed by observable facts only: effective type, populated share, distinct values. The list is not ranked and says nothing about relevance.</p>')
    ti = str(target_options.index(init["target"])) if init.get("target") else ""
    h.append('<p><label>Target ' + state("target") + '<br><select id="target"' + control_attrs("target", "target", "", ti or None) + '><option value="">(default: no target)</option>')
    for i, name in enumerate(target_options):
        reason = next((c["reason"] for c in schema["target_candidates"] if c["column"] == name), "declared in the existing configuration")
        h.append(f'<option value="{i}"' + (' selected' if str(i) == ti else '') + '>' + escape(name) + ' — ' + escape(reason) + '</option>')
    h.append('</select></label></p></div></section>')
    # Columns
    h.append('<section><h2>Columns</h2><p class="muted">Type and date-format overrides are human declarations; the inference is kept beside them in the report. Removing a column is not offered: it would suppress that column\'s findings.</p><div class="scroll"><table class="cols"><thead><tr><th>Column</th><th>Inferred / observed</th><th>Type override</th><th>Date format</th><th>exclude_from_target</th></tr></thead><tbody>')
    pickers=[]
    for i, c in enumerate(schema["columns"]):
        ic = init["columns"].get(c["name"], {})
        sug = {s["key"]: s for s in c["suggestions"]}
        cells = ['<td><b>' + escape(c["name"]) + '</b></td>',
                 '<td class="facts">inferred ' + escape(c["inferred_type"]) + ('; effective ' + escape(c["effective_type"]) + ' (existing override)' if c["override"] else '') + '<br><small>' + escape("; ".join(c["facts"])) + '</small></td>']
        for field, options in (("type", schema["types"]), ("date_format", schema["date_formats"])):
            k = f"col:{i}:{field}"
            s = sug.get(field)
            iv = ic.get(field)
            label = f"columns[{i}].{field}"
            if field=='date_format':
                canonical=(f'<label>Named format or custom pattern <input type="text" data-col="{i}" data-field="{field}" value="{attr(iv or "")}"'+control_attrs(k,label,"",iv,s and s["value"],s and s["reason"])+'> </label>'+state(k).replace('>default<','>existing config<' if iv else '>default<'))
                rate=ic.get('frame_rate')
                rate_control=(f'<label>Declared frame rate (only with %F) <input type="number" step="any" data-col="{i}" data-field="frame_rate" value="{attr(rate if rate is not None else "")}"'+control_attrs(f'col:{i}:frame_rate',f'columns[{i}].frame_rate',"",str(rate) if rate is not None else None)+'> </label>')
                canonical+=rate_control
                if c.get('temporal_picker'):
                    pickers.append(render_picker(i,c,canonical))
                    cell=f'<a href="#format-picker-{i}">Preview / choose format</a>'
                else:cell=canonical
            else:
                cell = (f'<select data-col="{i}" data-field="{field}"' + control_attrs(k, label, "", iv, s and s["value"], s and s["reason"]) + '>'
                        + '<option value="">(default)</option>'
                        + ''.join(f'<option value="{attr(o)}"' + (' selected' if o == iv else '') + f'>{escape(o)}</option>' for o in options) + '</select>' + state(k))
            if s:
                cell += f'<br><label class="sug"><input type="checkbox" data-accept="{attr(k)}"> suggested: {escape(s["value"])}<small>{escape(s["reason"])}</small></label>'
            cells.append('<td>' + cell + '</td>')
        k = f"col:{i}:exclude_from_target"
        iv = ic.get("exclude_from_target")
        cells.append(f'<td><input type="checkbox" data-col="{i}" data-field="exclude_from_target"' + (' checked' if iv else '')
                     + control_attrs(k, f"columns[{i}].exclude_from_target", "false", "true" if iv else None) + '>' + state(k) + '</td>')
        h.append('<tr>' + ''.join(cells) + '</tr>')
    h.append('</tbody></table></div>'+''.join(pickers)+'</section>')
    # Intervals
    h.append('<section><h2>Declared intervals</h2><div class="card"><p class="muted">Pairs of temporal columns, offered unticked. An interval is a domain declaration: Fathom checks end before start, end equal to start and durations only for declared pairs.</p>')
    if not interval_options: h.append('<p>No pair of temporal columns in this profile.</p>')
    for i, p in enumerate(interval_options):
        k = f"interval:{i}"
        declared = [p["start"], p["end"]] in init["intervals"]
        h.append(f'<p><label><input type="checkbox" data-interval="{i}"' + (' checked' if declared else '')
                 + control_attrs(k, f"intervals[{i}]", "false", "true" if declared else None, "true", p["reason"]) + '> start <b>'
                 + escape(p["start"]) + '</b> → end <b>' + escape(p["end"]) + '</b></label>' + state(k) + '<br><small>' + escape(p["reason"]) + '</small></p>')
    h.append('</div></section>')
    # Liftoff-only optional controls; plain configure remains a stage-two configuration page.
    if "time_series_options" in schema:
        h.append('<section><h2>Declared time series</h2><div class="card"><p>Unticked suggestions are not declarations. Previews use event counts with auto granularities. Selecting a value or different grain changes the question; by-group series and lag controls remain direct YAML options.</p>')
        if not schema["time_series_options"]: h.append('<p>No temporal column meets the30-distinct-period candidate rule.</p>')
        for i, item in enumerate(schema["time_series_options"]):
            k=f"series:{i}"
            h.append(f'<p><label><input type="checkbox" data-series="{i}"'+control_attrs(k,f'time_series[{i}]',"false",suggested="true",reason=item['reason'])+'> '+escape(item['column'])+'</label>'+state(k)+'<br><small>'+escape(item['reason'])+'</small></p>')
            h.append(f'<p><label>Value (only used when ticked) <select data-series-value="{i}"'+control_attrs(k+':value',f'time_series[{i}].value',"")+ '><option value="">Events (row counts)</option>')
            for j, name in enumerate(schema['series_value_options']):
                if name != item['column']: h.append(f'<option value="{j}">'+escape(name)+'</option>')
            h.append('</select></label>'+state(k+':value')+'</p>')
            h.append(f'<p><label>Granularity (only used when ticked) <select data-series-grain="{i}"'+control_attrs(k+':grain',f'time_series[{i}].granularity','auto')+'>')
            h.extend('<option value="'+g+'">'+g+'</option>' for g in ('auto','hour','day','week','month','year'))
            h.append('</select></label>'+state(k+':grain')+'</p>')
        h.append('</div></section>')
    else:
        # Time series
        h.append('<section><h2>Time series</h2><div class="card"><p class="muted">Series offered unticked, by the same rule the report uses to ask about one. A series is a domain declaration: Fathom never infers one. Value <i>event counts</i> counts rows per period (<code>value: null</code>); a numeric value is summed per period. With no granularity ticked, Fathom uses <code>auto</code>.</p>')
        if not series_options: h.append(f'<p>No temporal column with at least {MIN_N} distinct periods in this profile.</p>')
        for i, o in enumerate(series_options):
            k, oi = f"series:{i}", o.get("initial")
            what = ("event counts" if o["value"] is None else "sum of <b>" + escape(o["value"]) + "</b>") + " by <b>" + escape(o["time"]) + "</b>"
            h.append(f'<div class="series"><p><label><input type="checkbox" data-series="{i}"' + (' checked' if oi else '')
                     + control_attrs(k, f"time_series[{i}]", "false", "true" if oi else None, "true", o["reason"]) + '> ' + what + '</label>' + state(k)
                     + '<br><small>' + escape(o["reason"]) + '</small></p>')
            bk, bi = f"series:{i}:by", (str(by_options.index(oi["by"])) if oi and oi["by"] is not None else None)
            h.append(f'<p class="sub"><label>by <small>(optional; top {TOP_N} groups by row count)</small> <select data-series-by="{i}"' + control_attrs(bk, f"time_series[{i}].by", "", bi)
                     + '><option value="">(none)</option>' + ''.join(f'<option value="{j}"' + (' selected' if str(j) == bi else '') + '>' + escape(n) + '</option>' for j, n in enumerate(by_options))
                     + '</select></label>' + state(bk) + '</p><p class="sub">granularities: ')
            for g in schema["ts_granularities"]:
                gk, on = f"series:{i}:grain:{g}", bool(oi and g in oi["granularities"])
                h.append(f'<label class="g"><input type="checkbox" data-series-grain="{i}" data-grain="{g}"' + (' checked' if on else '')
                         + control_attrs(gk, f"time_series[{i}].granularities.{g}", "false", "true" if on else None) + f'> {g}</label>{state(gk)} ')
            if o.get("extra"): h.append('<br><small>kept from --config: ' + escape(", ".join(f"{k} {v}" for k, v in o["extra"].items())) + '</small>')
            h.append('</p></div>')
        h.append('</div></section>')
    # Knobs
    h.append('<section><h2>Bins, budget and samples</h2><div class="card">')
    labels = {"bins": ("Histogram bins (every histogram: values, positive log view, string lengths)", schema["bin_rule_default"]), "pair_budget": ("Relationship pair budget", "5"), "sample_rows": ("Sample rows per view", "20")}
    for k in INT_KNOBS:
        knob = schema["knobs"][k]
        name, default_text = labels[k]
        iv = init.get(k)
        h.append(f'<p><label>{escape(name)} <small>default: {escape(default_text)}; allowed {knob["min"]}–{knob["max"]}</small>{state(k)}<br>'
                 f'<input type="number" min="{knob["min"]}" max="{knob["max"]}" step="1" data-int="{k}" value="{attr("" if iv is None else iv)}"'
                 + control_attrs(k, k, "", None if iv is None else iv) + '></label></p>')
    h.append('<p id="warnings"></p></div></section>')
    # Sections
    h.append('<section><h2>Optional report sections</h2><div class="card"><p class="muted">An omitted section is named in the report under "What the data cannot tell" as omitted by configuration; the saved artifact still holds it. Findings, the dataset summary and provenance are always rendered.</p>')
    for s in schema["sections"]:
        k = f"section:{s['key']}"
        on = init["sections"].get(s["key"], True)
        h.append(f'<p><label><input type="checkbox" data-section="{attr(s["key"])}"' + (' checked' if on else '')
                 + control_attrs(k, f"sections.{s['key']}", "true", None if on else "false") + '> render ' + escape(s["title"]) + '</label>' + state(k) + '</p>')
    h.append('</div></section>')
    # Fixed rules
    h.append('<section><h2>Evidentiary rules (read-only)</h2><p class="muted">These thresholds decide what counts as evidence. They are recorded decisions, not settings, and no control here can suppress a warning or finding.</p><div class="scroll"><table><thead><tr><th>Rule</th><th>Threshold</th><th>Recorded source</th></tr></thead><tbody>')
    for r in schema["fixed_rules"]:
        h.append('<tr><td>' + escape(r["name"]) + '</td><td>' + escape(r["rule"]) + '</td><td>' + escape(r["source"]) + '</td></tr>')
    h.append('</tbody></table></div><h3>Not offered by this page</h3><ul>' + ''.join('<li><b>' + escape(e["key"]) + '</b>: ' + escape(e["status"]) + '</li>' for e in schema["extension_points"]) + '</ul></section>')
    # YAML pane
    h.append('</div><div class="yaml-pane"><section><h2>Generated YAML</h2><div class="bar"><button id="copy" type="button">Copy</button><a class="btn" id="download" download="fathom.yaml" href="#">Download YAML</a><a class="btn" id="manifest" download="config-manifest.json" href="#">Download manifest</a></div>'
             '<pre id="yaml"></pre><p class="muted">Only system-default values are left out. Run <code>guide profile DATA.csv --config fathom.yaml --out DIR</code>. The manifest records which values were default, suggested or selected, and the sha256 of this YAML; it is advisory, not an audit certificate, and Fathom does not read it.</p>'
             '<noscript><p>JavaScript is off. For the exact untouched Liftoff page defaults, run <code>guide liftoff DATA.csv --out discovery --yaml liftoff.yaml</code>, then edit YAML to declare choices and run <code>guide profile DATA.csv --config liftoff.yaml --out report</code>. Suggested controls stay unticked; this command does not accept them. Existing page edits must be transferred to YAML explicitly.</p></noscript></section></div></div>')
    if brief is not None:
        h[-1] = h[-1].replace('download="fathom.yaml"', 'download="'+attr(download_name)+'"').replace('--config fathom.yaml', '--config '+escape(download_name))
    page = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>'+('Fathom liftoff' if brief is not None else 'Configure Fathom')+'</title><style>' + CSS + STYLE_CSS + '</style></head><body>' + '\n'.join(h)
            + '\n<script type="application/json" id="fathom-schema">' + json_for_script(schema) + '</script>\n'
            + '<script id="fathom-yaml">' + YAML_JS + '</script>\n<script>' + UI_JS + '</script>\n'+(NAV_SCRIPT if brief is not None else '')+'</body></html>\n')
    return style_html(page,columns=[c['name'] for c in schema['columns']])


def schema_from_page(page: str) -> dict:
    """Recover the embedded control schema (tests and tooling)."""
    m = re.search(r'<script type="application/json" id="fathom-schema">(.*?)</script>', page, re.S)
    return json.loads(m.group(1))


def yaml_js_from_page(page: str) -> str:
    return re.search(r'<script id="fathom-yaml">(.*?)</script>', page, re.S).group(1)
