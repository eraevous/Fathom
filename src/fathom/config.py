"""Strict human declarations; no inferred domain facts or executable config."""

from dataclasses import asdict
from datetime import date
from pathlib import Path

import yaml

from .models import SchemaContract, TYPES


def text(value: object, name: str, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty text")


def mapping(value: object, name: str, allowed: set[str]) -> dict:
    if not isinstance(value, dict) or any(k not in allowed for k in value):
        raise ValueError(f"{name} must be a mapping with keys: {', '.join(sorted(allowed))}")
    return value


def validate_config(raw: dict | None = None, columns: list[str] | None = None) -> dict:
    cfg = dict(mapping({} if raw is None else raw, "config", {
        "question", "target", "pair_budget", "columns", "row_unit", "generating_process",
        "missingness_mechanism", "decisions", "context", "schema", "title", "description", "sample_rows", "sample_seed", "sample_text_limit", "group_by"}))
    for key in ("question", "target", "row_unit", "generating_process", "missingness_mechanism", "title", "description", "group_by"):
        text(cfg.get(key), key, nullable=True)
    for key,default,low,high in (("sample_rows",20,0,100),("sample_seed",0,0,2**32-1),("sample_text_limit",120,20,1000)):
        value=cfg.get(key,default)
        if type(value) is not int or not low<=value<=high: raise ValueError(f"{key} must be an integer from {low} to {high}")
        cfg[key]=value
    budget = cfg.get("pair_budget", 5)
    if type(budget) is not int or not 0 <= budget <= 20:
        raise ValueError("pair_budget must be an integer from 0 to 20")
    cfg["pair_budget"] = budget
    metadata = mapping(cfg.get("columns", {}), "columns", set(columns) if columns is not None else set(cfg.get("columns", {})) if isinstance(cfg.get("columns", {}), dict) else set())
    for name, item in metadata.items():
        text(name, "column name")
        mapping(item, f"columns.{name}", {"type", "meaning", "date_format", "units", "role", "exclude_from_target"})
        if "exclude_from_target" in item and type(item["exclude_from_target"]) is not bool:raise ValueError("exclude_from_target must be boolean")
        if "type" in item and (not isinstance(item["type"], str) or item["type"] not in TYPES):
            raise ValueError(f"columns.{name}.type is unsupported; use one of: {', '.join(sorted(TYPES))} (dates are temporal)")
        if "date_format" in item:
            from .parsing import DATE_FORMATS
            if not isinstance(item["date_format"],str) or item["date_format"] not in DATE_FORMATS: raise ValueError(f"columns.{name}.date_format is unsupported; use one of: {', '.join(sorted(DATE_FORMATS))} (named formats, not strftime patterns)")
        if "role" in item and (not isinstance(item["role"],str) or item["role"] not in {"identifier","quantity"}): raise ValueError("unsupported column role")
        if "units" in item: text(item["units"], "column units")
        if "meaning" in item:
            text(item["meaning"], f"columns.{name}.meaning")
    cfg["columns"] = metadata
    if columns is not None and cfg.get("target") is not None and cfg["target"] not in columns:
        raise ValueError("target references an unknown column")
    if columns is not None and cfg.get("group_by") is not None and cfg["group_by"] not in columns:raise ValueError("group_by references an unknown column")
    context = mapping(cfg.get("context", {}), "context", {"snapshot_date", "source", "transformations", "other_changes"})
    snapshot = context.get("snapshot_date")
    if snapshot is not None:
        text(snapshot, "snapshot_date")
        try:
            if date.fromisoformat(snapshot).isoformat() != snapshot:
                raise ValueError
        except ValueError as exc:
            raise ValueError("snapshot_date must be YYYY-MM-DD") from exc
    text(context.get("source"), "context.source", nullable=True)
    transforms = context.get("transformations", [])
    if not isinstance(transforms, list):
        raise ValueError("transformations must be a list")
    for item in transforms:
        mapping(item, "transformation", {"type", "description"})
        for key in ("type", "description"):
            text(item.get(key), f"transformation.{key}")
    changes = context.get("other_changes", [])
    if not isinstance(changes, list):
        raise ValueError("other_changes must be a list")
    for item in changes:
        text(item, "other_change")
    cfg["context"] = {"snapshot_date": snapshot, "source": context.get("source"),
                      "transformations": transforms, "other_changes": changes}
    decisions = cfg.get("decisions", [])
    if not isinstance(decisions, list):
        raise ValueError("decisions must be a list")
    for item in decisions:
        mapping(item, "decision", {"decision", "rationale"})
        for key in ("decision", "rationale"):
            text(item.get(key), key)
    cfg["decisions"] = decisions
    schema = mapping(cfg.get("schema", {}), "schema", set(asdict(SchemaContract())))
    for key in ("key", "context"):
        values = schema.get(key, [])
        if not isinstance(values, (list, tuple)):
            raise ValueError(f"schema.{key} must be a list")
        for item in values:
            text(item, f"schema.{key}")
    for key in ("metric", "value", "data_type"):
        text(schema.get(key), f"schema.{key}", nullable=True)
    if not isinstance(schema.get("mode", "unknown"), str) or schema.get("mode", "unknown") not in {"unknown", "wide", "long"}:
        raise ValueError("schema.mode must be unknown, wide or long")
    cfg["schema"] = schema
    if columns is not None:
        SchemaContract(**schema).resolve(columns)
    return cfg


def load_config(path: str | Path | None) -> dict:
    if path is None:
        return validate_config()
    # BaseLoader keeps dates as strings; SafeLoader is used with its timestamp
    # resolver removed on a private subclass so ISO dates have the same wire type.
    class ConfigLoader(yaml.SafeLoader):
        pass
    ConfigLoader.yaml_implicit_resolvers = {
        k: [(tag, rx) for tag, rx in values if tag != "tag:yaml.org,2002:timestamp"]
        for k, values in yaml.SafeLoader.yaml_implicit_resolvers.items()
    }
    def unique_mapping(loader, node, deep=False):
        pairs = loader.construct_pairs(node, deep=deep)
        result = {}
        for key, value in pairs:
            if not isinstance(key, str) or key in result:
                raise ValueError("configuration keys must be unique strings")
            result[key] = value
        return result
    ConfigLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)
    return validate_config(yaml.load(Path(path).read_text(encoding="utf-8"), Loader=ConfigLoader))
