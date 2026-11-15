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
    categories = {"by config": [], "unsupported type": [], "budget": [], "other eligibility": []}
    for entry in ta.get("excluded", []):
        reason = entry.get("reason", "unspecified")
        if reason == "target column": continue
        category = (
            "by config" if reason.startswith(("target excluded by config", "excluded by config:"))
            else "unsupported type" if reason.startswith("unsupported type")
            else "budget" if reason == "pair budget exhausted"
            else "other eligibility"
        )
        item = entry["column"] + " (" + reason + ")"
        if item not in categories[category]: categories[category].append(item)
    target = (f"target: {ta['target']}; excluded from target " + "; ".join(k + ": " + (", ".join(v) or "none") for k,v in categories.items())
              if ta.get("target") else "target: not declared")
    return (f"guide: question: {purpose.get('question') or 'none declared'}; {target}; "
            f"row unit: {record.get('row_unit') or 'unknown (not declared)'}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="guide", description="Evidenced local table review")
    parser.add_argument("--version", action="version", version=f"guide {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    helps = {"bundle": "profile independent local CSV tables from a JSON manifest; no joins", "serve": "edit configuration and rerun a startup-fixed CSV on authenticated 127.0.0.1 only", "liftoff": "inspect a CSV without config; write a Brief + Configurations HTML page and its profile", "configure": "write configure.html, a self-contained page that builds a YAML config from this table's profile "
                          "(defaults, observable suggestions, explicit selections), and configure-profile.json, the profile it used"}
    for command in ("profile", "render", "compare", "validate", "export", "configure", "liftoff", "panel", "serve", "bundle"):
        sub = commands.add_parser(command, help=helps.get(command), description=helps.get(command))
        sub.add_argument("input", type=Path)
        if command == "serve":
            sub.add_argument("--host", default="127.0.0.1", choices=("127.0.0.1",))
            sub.add_argument("--idle-timeout", type=float, default=1800, help="idle expiry in seconds (default 1800)")
        if command == "compare":
            sub.add_argument("after", type=Path)
        if command in {"profile", "validate", "configure", "panel", "render", "export", "serve"}:
            sub.add_argument("--config", type=Path, required=command == 'panel', help=("presentation options only; saved measurements are unchanged" if command in {"render","export"} else "existing YAML config") + ("; its values start the page as 'existing config'" if command == "configure" else ""))
        if command == 'liftoff':
            sub.add_argument('--yaml', type=Path, help='write exactly the page default selection as YAML; no suggestions applied')

        if command == 'panel':
            sub.add_argument('--aggregate', help='separate week,month views from daily input')
        if command != "validate":
            sub.add_argument("--out", type=Path, required=command!="export")
        if command == "export":
            sub.add_argument("--formats", nargs="+", choices=("pdf", "pptx"), default=None)
            sub.add_argument("--tidy",type=Path,help="write saved-profile columns/findings/relations/samples CSVs; no Office extra required")
            sub.add_argument("--deck",choices=("summary","full"),default="summary")
    args = parser.parse_args(argv)
    if args.command=='export' and args.out is None and args.tidy is None:parser.error('export needs --out or --tidy')
    if args.command=='export' and args.formats and args.out is None:parser.error('--formats requires --out')
    try:
        if args.command == "bundle":
            from .bundle import build_bundle
            index = build_bundle(args.input, args.out)
            failed = sum(t["status"] != "ok" for t in index["tables"])
            print(f"guide: bundle written; {failed} table(s) failed; no joins performed")
            return 2 if failed else 0
        if args.command == "serve":
            from .serve import run
            return run(args.input, args.out, args.config, host=args.host, idle_timeout=args.idle_timeout)
        from .summary_view import report_options
        options=report_options(read_config(args.config) if getattr(args,'config',None) else None)
        if args.command == 'panel':
            from .panel import build_panel, panel_files
            raw = read_config(args.config)
            if args.aggregate is not None:
                raw['aggregate'] = args.aggregate.split(',')
            result = build_panel(CSVConnector(args.input).load(), raw, args.config.parent)
            files = panel_files(result)
            args.out.mkdir(parents=True, exist_ok=True)
            for name, contents in files.items():
                path = args.out / name;path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(contents, encoding='utf-8', newline='\n')
            print(f'guide: wrote {len(files)} local panel files; all signals training-only')
            return 0
        if args.command == "liftoff":
            from .liftoff import build_liftoff, render_liftoff
            if args.yaml is not None:
                protected = (args.input, args.out / 'liftoff.html', args.out / 'liftoff-profile.json')
                if any(
                    args.yaml.resolve() == path.resolve() or
                    (args.yaml.exists() and path.exists() and args.yaml.samefile(path))
                    for path in protected
                ):
                    raise ValueError('--yaml must not overwrite the source or standard Liftoff artifacts')
            result = build_liftoff(CSVConnector(args.input).load())
            page = render_liftoff(result)
            args.out.mkdir(parents=True, exist_ok=True)
            for name, contents in (("liftoff.html", page), ("liftoff-profile.json", result.to_json())):
                (args.out / name).write_text(contents, encoding="utf-8", newline="\n")
            if args.yaml is not None:
                from .configure import config_yaml
                schema = result.document['liftoff']['configuration']
                args.yaml.parent.mkdir(parents=True, exist_ok=True)
                args.yaml.write_text(config_yaml(schema, schema['initial']), encoding='utf-8', newline='\n')
            print(f"guide: wrote {args.out / 'liftoff-profile.json'}, {args.out / 'liftoff.html'}; no suggestions applied")
            if args.yaml is not None: print(f"guide: wrote {args.yaml}; exact page defaults; edit YAML to declare choices")
            return 0
        if args.command == "configure":
            from .configure import build_schema, render_page
            raw = read_config(args.config) if args.config else None
            cfg = validate_config(raw)
            data = CSVConnector(args.input, SchemaContract(**cfg["schema"])).load()
            result = profile(data, validate_config(cfg, list(data.frame.columns)))
            schema = build_schema(result.document, data.frame, raw)
            page = render_page(schema)
            args.out.mkdir(parents=True, exist_ok=True)
            for name, contents in (("configure.html", page), ("configure-profile.json", result.to_json())):
                (args.out / name).write_text(contents, encoding="utf-8", newline="\n")
            print(f"guide: wrote {args.out / 'configure-profile.json'}, {args.out / 'configure.html'}")
            print(f"guide: time_series: {len(schema['series_suggestions'])} series offered unticked; max_lag and top_n are not offered by the page "
                  "(declare them directly in YAML)")
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
            if args.config:validate_config(read_config(args.config)) # syntax only, no analysis declarations applied
            if args.command=='export' and args.tidy is not None:
                from .tidy import tidy_files
                tidy=tidy_files(result.document)
                if args.out is None:
                    args.tidy.mkdir(parents=True,exist_ok=True)
                    for name,value in tidy.items():(args.tidy/name).write_text(value,encoding='utf-8',newline='\n')
                    print('guide: wrote '+', '.join(str(args.tidy/name) for name in sorted(tidy)))
                    return 0
            if result.document['kind'] == 'panel':
                if args.command == 'export': raise ValueError('panel Office export is not supported; use panel CSV/HTML')
                from .panel import panel_files
                files = panel_files(result)
                for name, text in files.items():
                    path = args.out / name;path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(text, encoding='utf-8', newline='\n')
                return 0
        else:
            result = compare(ProfilingResult.load(args.input), ProfilingResult.load(args.after))
        if args.command == "render" and "liftoff" in result.document:
            from .liftoff import render_liftoff
            page = render_liftoff(result)
            args.out.mkdir(parents=True, exist_ok=True)
            (args.out / "liftoff.html").write_text(page, encoding="utf-8", newline="\n")
            print(f"guide: wrote {args.out / 'liftoff.html'}")
            return 0
        # Finish validation/computation/rendering before creating the directory.
        is_profile = result.document["kind"] == "profile"
        prefix = "report" if is_profile else "comparison"
        files = {prefix + ".md": render_markdown(result,report=options), prefix + ".html": render_html(result,report=options)}
        if args.command not in {"render", "export"}:
            files["guide-profile.json" if is_profile else "guide-comparison.json"] = result.to_json()
        binaries = {}
        if args.command == "export":
            from .exports import export_bundle
            binaries, status = export_bundle(result, args.formats or ["pdf","pptx"],deck=args.deck,report=options)
            files['export-status.json'] = canonical_json(status)
        args.out.mkdir(parents=True, exist_ok=True)
        for name, contents in files.items():
            (args.out / name).write_text(contents, encoding="utf-8", newline="\n")
        for name, contents in binaries.items():
            (args.out / name).write_bytes(contents)
        print(f"guide: wrote {', '.join(str(args.out / name) for name in sorted([*files, *binaries]))}")
        if args.command=='export' and args.tidy is not None:
            args.tidy.mkdir(parents=True,exist_ok=True)
            for name,value in tidy.items():(args.tidy/name).write_text(value,encoding='utf-8',newline='\n')
            print('guide: wrote '+', '.join(str(args.tidy/name) for name in sorted(tidy)))
        if args.command == "profile":
            print(summary_line(result.document), file=sys.stderr)
            from .parsing import temporal_failure_message
            for column in result.document['columns']:
                failure=column['statistics'].get('parse_failure')
                if failure:print('guide: '+temporal_failure_message(column['name'],failure),file=sys.stderr)
        if args.command == "export":
            for fmt, item in sorted(status["formats"].items()):
                if item["status"] == "unavailable":
                    print(f"guide: {fmt} not written: optional extra missing; from the repository clone run: pip install -e '.[exports]'", file=sys.stderr)
        return 0
    except (ValueError, OSError, UnicodeError, csv.Error, yaml.YAMLError) as exc:
        print(f"guide: {exc}", file=sys.stderr)
        return 2
