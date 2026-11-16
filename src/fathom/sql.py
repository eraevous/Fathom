"""Opt-in SQL source: rows from a DB-API 2.0 connection the user opened (spec 030).

Reviewer guide:
- Fathom never opens a connection, never asks for or stores credentials, and imports no database
  driver. The caller's own code creates the connection and passes it in (``fathom.profile_query``)
  or names a factory the CLI calls (``guide profile --source sql --connect module:function``).
- The result rows are written as CSV text and parsed by ``connectors.load_csv_bytes``, the same
  parse as a CSV file and a DataFrame (spec 029). After that the pipeline is the CLI's.
- Size is declared: ``limit`` is required. Fathom fetches at most ``limit + 1`` rows and refuses the
  result if the extra row exists. It never rewrites the query (no push-down, no dialect guessing).
- Provenance (``source``): ``connector`` "sql", ``adapter`` (the driver's top-level module name,
  for example "sqlite3"), ``query`` (the text as given), ``row_limit`` and the content hash of the
  serialised rows. Never the connection, its arguments, or the factory's code.
"""

from __future__ import annotations

import csv
import importlib
import importlib.util
import io
from pathlib import Path

from .connectors import load_csv_bytes
from .models import GuideDataFrame, SchemaContract

__all__ = ["adapter_name", "query_csv_bytes", "load_query", "load_factory"]


def adapter_name(conn) -> str:
    """The driver's top-level module (``sqlite3.Connection`` -> "sqlite3"); no connection details."""
    module = type(conn).__module__ or "unknown"
    return module.split(".")[0].lstrip("_") or "unknown"


def _check_limit(limit) -> int:
    if type(limit) is not int or limit < 1:
        raise ValueError("limit is required: a whole number of rows of at least 1 (the declared table size)")
    return limit


def _cell(value, column: str) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise ValueError(f"column {column!r} returned binary data; select it as text (for example CAST(... AS TEXT)) or leave it out")
    return str(value)


def query_csv_bytes(conn, query: str, limit: int) -> bytes:
    """Run ``query`` on the user's connection; return the rows as UTF-8 CSV bytes.

    Header from ``cursor.description``; ``None`` becomes an empty field; other values use
    ``str()`` (as the DataFrame API does). Raises ValueError past ``limit`` rows.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be nonblank SQL text")
    limit = _check_limit(limit)
    cursor = conn.cursor()
    try:
        try:
            cursor.execute(query)
        except Exception as exc:  # DB-API errors are driver classes; report them as a usage error.
            raise ValueError(f"query failed ({type(exc).__name__}): {exc}") from None
        if not cursor.description:
            raise ValueError("query returned no result set; use a SELECT")
        columns = [str(d[0]) for d in cursor.description]
        rows = cursor.fetchmany(limit + 1)
        # fetchmany may return fewer than asked before the end; keep reading up to limit + 1.
        while len(rows) <= limit:
            more = cursor.fetchmany(limit + 1 - len(rows))
            if not more:
                break
            rows.extend(more)
    finally:
        cursor.close()
    if len(rows) > limit:
        raise ValueError(f"query returned more than the row limit ({limit}); raise the limit or narrow the query")
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(columns)
    for row in rows:
        writer.writerow([_cell(v, c) for v, c in zip(row, columns)])
    return buffer.getvalue().encode("utf-8")


def load_query(conn, query: str, limit: int, schema: SchemaContract | None = None,
               name: str = "sql query") -> GuideDataFrame:
    """Query rows -> GuideDataFrame through the shared CSV parse, with SQL provenance."""
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name must be a nonblank string")
    raw = query_csv_bytes(conn, query, limit)
    data = load_csv_bytes(raw, schema or SchemaContract(), "sql", name)
    data.source.update({"adapter": adapter_name(conn), "query": query, "row_limit": limit})
    return data


def load_factory(spec: str):
    """Resolve ``module:function`` or ``path/to/file.py:function`` to the user's factory.

    Fathom calls it with no arguments; it returns an open DB-API connection. Credentials stay in
    the user's code or environment; Fathom never reads or records them.
    """
    target, sep, attr = spec.rpartition(":")
    if not sep or not target or not attr.isidentifier():
        raise ValueError("--connect must be module:function or path/to/file.py:function")
    if target.endswith(".py"):
        path = Path(target)
        if not path.is_file():
            raise ValueError(f"connection factory file not found: {path}")
        module_spec = importlib.util.spec_from_file_location("fathom_user_connect", path)
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
    else:
        try:
            module = importlib.import_module(target)
        except ImportError as exc:
            raise ValueError(f"cannot import connection factory module {target!r}: {exc}") from None
    factory = getattr(module, attr, None)
    if not callable(factory):
        raise ValueError(f"{spec!r} is not a callable connection factory")
    return factory
