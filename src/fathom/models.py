"""The canonical input wrapper and versioned result interface."""

from dataclasses import asdict, dataclass
import json
from pathlib import Path

import pandas as pd


TYPES = {"numeric", "categorical", "boolean", "temporal", "string"}


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"


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


def validate_document(doc: dict) -> None:
    """Check the stable wire shape before a view or comparison consumes it."""
    if not isinstance(doc, dict) or type(doc.get("schema_version")) is not int or doc["schema_version"] != 1:
        raise ValueError("unsupported artifact schema_version; expected 1")
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
                         **{k: doc["purpose"].get(k) for k in ("question", "target")}}, names)
        selection = doc["selection"]
        if (not isinstance(selection.get("selected"), list) or not isinstance(selection.get("excluded"), list)
                or type(selection.get("budget")) is not int or not 0 <= selection["budget"] <= 20):
            raise ValueError("invalid artifact selection")
    else:
        if set(doc["contexts"]) != {"before", "after"}:
            raise ValueError("comparison needs before and after contexts")
        if not all(isinstance(v, dict) for v in doc["contexts"].values()) or not all(isinstance(v, str) for v in doc["limitations"]):
            raise ValueError("invalid comparison contexts/limitations")
    # Also reject non-JSON data and non-finite metrics in programmatically built results.
    canonical_json(doc)
