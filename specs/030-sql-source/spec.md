# 030: Opt-in SQL source over a user-supplied DB-API connection

Handoff HO-DG-20261106-NZ0P, PR 2 of 2 (PR 1, the notebook API, is spec 029, merged as #51). Owner request, Zach 2026-11-06: "… or have a [data warehouse] connector" (product name redacted per Zach 2026-11-15). The handoff narrows it to a generic, opt-in source: the user opens the connection; Fathom never does.

Proposed for Zach. Serves: P0@2, DG-RE@1, DG-RF@1.

## US1: Profile a query from Python (P1)

- `fathom.profile_query(conn, query, limit, out=None, config=None, *, name="sql query")`. `conn` is any DB-API 2.0 connection the caller opened.
- The rows are written as CSV text (header from `cursor.description`; `None` as an empty field; other values with `str()`, as in spec 029) and parsed by `connectors.load_csv_bytes`, the same parse as a file and a DataFrame. After that the pipeline is `guide profile`'s, so the measurements equal `fathom.profile` on the same rows; only `source` differs.

## US2: The same from the CLI (P1)

- `guide profile --source sql --connect MODULE:FUNC --query "SELECT …" --limit N --out DIR` (also `path/to/file.py:FUNC`). Fathom calls the factory with no arguments, profiles the query, and closes the connection.
- `--source sql` requires `--connect`, `--query` and `--limit`, and takes no input file; the SQL flags without `--source sql` are an error. `--source csv` (the default) is unchanged.

## Credentials and provenance

- Fathom never asks for, stores, logs or writes credentials. The factory lives in the user's code.
- `source` records `connector: "sql"`, `adapter` (the driver's top-level module, e.g. `sqlite3`), `query` (as given), `row_limit`, `origin` (`name`) and `sha256` of the serialised rows. Never the connection, the factory spec, its arguments or its environment.
- The query text is recorded verbatim and appears in the reports; the doc page warns against putting secrets or sensitive literals in it (stress-test, 2026-11-16).
- A factory module that raises while loading, while its factory attribute is looked up, or when the factory is called is reported by exception type only; its message is withheld, since it may echo connection details. A query error is reported with the driver's message (it concerns the SQL).

## Size

- `limit` is required (a whole number ≥ 1) and recorded. Fathom fetches at most `limit + 1` rows; one more than the limit is an error naming the limit. No silent truncation, and the query is never rewritten (no push-down, no dialect handling).

## Network and drivers

- Fathom opens no connection itself; the CLI form passes the all-sockets-blocked harness. Importing `fathom`, `fathom.api`, `fathom.sql` and `fathom.cli` imports no database driver (not even `sqlite3`).
- Adapter shipped and tested: SQLite from the standard library, through the generic path. No vendor-specific adapter. DuckDB (an optional extra in the handoff) is not added: it would be a new dependency, and its DB-API connection already works through the generic path; narrower reading, recorded.

## Read-only guard (Copilot review, 2026-11-16)

- Before executing, Fathom refuses a query whose first keyword (after comments) isn't `SELECT`, `WITH` or `VALUES`, or that has a second statement after `;`. A small scanner skips string literals, quoted identifiers and comments. Nothing is executed when the query is refused.
- This is a guard, not a guarantee. The docs ask for a read-only connection.
- Quoting and comments differ between databases (backslash escapes, `` `backticks` ``, `[brackets]`, `$tag$` dollar quotes with tags of any letters, MySQL `#` comments and `--` needing a following space, nested `/* */` comments in PostgreSQL and SQL Server). The scanner reads the query under every combination of these rules, since real dialects combine them, and refuses it if any reading finds a non-read start or a second statement. A MySQL `/*! */` or `/*+ */` comment is read as code. This fails closed: a `;` inside such a quote or comment may be refused even where the database would accept it (security sweep and Copilot review, #55, 2026-11-17).

## Errors

Blank query, a non-read or multi-statement query (refused before running), no result set, driver errors while executing or fetching, binary columns (select them as text), duplicate or blank column names, and a bad `--connect` spec all raise a clear `ValueError` (CLI exit 2).

## Tests

`tests/test_sql_source.py`, SQLite fixtures in `tmp_path` only (no live service): rows serialise exactly as the DataFrame; measurements equal `fathom.profile`; provenance fields; the row cap (required, enforced, recorded); bad queries; CLI argument rules; the no-secrets scan (a fake password held by the factory appears in no output file or printed line, including when the factory fails); no driver imported; the CLI SQL path under the all-sockets-blocked harness. Run: `python -m pytest tests/test_sql_source.py`.

## Unchanged

CSV and DataFrame behaviour and artifacts, `liftoff`, determinism and offline behaviour.
