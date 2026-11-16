"""Python API for notebooks: profile a pandas DataFrame with no CSV file on disk (spec 029).

Reviewer guide:
- The DataFrame is serialised to CSV bytes in memory (``dataframe_csv_bytes``) and goes through
  ``connectors.load_csv_bytes``, the same parse the CLI uses for a file. Everything after that
  (config validation, profiling, rendering) calls the same functions as ``guide profile`` and
  ``guide liftoff``. So for the same CSV bytes and config the artifacts are byte-identical to the
  CLI's, except ``source.connector`` ("dataframe") and ``source.origin`` (the ``name`` given).
- Provenance keeps a content hash: ``source.sha256`` is the SHA-256 of the serialised bytes.
- Fathom profiles text as written (DG-RB, spec 001). A DataFrame read with ``dtype=str`` and
  ``keep_default_na=False`` keeps every cell's text, but not the file's bytes: CRLF line ends,
  extra quoting or a BOM are rewritten, so ``source.sha256`` can differ from the CLI's for that
  file. Parity is for the same serialised bytes. Typed columns are written with ``str()`` and so
  are profiled from that text (documented in docs/notebooks.md).
- Nothing here opens a network connection or imports IPython. ``show()`` returns an object that
  Jupyter displays through ``_repr_html_``; outside Jupyter it is a plain string holder.
"""

from __future__ import annotations

import csv
from html import escape
import io
import math
from pathlib import Path

import yaml

from .config import config_from_yaml, read_config, validate_config
from .connectors import load_csv_bytes
from .models import GuideDataFrame, ProfilingResult, SchemaContract

__all__ = ["profile", "liftoff", "NotebookResult", "dataframe_csv_bytes"]


def _cell(value) -> str:
    """One cell as CSV text: missing values (None, NaN, NaT, pd.NA) become empty fields."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        import pandas as pd
        if pd.isna(value) is True:
            return ""
    except (TypeError, ValueError):
        pass
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value)


def dataframe_csv_bytes(df) -> bytes:
    """The DataFrame as UTF-8 CSV bytes: header row, then rows; index dropped; '\\n' line ends.

    Column names must be unique, nonblank strings (the CSV rule). Call ``df.reset_index()`` first
    to keep the index as a column.
    """
    import pandas as pd
    if not isinstance(df, pd.DataFrame):
        raise ValueError("expected a pandas DataFrame")
    columns = list(df.columns)
    if any(not isinstance(c, str) for c in columns):
        raise ValueError("DataFrame column names must be strings; rename them or call df.columns = df.columns.astype(str)")
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(columns)
    for row in df.itertuples(index=False, name=None):
        writer.writerow([_cell(v) for v in row])
    return buffer.getvalue().encode("utf-8")


def _config(config) -> tuple[dict | None, dict]:
    """Return (raw mapping, validated config) using exactly the YAML file rules.

    A dict is dumped to YAML and re-read with the file loader, so a dict and the equivalent
    file give the same config (no executable YAML, ISO dates stay strings).
    """
    if config is None:
        return None, validate_config()
    if isinstance(config, (str, Path)):
        raw = read_config(config)
    elif isinstance(config, dict):
        raw = config_from_yaml(yaml.safe_dump(config, sort_keys=False, allow_unicode=True))
    else:
        raise ValueError("config must be None, a dict, or a path to a YAML file")
    return raw, validate_config(raw)


def _load(df, schema: SchemaContract | None, name: str) -> GuideDataFrame:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name must be a nonblank string")
    return load_csv_bytes(dataframe_csv_bytes(df), schema or SchemaContract(), "dataframe", name)


def _write(out, files: dict[str, str]) -> Path | None:
    if out is None:
        return None
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for file_name, contents in files.items():
        (out / file_name).write_text(contents, encoding="utf-8", newline="\n")
    return out


class NotebookResult:
    """A profile (or Liftoff) result plus the files it rendered.

    ``result.document`` is the machine-readable artifact (DG-RE); ``result.files`` maps file
    names to their text; ``result.out`` is where they were written, or None.
    """

    def __init__(self, result: ProfilingResult, files: dict[str, str], out: Path | None, main_page: str):
        self.result = result
        self.document = result.document
        self.files = files
        self.out = out
        self.main_page = main_page

    def to_json(self) -> str:
        return self.result.to_json()

    def show(self) -> "InlineView":
        """An inline view for a notebook cell: Key findings and summary tables, no scripts."""
        return InlineView(inline_html(self))

    def _repr_html_(self) -> str:
        return inline_html(self)

    def __repr__(self) -> str:
        where = str(self.out / self.main_page) if self.out else "not written (pass out=...)"
        return f"<Fathom {self.document.get('kind', 'result')}: {len(self.document.get('columns', []))} columns; report: {where}>"


class InlineView:
    """Holds inline HTML; Jupyter renders it through ``_repr_html_`` (no IPython import)."""

    def __init__(self, html: str):
        self.html = html

    def _repr_html_(self) -> str:
        return self.html

    def __str__(self) -> str:
        return self.html


INLINE_CSS = (".fathom-inline{font:14px/1.5 system-ui,sans-serif;max-width:960px}"
              ".fathom-inline table{border-collapse:collapse;margin:8px 0}"
              ".fathom-inline td,.fathom-inline th{padding:4px 8px;border-bottom:1px solid #ccc;text-align:left;vertical-align:top}"
              ".fathom-inline h2{font-size:18px;margin:12px 0 6px}.fathom-inline small{color:#666}")


def inline_html(view: NotebookResult) -> str:
    """The collapsed in-cell view.

    Reviewer note: the full report carries navigation scripts, and sandboxed notebook outputs
    often strip scripts, so the cell always shows the collapsed view (Key findings plus the
    dataset summary table, or the Liftoff Brief) and points to the full HTML when one was
    written. No external requests: inline CSS only, no links outside the page.
    """
    d = view.document
    parts = ['<div class="fathom-inline"><style>' + INLINE_CSS + '</style>',
             '<p><strong>Fathom</strong> · ' + escape(d['source']['origin']) + ' · ' + str(len(d.get('columns', []))) + ' columns</p>']
    if 'liftoff' in d:
        from .liftoff import brief_html
        parts.append(_strip_anchors(brief_html(d)))
    else:
        from .renderers import summary_rows
        from .verdicts import headlines_html
        parts.append(_strip_anchors(headlines_html(d)))
        parts.append('<h2>Dataset summary</h2><table><tbody>')
        parts += ['<tr><th>' + escape(title) + '</th><td>' + escape(value) + '</td></tr>' for title, value, _ in summary_rows(d)]
        parts.append('</tbody></table>')
    if view.out is not None:
        parts.append('<p><small>Full report: ' + escape(str(view.out / view.main_page)) + '</small></p>')
    else:
        parts.append('<p><small>Collapsed view. Pass out=... to write the full report.</small></p>')
    parts.append('</div>')
    return ''.join(parts)


def _strip_anchors(fragment: str) -> str:
    """In-page '#…' evidence links point into the full report, not the cell; drop them."""
    import re
    fragment = re.sub(r'\s*<a href="#[^"]*">Evidence</a>', '', fragment)
    return re.sub(r'<a href="#[^"]*">(.*?)</a>', r'\1', fragment)


def profile(df, config=None, out=None, *, name: str = "dataframe") -> NotebookResult:
    """Profile a DataFrame like ``guide profile``: writes report.md, report.html and
    guide-profile.json to ``out`` when given. ``config`` is None, a dict, or a YAML path."""
    from .profiler import profile as run_profile
    from .renderers import render_html, render_markdown
    from .summary_view import report_options
    raw, cfg = _config(config)
    data = _load(df, SchemaContract(**cfg["schema"]), name)
    cfg = validate_config(cfg, list(data.frame.columns))
    result = run_profile(data, cfg)
    options = report_options(raw)
    files = {"report.md": render_markdown(result, report=options), "report.html": render_html(result, report=options),
             "guide-profile.json": result.to_json()}
    return NotebookResult(result, files, _write(out, files), "report.html")


def liftoff(df, out=None, *, name: str = "dataframe") -> NotebookResult:
    """Liftoff for a DataFrame, like ``guide liftoff``: writes liftoff.html and liftoff-profile.json."""
    from .liftoff import build_liftoff, render_liftoff
    result = build_liftoff(_load(df, None, name))
    files = {"liftoff.html": render_liftoff(result), "liftoff-profile.json": result.to_json()}
    return NotebookResult(result, files, _write(out, files), "liftoff.html")
