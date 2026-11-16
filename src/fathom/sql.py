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
import re
import sys

from .connectors import load_csv_bytes
from .models import GuideDataFrame, SchemaContract

__all__ = ["adapter_name", "check_read_query", "query_csv_bytes", "load_query", "load_factory"]


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


READ_KEYWORDS = ("select", "with", "values")


def _code_outside_literals(query: str) -> str:
    """The query with string literals, quoted identifiers and comments blanked out.

    A small scanner, not a SQL parser: '...' and "..." (doubled quotes escape), -- line comments
    and /* */ block comments. Enough to find the first keyword and a second statement.
    """
    out, i, n = [], 0, len(query)
    while i < n:
        c = query[i]
        if c in "'\"":
            j = i + 1
            while j < n:
                if query[j] == c:
                    if j + 1 < n and query[j + 1] == c:
                        j += 2
                        continue
                    break
                j += 1
            out.append(" ")
            i = j + 1
        elif query.startswith("--", i):
            j = query.find("\n", i)
            i = n if j < 0 else j
            out.append(" ")
        elif query.startswith("/*", i):
            j = query.find("*/", i + 2)
            i = n if j < 0 else j + 2
            out.append(" ")
        else:
            out.append(c)
            i += 1
    return "".join(out)


def check_read_query(query: str) -> None:
    """Refuse, before anything runs, SQL that is not a single SELECT / WITH / VALUES statement.

    A guard, not a guarantee (Copilot review, #53): a dialect may allow writes inside WITH, and a
    function called by a SELECT can have side effects. The real protection is a read-only
    connection, which the docs ask for.
    """
    code = _code_outside_literals(query)
    first_word = re.match(r"[\s(]*([A-Za-z_]+)", code)  # a token boundary, so "SELECT*" reads as SELECT (Codex review)
    if not first_word or first_word.group(1).lower() not in READ_KEYWORDS:
        raise ValueError("only a read query is run: it must start with SELECT, WITH or VALUES (nothing was executed)")
    first, sep, rest = code.partition(";")
    if sep and rest.strip(" \t\r\n;"):
        raise ValueError("only one statement is run; remove everything after the first ';' (nothing was executed)")


def _driver_error(step: str, exc: Exception) -> ValueError:
    return ValueError(f"query failed while {step} ({type(exc).__name__}): {exc}")


def query_csv_bytes(conn, query: str, limit: int) -> bytes:
    """Run ``query`` on the user's connection; return the rows as UTF-8 CSV bytes.

    Header from ``cursor.description``; ``None`` becomes an empty field; other values use
    ``str()`` (as the DataFrame API does). Raises ValueError past ``limit`` rows.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be nonblank SQL text")
    limit = _check_limit(limit)
    check_read_query(query)
    cursor = conn.cursor()
    try:
        # DB-API errors are driver classes; every driver call reports them as a usage error.
        try:
            cursor.execute(query)
        except Exception as exc:
            raise _driver_error("executing", exc) from None
        if not cursor.description:
            raise ValueError("query returned no result set; use a SELECT")
        columns = [str(d[0]) for d in cursor.description]
        try:
            rows = list(cursor.fetchmany(limit + 1))  # DB-API allows any sequence (e.g. a tuple)
            # fetchmany may return fewer than asked before the end; keep reading up to limit + 1.
            while len(rows) <= limit:
                more = cursor.fetchmany(limit + 1 - len(rows))
                if not more:
                    break
                rows.extend(more)
        except Exception as exc:
            raise _driver_error("fetching rows", exc) from None
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
    if target.endswith(".py") and not Path(target).is_file():
        raise ValueError(f"connection factory file not found: {target}")
    try:
        if target.endswith(".py"):
            # Registered in sys.modules while it runs, as a normal import would be (dataclasses and
            # similar look the module up there; Copilot review, #53). Removed again on failure.
            name = "fathom_user_connect"
            module_spec = importlib.util.spec_from_file_location(name, target)
            module = importlib.util.module_from_spec(module_spec)
            previous = sys.modules.get(name)
            sys.modules[name] = module
            try:
                module_spec.loader.exec_module(module)
            except BaseException:
                if previous is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = previous
                raise
        else:
            module = importlib.import_module(target)
        factory = getattr(module, attr, None)
    except ModuleNotFoundError as exc:
        if exc.name and target.startswith(exc.name):
            raise ValueError(f"cannot import connection factory module {target!r}: module not found") from None
        raise ValueError(f"loading connection factory {target!r} raised ModuleNotFoundError; message withheld so no connection details are printed") from None
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        # The user's module holds connection details; its import-time message may echo them (Codex review, #53).
        raise ValueError(f"loading connection factory {target!r} raised {type(exc).__name__}; message withheld so no connection details are printed") from None
    if not callable(factory):
        raise ValueError(f"{spec!r} is not a callable connection factory")
    return factory
