"""Local CSV bundle composition; tables remain independent profiling artifacts."""

import csv
from hashlib import sha256
from html import escape
import json
from pathlib import Path, PurePosixPath
import re

from .config import validate_config
from .connectors import CSVConnector
from .models import SchemaContract, canonical_json
from .profiler import profile
from .renderers import render_html, render_markdown
from .summary_view import report_options


def read_manifest(raw: bytes) -> dict:
    """Reject ambiguous manifests before reading any data or writing outputs."""
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate manifest key: ' + key)
            result[key] = value
        return result

    doc = json.loads(raw, object_pairs_hook=unique_object)
    if not isinstance(doc, dict) or set(doc) != {'version', 'tables'}:
        raise ValueError('bundle requires only version and tables')
    if type(doc['version']) is not int or doc['version'] != 1:
        raise ValueError('unsupported bundle version')
    if not isinstance(doc['tables'], list) or not doc['tables']:
        raise ValueError('bundle requires a nonempty tables list')
    seen = set()
    for table in doc['tables']:
        if (not isinstance(table, dict) or not {'id', 'path'} <= table.keys()
                or table.keys() - {'id', 'path', 'config'}):
            raise ValueError('table requires id/path and optional inline config')
        name = table['id']
        if not isinstance(name, str) or not re.fullmatch(r'[a-z][a-z0-9_-]{0,63}', name):
            raise ValueError('table id must be a portable lowercase identifier')
        if name in {'con', 'prn', 'aux', 'nul'} or re.fullmatch(r'(com|lpt)[0-9]', name):
            raise ValueError('table id is reserved on Windows')
        if name in seen:
            raise ValueError('duplicate table id: ' + name)
        seen.add(name)
        if not isinstance(table['path'], str):
            raise ValueError('table path must be a string')
        if 'config' in table and not isinstance(table['config'], dict):
            raise ValueError('table config must be an inline object')
    return doc


def local_source(root: Path, value: str) -> Path:
    """Confine ordinary local reads; this is not an adversarial filesystem sandbox."""
    path = PurePosixPath(value)
    if (not value or path.is_absolute() or '..' in path.parts
            or '\\' in value or ':' in value or '\x00' in value):
        raise ValueError('source must be a confined relative local path')
    resolved = (root / value).resolve()
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError('source is missing, not a file, or outside the bundle root')
    return resolved


def render_index(index: dict) -> str:
    """Render only the bundle index, not data or independently computed findings."""
    rows = []
    for table in index['tables']:
        name = escape(table['id'])
        if table['status'] == 'ok':
            detail = '<a href="' + escape(table['report'], quote=True) + '">Open report</a>'
        else:
            detail = 'Unavailable: ' + escape(table['error'])
        rows.append('<li><h2>' + name + '</h2><p>' + detail + '</p><p>Row unit: '
                    + escape(table.get('row_unit') or 'unknown (not declared)') + '</p></li>')
    return ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>Fathom bundle</title><style>body{font:1rem system-ui;max-width:60rem;'
            'margin:2rem auto;padding:1rem;overflow-wrap:anywhere}li{margin-bottom:2rem}</style>'
            '<h1>Fathom bundle</h1><p>Independent table profiles. No joins or relationships '
            'have been inferred. Failed tables are not evidence of clean data.</p>'
            '<p><a href="bundle-index.json">Machine-readable index and source hashes</a></p><ul>'
            + ''.join(rows) + '</ul></html>\n')


def build_bundle(manifest: Path, out: Path) -> dict:
    """Profile each table; publish to a new directory so stale reports cannot linger."""
    raw = manifest.read_bytes()
    doc = read_manifest(raw)
    if out.exists() or out.is_symlink():
        raise ValueError('bundle output must be a new directory; choose another --out')
    root = manifest.resolve().parent
    index = {'version': 1, 'kind': 'csv-bundle-index',
             'manifest_sha256': sha256(raw).hexdigest(), 'tables': []}
    files = {}
    for table in doc['tables']:
        name = table['id']
        entry = {'id': name, 'path': table['path'], 'status': 'error', 'row_unit': None}
        index['tables'].append(entry)
        try:
            source = local_source(root, table['path'])
            cfg = validate_config(table.get('config'))
            data = CSVConnector(source, SchemaContract(**cfg['schema'])).load()
            # Relative provenance makes copied bundles reproducible and avoids host paths.
            data.source['origin'] = table['path']
            entry['sha256'] = data.source['sha256']
            result = profile(data, validate_config(cfg, list(data.frame.columns)))
            options = report_options(table.get('config'))
            artifacts = {'guide-profile.json': result.to_json(),
                         'report.html': render_html(result, report=options),
                         'report.md': render_markdown(result, report=options)}
            files.update({name + '/' + key: value for key, value in artifacts.items()})
            entry.update(status='ok', row_unit=result.document['working_record'].get('row_unit'),
                         report=name + '/report.html', profile=name + '/guide-profile.json')
        except (ValueError, OSError, UnicodeError, csv.Error) as exc:
            # Stable category; exception strings can leak absolute paths/source values.
            entry['error'] = type(exc).__name__ + ': source, configuration or profile failed validation'
    files['bundle-index.json'] = canonical_json(index)
    files['index.html'] = render_index(index)
    out.mkdir(parents=True, exist_ok=False)
    for name, text in files.items():
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8', newline='\n')
    return index
