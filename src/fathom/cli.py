"""Thin local composition of connector, profiler and saved-result views."""

import argparse
import csv
from dataclasses import asdict
from pathlib import Path
import sys

import yaml

from . import __version__
from .config import load_config, read_config, validate_config
from .connectors import CSVConnector
from .models import ProfilingResult, SchemaContract, canonical_json
from .profiler import compare, profile
from .renderers import render_html, render_markdown


def summary_line(d: dict) -> str:
    """One deterministic line of what profile resolved; no timestamps."""
    purpose, record, ta = d.get("purpose") or {}, d.get("working_record") or {}, d.get("target_analysis") or {}
    excluded = [e["column"] for e in ta.get("excluded", []) if e.get("reason") != "target column"]
    target = (f"target: {ta['target']}; excluded from target: {', '.join(excluded) or 'none'}"
              if ta.get("target") else "target: not declared")
    return (f"guide: question: {purpose.get('question') or 'none declared'}; {target}; "
            f"row unit: {record.get('row_unit') or 'unknown (not declared)'}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="guide", description="Evidenced local table review")
    parser.add_argument("--version", action="version", version=f"guide {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    helps = {"configure": "write configure.html, a self-contained page that builds a YAML config from this table's profile "
                          "(defaults, observable suggestions, explicit selections), and configure-profile.json, the profile it used"}
    for command in ("profile", "render", "compare", "validate", "export", "configure"):
        sub = commands.add_parser(command, help=helps.get(command), description=helps.get(command))
        sub.add_argument("input", type=Path)
        if command == "compare":
            sub.add_argument("after", type=Path)
        if command in {"profile", "validate", "configure"}:
            sub.add_argument("--config", type=Path, help="existing YAML config" + ("; its values start the page as 'existing config'" if command == "configure" else ""))
        if command != "validate":
            sub.add_argument("--out", type=Path, required=True)
        if command == "export":
            sub.add_argument("--formats", nargs="+", choices=("pdf", "pptx"), default=["pdf", "pptx"])
            sub.add_argument("--deck",choices=("summary","full"),default="summary")
    args = parser.parse_args(argv)
    try:
        if args.command == "configure":
            from .configure import build_schema, render_page
            raw = read_config(args.config) if args.config else None
            cfg = validate_config(raw)
            data = CSVConnector(args.input, SchemaContract(**cfg["schema"])).load()
            result = profile(data, validate_config(cfg, list(data.frame.columns)))
            page = render_page(build_schema(result.document, data.frame, raw))
            args.out.mkdir(parents=True, exist_ok=True)
            for name, contents in (("configure.html", page), ("configure-profile.json", result.to_json())):
                (args.out / name).write_text(contents, encoding="utf-8", newline="\n")
            print(f"guide: wrote {args.out / 'configure-profile.json'}, {args.out / 'configure.html'}")
            return 0
        if args.command in {"profile", "validate"}:
            cfg = load_config(args.config)
            data = CSVConnector(args.input, SchemaContract(**cfg["schema"])).load()
            cfg = validate_config(cfg, list(data.frame.columns))
            if args.command == "validate":
                # The resolved schema keys stay at top level (CLI contract); "resolved" echoes
                # the human declarations that profile will use. Inference is not run here.
                values = {n: {k: m[k] for k in ("type", "date_format", "role", "units", "exclude_from_target") if k in m}
                          for n, m in sorted(cfg["columns"].items())}
                resolved = {"column_override_values": values, "rows": len(data.frame), "columns": len(data.frame.columns),
                            **{k: cfg.get(k) for k in ("question", "target", "group_by", "pair_budget", "row_unit")},
                            "exclude_from_target": sorted(n for n, m in cfg["columns"].items() if m.get("exclude_from_target")),
                            "column_overrides": {n: sorted(m) for n, m in sorted(cfg["columns"].items())},
                            "intervals": cfg["intervals"], "bins": cfg["bins"], "sections": cfg["sections"]}
                print(canonical_json({**asdict(data.schema), "resolved": resolved}), end="")
                return 0
            result = profile(data, cfg)
        elif args.command in {"render", "export"}:
            result = ProfilingResult.load(args.input)
        else:
            result = compare(ProfilingResult.load(args.input), ProfilingResult.load(args.after))
        # Finish validation/computation/rendering before creating the directory.
        is_profile = result.document["kind"] == "profile"
        prefix = "report" if is_profile else "comparison"
        files = {prefix + ".md": render_markdown(result), prefix + ".html": render_html(result)}
        if args.command not in {"render", "export"}:
            files["guide-profile.json" if is_profile else "guide-comparison.json"] = result.to_json()
        binaries = {}
        if args.command == "export":
            from .exports import export_bundle
            binaries, status = export_bundle(result, args.formats,deck=args.deck)
            files['export-status.json'] = canonical_json(status)
        args.out.mkdir(parents=True, exist_ok=True)
        for name, contents in files.items():
            (args.out / name).write_text(contents, encoding="utf-8", newline="\n")
        for name, contents in binaries.items():
            (args.out / name).write_bytes(contents)
        print(f"guide: wrote {', '.join(str(args.out / name) for name in sorted([*files, *binaries]))}")
        if args.command == "profile":
            print(summary_line(result.document))
        if args.command == "export":
            for fmt, item in sorted(status["formats"].items()):
                if item["status"] == "unavailable":
                    print(f"guide: {fmt} not written: optional extra missing; from the repository clone run: pip install -e '.[exports]'", file=sys.stderr)
        return 0
    except (ValueError, OSError, UnicodeError, csv.Error, yaml.YAMLError) as exc:
        print(f"guide: {exc}", file=sys.stderr)
        return 2
