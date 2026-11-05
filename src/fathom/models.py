"""The canonical input wrapper and versioned result interface."""

from dataclasses import asdict, dataclass
import json
from pathlib import Path

import pandas as pd


TYPES = {"numeric", "categorical", "boolean", "temporal", "string", "phone", "email", "url", "latitude", "longitude"}


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"


def validate_target_payload(ta,purpose_target,names,total_rows):
    """Validate fields consumed by target tables and coverage before any renderer runs."""
    def count(v):return type(v) is int and v>=0
    def number(v):return v is None or type(v) in (int,float)
    def share(v):return v is None or type(v) in (int,float) and 0<=v<=1
    if 'target' not in ta or ta['target']!=purpose_target or (ta['target'] is not None and (not isinstance(ta['target'],str) or ta['target'] not in names)):
        raise ValueError('target analysis must match purpose.target')
    for entry in ta['excluded']:
        if not isinstance(entry,dict) or entry.get('column') not in names or not isinstance(entry.get('reason'),str):raise ValueError('invalid target exclusion')
    for summary in ta['groups']:
        if not isinstance(summary,dict) or not count(summary.get('share_denominator')) or summary['share_denominator']!=total_rows or not count(summary.get('group_missing')) or summary['group_missing']>total_rows or not isinstance(summary.get('value_type'),str) or summary.get('value_type') not in {'numeric','latitude','longitude','categorical','boolean'} or not isinstance(summary.get('groups'),list):raise ValueError('invalid target summary fields')
        for group in summary['groups']:
            if not isinstance(group,dict) or not isinstance(group.get('value'),str) or not isinstance(group.get('statistics'),dict) or not isinstance(group.get('contrasts'),list) or 'missing_share' not in group or not share(group['missing_share']):raise ValueError('invalid target group fields')
            stats=group['statistics']
            if summary['value_type'] in {'numeric','latitude','longitude'}:
                if any(k not in {'mean','median','min','max'} or not number(v) for k,v in stats.items()) or (group.get('valid',0) and not {'mean','median','min','max'}<=stats.keys()):raise ValueError('invalid numeric group statistics')
            else:
                rates=stats.get('rates')
                if not isinstance(rates,list) or len(rates)>20:raise ValueError('invalid group rates')
                for rate in rates:
                    if not isinstance(rate,dict) or not isinstance(rate.get('value'),str) or not count(rate.get('count')) or 'share' not in rate or not share(rate['share']):raise ValueError('invalid group rate entry')
            for contrast in group['contrasts']:
                if not isinstance(contrast,dict) or any(not isinstance(contrast.get(k),str) for k in ('measure','basis')) or any(k not in contrast or not number(contrast[k]) for k in ('group','rest')):raise ValueError('invalid group contrast')
    for chart in ta['charts']:
        if not isinstance(chart,dict) or not isinstance(chart.get('kind'),str) or chart['kind'] not in {'scatter','group_box','rates'} or not count(chart.get('n')) or not count(chart.get('total_rows')) or chart['total_rows']!=total_rows or chart['n']>total_rows:raise ValueError('invalid target chart coverage')
        for key in ('plotted','omitted_nonpositive','omitted_points'):
            if key in chart and (not count(chart[key]) or chart[key]>chart['n']):raise ValueError('invalid target chart optional count')
        if chart.get('kind')=='group_box' and isinstance(chart.get('data'),list):
            for row in chart['data']:
                if isinstance(row,dict) and 'excluded_nonpositive' in row and not count(row['excluded_nonpositive']):raise ValueError('invalid box exclusion count')


@dataclass(frozen=True)
class SchemaContract:
    mode: str = "unknown"
    key: tuple[str, ...] = ()
    context: tuple[str, ...] = ()
    metric: str | None = None
    value: str | None = None
    data_type: str | None = None

    def resolve(self, columns: list[str]) -> "SchemaContract":
        if self.mode not in {"unknown", "wide", "long"}:
            raise ValueError("schema.mode must be unknown, wide or long")
        if self.mode == "long":
            raise ValueError("long schema profiling is not supported in this slice; use wide")
        references = list(self.key) + list(self.context)
        references += [s for s in (self.metric, self.value, self.data_type) if s is not None]
        if len(references) != len(set(references)):
            raise ValueError("schema column roles must be unique")
        if any(s not in columns for s in references):
            raise ValueError("schema references an unknown column")
        return SchemaContract(**{**asdict(self), "mode": "wide"})


@dataclass
class GuideDataFrame:
    frame: pd.DataFrame
    schema: SchemaContract
    source: dict
    raw_rows: list[list[str]] | None = None


@dataclass
class ProfilingResult:
    document: dict

    def __post_init__(self) -> None:
        validate_document(self.document)

    def to_json(self) -> str:
        return canonical_json(self.document)

    @classmethod
    def load(cls, path: str | Path) -> "ProfilingResult":
        def reject_constant(value: str) -> None:
            raise ValueError(f"non-finite JSON value: {value}")
        return cls(json.loads(Path(path).read_text(encoding="utf-8"), parse_constant=reject_constant))


# 1: finite metrics rounded to 10 decimals. 2: at least 6 significant figures (spec 008).
SCHEMA_VERSIONS = (1, 2)


def validate_document(doc: dict) -> None:
    """Check the stable wire shape before a view or comparison consumes it."""
    if not isinstance(doc, dict) or type(doc.get("schema_version")) is not int or doc["schema_version"] not in SCHEMA_VERSIONS:
        raise ValueError("unsupported artifact schema_version; expected 1 or 2")
    kind = doc.get("kind")
    shapes = {
        "profile": {"source": dict, "context": dict, "purpose": dict, "working_record": dict,
                    "schema": dict, "overview": dict, "columns": list, "findings": list,
                    "selection": dict, "bivariate": list, "dependencies": dict, "annotations": dict},
        "comparison": {"contexts": dict, "context_differences": dict, "deltas": dict,
                       "limitations": list, "annotations": dict},
    }
    if not isinstance(kind, str) or kind not in shapes:
        raise ValueError("unsupported artifact kind")
    for name, typ in shapes[kind].items():
        if not isinstance(doc.get(name), typ):
            raise ValueError(f"artifact field {name} must be {typ.__name__}")
    if kind == "profile":
        required = {"rows", "columns", "missing_cells", "duplicate_rows"}
        if not required <= doc["overview"].keys() or any(
            type(doc["overview"][k]) is not int or doc["overview"][k] < 0 for k in required
        ):
            raise ValueError("invalid profile overview")
        names = []
        for col in doc["columns"]:
            if not isinstance(col, dict) or not isinstance(col.get("name"), str):
                raise ValueError("invalid artifact column")
            if not {"count", "missing", "distinct", "effective_type", "inference", "statistics",
                    "examples", "frequencies", "meaning", "override", "observed_type"} <= col.keys():
                raise ValueError("incomplete artifact column")
            if not isinstance(col["effective_type"], str) or col["effective_type"] not in TYPES:
                raise ValueError("invalid artifact column type")
            if any(type(col[k]) is not int or col[k] < 0 for k in ("count", "missing", "distinct")):
                raise ValueError("invalid artifact column counts")
            if not isinstance(col["observed_type"], str) or not isinstance(col["statistics"], dict):
                raise ValueError("invalid artifact column summary")
            inference = col["inference"]
            if (not isinstance(inference, dict) or not isinstance(inference.get("type"), str)
                    or inference["type"] not in TYPES or not isinstance(inference.get("confidence"), str)
                    or any(not isinstance(inference.get(k), list) or not all(isinstance(v, str) for v in inference[k])
                           for k in ("reasons", "alternatives"))):
                raise ValueError("invalid artifact inference")
            for key, field in (("meaning", "value"), ("override", "type")):
                value = col[key]
                if value is not None and (not isinstance(value, dict) or not isinstance(value.get(field), str)
                                          or value.get("generator") != "human"):
                    raise ValueError(f"invalid artifact {key}")
            if not isinstance(col["examples"], list) or not all(isinstance(v, str) for v in col["examples"]):
                raise ValueError("invalid artifact examples")
            if not isinstance(col["frequencies"], list) or any(
                not isinstance(v, dict) or not isinstance(v.get("value"), str)
                or type(v.get("count")) is not int or v["count"] < 0 for v in col["frequencies"]
            ):
                raise ValueError("invalid artifact frequencies")
            names.append(col["name"])
        if len(set(names)) != len(names) or len(names) != doc["overview"]["columns"]:
            raise ValueError("invalid artifact column names/count")
        for finding in doc["findings"]:
            if not isinstance(finding, dict) or not {"id", "kind", "message", "generator", "evidence",
                                                    "uncertainty", "provenance"} <= finding.keys():
                raise ValueError("incomplete artifact finding")
            if not isinstance(finding["kind"], str) or finding["kind"] not in {"observation", "interpretation", "hypothesis", "action", "question"}:
                raise ValueError("invalid finding kind")
            if any(not isinstance(finding[k], str) for k in ("id", "message", "generator", "uncertainty")):
                raise ValueError("invalid finding text")
            if not isinstance(finding["provenance"], dict) or not isinstance(finding["evidence"], list):
                raise ValueError("invalid finding evidence/provenance")
            for evidence in finding["evidence"]:
                if not isinstance(evidence, dict) or not (isinstance(evidence.get("finding"), str)
                        or (isinstance(evidence.get("path"), str) and "value" in evidence)):
                    raise ValueError("invalid finding evidence item")
        if not {"sha256", "connector", "origin"} <= doc["source"].keys():
            raise ValueError("incomplete artifact source")
        if not all(isinstance(doc["source"][k], str) for k in ("sha256", "connector", "origin")):
            raise ValueError("invalid artifact source")
        if len(doc["source"]["sha256"]) != 64 or any(c not in "0123456789abcdef" for c in doc["source"]["sha256"]):
            raise ValueError("invalid artifact source hash")
        # Reuse strict declaration validation; it does not infer meaning or reopen data.
        from .config import validate_config
        working = doc["working_record"]
        if working.get("generator") != "human":
            raise ValueError("invalid working-record generator")
        validate_config({"context": doc["context"], "schema": doc["schema"],
                         **{k: working.get(k) for k in ("row_unit", "generating_process", "missingness_mechanism")},
                         "decisions": working.get("decisions", []),
                         **{k: doc["purpose"].get(k) for k in ("question", "target", "group_by")}}, names)
        selection = doc["selection"]
        if (not isinstance(selection.get("selected"), list) or not isinstance(selection.get("excluded"), list)
                or type(selection.get("budget")) is not int or not 0 <= selection["budget"] <= 20):
            raise ValueError("invalid artifact selection")
        if len(doc['bivariate'])>selection['budget'] or len(selection['selected'])>selection['budget']:raise ValueError('pair budget exceeded')
        if 'target_analysis' in doc:
            ta=doc['target_analysis']
            if not isinstance(ta,dict) or not isinstance(ta.get('status'),str) or ta.get('status') not in {'active','skipped'} or any(not isinstance(ta.get(k),str) for k in ('reason','warning','grouping_policy')):raise ValueError('invalid target status')
            if any(not isinstance(ta.get(k),list) for k in ('ranked','excluded','charts','groups')):raise ValueError('invalid target collections')
            if len(ta['charts'])>len(doc['bivariate']) or len(ta['groups'])>len(doc['bivariate']):raise ValueError('target detail budget exceeded')
            validate_target_payload(ta,doc['purpose'].get('target'),names,doc['overview']['rows'])
            for r in ta['ranked']:
                if not isinstance(r,dict) or r.get('column') not in names or type(r.get('n')) is not int or r['n']<2 or type(r.get('rank')) is not int or r['rank']<1 or type(r.get('selected')) is not bool or type(r.get('value')) not in (int,float) or not -1<=r['value']<=1 or type(r.get('strength')) not in (int,float) or not 0<=r['strength']<=1 or r.get('measure') not in {'Pearson r','Correlation ratio eta',"Cramer's V"}:raise ValueError('invalid target ranking')
            for s in ta['groups']:
                if not isinstance(s,dict) or s.get('group_column') not in names or s.get('value_column') not in names or not isinstance(s.get('groups'),list) or len(s['groups'])>20:raise ValueError('invalid target groups')
                for g in s['groups']:
                    if not isinstance(g,dict) or any(type(g.get(k)) is not int or g[k]<0 for k in ('n','valid','missing','rest_n','rest_valid')) or g['valid']+g['missing']!=g['n'] or type(g.get('share')) not in (int,float) or not 0<=g['share']<=1 or type(g.get('small')) is not bool:raise ValueError('invalid target group count')
            for ch in ta['charts']:
                if not isinstance(ch,dict) or ch.get('kind') not in {'scatter','group_box','rates'} or any(not isinstance(ch.get(k),str) for k in ('title','x_label','y_label')):raise ValueError('invalid target chart')
                if ch['kind']=='scatter':
                    if not isinstance(ch.get('points'),list) or not 1<=len(ch['points'])<=200 or any(not isinstance(p,dict) or any(type(p.get(k)) not in (int,float) for k in ('x','y')) for p in ch['points']):raise ValueError('invalid scatter points')
                    if any(not isinstance(ch.get(k),str) or ch.get(k) not in {'linear','log10'} for k in ('x_scale','y_scale')) or any((ch['x_scale']=='log10' and p['x']<=0) or (ch['y_scale']=='log10' and p['y']<=0) for p in ch['points']):raise ValueError('invalid scatter scale')
                else:
                    if not isinstance(ch.get('data'),list) or not 1<=len(ch['data'])<=20 or any(not isinstance(r,dict) or not isinstance(r.get('label'),str) or type(r.get('n')) is not int or r['n']<0 for r in ch['data']):raise ValueError('invalid grouped chart')
                    if ch['kind']=='group_box':
                        if not isinstance(ch.get('x_scale'),str) or ch.get('x_scale') not in {'linear','log10'}:raise ValueError('invalid grouped box scale')
                        for row in ch['data']:
                            box=row.get('box')
                            if box is not None:
                                if not isinstance(box,dict) or any(type(box.get(k)) not in (int,float) for k in ('min','q1','median','q3','max')) or sorted(box[k] for k in ('min','q1','median','q3','max'))!=[box[k] for k in ('min','q1','median','q3','max')] or (ch['x_scale']=='log10' and box['min']<=0):raise ValueError('invalid grouped box values')
                    if ch['kind']=='rates' and (not isinstance(ch.get('levels'),list) or not 1<=len(ch['levels'])<=20 or any(not isinstance(r.get('rates'),dict) or set(r['rates'])!=set(ch['levels']) or any(type(v) not in (int,float) or not 0<=v<=1 for v in r['rates'].values()) or abs(sum(r['rates'].values())-(1 if r['n'] else 0))>1e-8 for r in ch['data'])):raise ValueError('invalid target rates')
        if "dataset" in doc:
            identity=doc["dataset"]
            if not isinstance(identity,dict):raise ValueError("invalid dataset identity")
            for key in ("title","description"):
                if not isinstance(identity.get(key),dict) or not isinstance(identity[key].get("text"),str) or not isinstance(identity[key].get("status"),str) or identity[key].get("status") not in {"human","inferred"}:raise ValueError("invalid dataset identity text")
        if "samples" in doc:
            samples=doc["samples"]
            if not isinstance(samples,dict) or samples.get("columns")!=names or type(samples.get("seed")) is not int:raise ValueError("invalid samples")
            for key in ("first","last","random"):
                if not isinstance(samples.get(key),list):raise ValueError("invalid sample window")
                for row in samples[key]:
                    if not isinstance(row,dict) or type(row.get("position")) is not int or not 1<=row["position"]<=doc["overview"]["rows"]:raise ValueError("invalid sample position")
                    if not isinstance(row.get("values"),list) or len(row["values"])!=len(names) or any(v is not None and not isinstance(v,str) for v in row["values"]):raise ValueError("invalid sample cells")
        for col in doc["columns"]:
            if "special" in col:
                s=col['special']
                if not isinstance(s,dict) or any(type(s.get(k)) is not int or s[k]<0 for k in ('valid','invalid','placeholders','test_values')):raise ValueError('invalid special counts')
                if any(not isinstance(s.get(k),str) for k in ('policy','recognition','generator')):raise ValueError('invalid special provenance')
                for key in ('invalid_examples','placeholder_examples','test_examples'):
                    if not isinstance(s.get(key),list) or any(not isinstance(v,str) for v in s[key]):raise ValueError('invalid special examples')
                if not isinstance(s.get('domains'),list) or any(not isinstance(v,dict) or not isinstance(v.get('value'),str) or type(v.get('count')) is not int or v['count']<0 for v in s['domains']):raise ValueError('invalid special domains')
            if "exclude_from_target" in col and type(col["exclude_from_target"]) is not bool:raise ValueError("invalid exclusion declaration")
            if "univariate" in col:
                u=col["univariate"]
                if not isinstance(u,dict) or not isinstance(u.get("statistics"),dict) or not isinstance(u.get("charts"),list):raise ValueError("invalid univariate profile")
                if 'top_n_suppression' in u and not isinstance(u['top_n_suppression'],str):raise ValueError('invalid top-N suppression')
                for chart in u["charts"]:
                    if not isinstance(chart,dict) or any(not isinstance(chart.get(k),str) or not chart[k] for k in ("kind","title","x_label","y_label")):raise ValueError("invalid chart labels")
                    if chart["kind"] not in {"bar","time","histogram","box","ecdf"}:raise ValueError("unsupported chart kind")
                    if 'coverage_counts' in chart:
                        coverage=chart['coverage_counts']
                        if not isinstance(coverage,dict) or any(type(coverage.get(k)) is not int or coverage[k]<0 for k in ('positive','zeros','negatives','invalid')) or chart.get('scale')!='log10':raise ValueError('invalid log coverage')
                        if chart['kind']=='ecdf':
                            if not chart.get('points') or chart['points'][-1].get('count')!=coverage['positive'] or chart.get('n')!=coverage['positive']:raise ValueError('inconsistent log ECDF coverage')
                        elif sum(x.get('count',0) for x in chart.get('data',[]) if isinstance(x,dict))!=coverage['positive']:raise ValueError('inconsistent log coverage')
                    if chart["kind"]=='ecdf':
                        points=chart.get('points')
                        if not isinstance(points,list) or not points or len(points)>200:raise ValueError('invalid ECDF points')
                        previous=None
                        for point in points:
                            if not isinstance(point,dict) or type(point.get('x')) not in (int,float) or type(point.get('cumulative')) not in (int,float) or not 0<=point['cumulative']<=1 or type(point.get('count')) is not int or point['count']<1:raise ValueError('invalid ECDF point')
                            if previous and (point['x']<=previous['x'] or point['cumulative']<previous['cumulative']):raise ValueError('invalid ECDF ordering')
                            previous=point
                        if points[-1]['cumulative']!=1:raise ValueError('invalid ECDF endpoint')
                    elif chart["kind"]=="box":
                        box=chart.get("box")
                        if not isinstance(box,dict) or any(type(box.get(k)) not in (int,float) for k in ("min","q1","median","q3","max")):raise ValueError("invalid box values")
                    else:
                        if not isinstance(chart.get("data"),list) or any(not isinstance(v,dict) or not isinstance(v.get("label"),str) or type(v.get("count")) is not int or v["count"]<0 for v in chart["data"]):raise ValueError("invalid chart data")
        if 'missingness_patterns' in doc:
            m=doc['missingness_patterns']
            if not isinstance(m,dict) or not isinstance(m.get('patterns'),list) or len(m['patterns'])>20 or m.get('rows')!=doc['overview']['rows']:raise ValueError('invalid missingness patterns')
            if not isinstance(m.get('columns'),list) or len(m['columns'])>20 or any(name not in names for name in m['columns']) or any(type(m.get(k)) is not int or m[k]<0 for k in ('omitted_rows','omitted_columns','omitted_patterns')):raise ValueError('invalid missingness bounds')
            ch=m.get('chart')
            if not isinstance(ch,dict) or ch.get('kind')!='bar' or any(not isinstance(ch.get(k),str) for k in ('title','x_label','y_label')) or not isinstance(ch.get('data'),list) or len(ch['data'])!=len(m['patterns']):raise ValueError('invalid missingness chart')
            if any(not isinstance(v,dict) or not isinstance(v.get('label'),str) or type(v.get('count')) is not int or v['count']<0 for v in ch['data']):raise ValueError('invalid missingness chart counts')
            for pattern in m['patterns']:
                if not isinstance(pattern,dict) or not isinstance(pattern.get('missing'),list) or any(v not in names for v in pattern['missing']) or type(pattern.get('count')) is not int or pattern['count']<0 or type(pattern.get('share')) not in (int,float) or not 0<=pattern['share']<=1:raise ValueError('invalid missingness pattern')
            if sum(p['count'] for p in m['patterns'])+m.get('omitted_rows',-1)!=m['rows']:raise ValueError('inconsistent missingness totals')
        if "dataset_summary" in doc:
            summary = doc["dataset_summary"]
            if not isinstance(summary, dict):
                raise ValueError("invalid dataset summary")
            for key in ("rows", "columns", "duplicate_rows", "duplicate_columns", "lockstep_columns"):
                if type(summary.get(key)) is not int or summary[key] < 0:
                    raise ValueError("invalid dataset summary count")
            for key in ("complete_rows", "complete_columns", "missing_cells"):
                measure = summary.get(key)
                if not isinstance(measure, dict) or type(measure.get("count")) is not int or measure["count"]<0:
                    raise ValueError("invalid dataset summary measure")
                rate = measure.get("share")
                if rate is not None and (type(rate) not in (int,float) or not 0<=rate<=1):
                    raise ValueError("invalid dataset summary share")
            for key in ("duplicate_groups", "lockstep_groups", "constant_columns", "near_constant_columns"):
                if not isinstance(summary.get(key), list):
                    raise ValueError("invalid dataset summary column groups")
                groups = summary[key] if key.endswith("groups") else [summary[key]]
                if any(not isinstance(group,list) or any(not isinstance(name,str) or name not in names for name in group) for group in groups):
                    raise ValueError("invalid dataset summary column names")
            if any(summary[k] != doc["overview"][k] for k in ("rows","columns","duplicate_rows")):
                raise ValueError("inconsistent dataset summary")
            if not isinstance(summary.get("inferred_types"), dict) or any(
                    k not in TYPES or type(v) is not int or v<0 for k,v in summary["inferred_types"].items()):
                raise ValueError("invalid dataset summary inferred types")
            ids = [f["id"] for f in doc["findings"]]
            links = summary.get("finding_links")
            if len(set(ids)) != len(ids) or not isinstance(links, dict) or any(
                    not isinstance(refs,list) or not refs or any(not isinstance(ref,str) or ref not in ids for ref in refs) for refs in links.values()):
                raise ValueError("invalid dataset summary finding links")
            if not set(summary)-{"finding_links"} <= links.keys():
                raise ValueError("incomplete dataset summary finding links")
        if "quality" in doc:
            quality = doc["quality"]
            if not isinstance(quality,dict) or any(not isinstance(quality.get(k),dict) for k in ("rules","coverage","value_exclusions")):
                raise ValueError("invalid quality evidence")
    else:
        if set(doc["contexts"]) != {"before", "after"}:
            raise ValueError("comparison needs before and after contexts")
        if not all(isinstance(v, dict) for v in doc["contexts"].values()) or not all(isinstance(v, str) for v in doc["limitations"]):
            raise ValueError("invalid comparison contexts/limitations")
    # Also reject non-JSON data and non-finite metrics in programmatically built results.
    canonical_json(doc)
