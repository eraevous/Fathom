"""Spec 030: an opt-in SQL source over a DB-API connection the user opens (SQLite fixtures only).

No live service: every database here is a SQLite file built from a synthetic fixture in tmp_path.
Run alone with: python -m pytest tests/test_sql_source.py
"""
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pandas as pd
import pytest

import fathom
from fathom.api import dataframe_csv_bytes
from fathom.cli import main
from fathom.sql import adapter_name, query_csv_bytes

ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "tests/fixtures"
SECRET = "fixture-pw-7Kq2-not-real"
QUERY = 'SELECT id, amount, "group", "when", flag FROM review ORDER BY rowid'


def build_db(tmp_path) -> tuple[Path, pd.DataFrame]:
    """review.csv as an all-TEXT SQLite table; empty cells stored as NULL."""
    frame = pd.read_csv(FIXTURES / "review.csv", dtype=str, keep_default_na=False)
    path = tmp_path / "review.db"
    with sqlite3.connect(path) as conn:
        cols = ", ".join(f'"{c}" TEXT' for c in frame.columns)
        conn.execute(f"CREATE TABLE review ({cols})")
        conn.executemany(f"INSERT INTO review VALUES ({', '.join('?' * len(frame.columns))})",
                         [[v if v != "" else None for v in row] for row in frame.itertuples(index=False, name=None)])
    conn.close()
    return path, frame


def write_factory(tmp_path, db: Path, *, fail: bool = False) -> Path:
    """A user's connection factory holding a fake password, as real factories hold credentials."""
    body = (f"import sqlite3\nPASSWORD = {SECRET!r}\n"
            "def make_conn():\n"
            + (f"    raise RuntimeError('login failed for password ' + PASSWORD)\n" if fail else
               f"    return sqlite3.connect('file:{db.as_posix()}?mode=ro&password=' + PASSWORD, uri=True)\n"))
    path = tmp_path / "connect_fixture.py"
    path.write_text(body, encoding="utf-8")
    return path


def without_source(text: str) -> dict:
    doc = json.loads(text)
    doc.pop("source")
    return doc


def test_query_rows_serialise_like_the_dataframe(tmp_path):
    db, frame = build_db(tmp_path)
    with sqlite3.connect(db) as conn:
        assert query_csv_bytes(conn, QUERY, 100) == dataframe_csv_bytes(frame)
        assert adapter_name(conn) == "sqlite3"
    conn.close()


def test_profile_query_matches_dataframe_profile_except_source(tmp_path):
    db, frame = build_db(tmp_path)
    conn = sqlite3.connect(db)
    try:
        sql = fathom.profile_query(conn, QUERY, limit=100, out=tmp_path / "sql", config=FIXTURES / "review.yaml")
    finally:
        conn.close()
    df = fathom.profile(frame, config=FIXTURES / "review.yaml", name="sql query")
    sql_doc, df_doc = json.loads(sql.files["guide-profile.json"]), json.loads(df.files["guide-profile.json"])
    assert without_source(sql.files["guide-profile.json"]) == without_source(df.files["guide-profile.json"])
    assert sql_doc["source"] == {"connector": "sql", "origin": "sql query", "sha256": df_doc["source"]["sha256"],
                                 "adapter": "sqlite3", "query": QUERY, "row_limit": 100}
    assert (tmp_path / "sql" / "report.html").is_file()
    for line in ("  - Adapter: sqlite3", "  - Connector: sql", "  - Row limit: 100", "  - Query: SELECT id, amount"):
        assert line in sql.files["report.md"], line


def test_row_cap_is_required_and_enforced(tmp_path):
    db, frame = build_db(tmp_path)
    rows = len(frame)
    conn = sqlite3.connect(db)
    try:
        for bad in (None, 0, -1, 2.5, True):
            with pytest.raises(ValueError, match="limit is required"):
                fathom.profile_query(conn, QUERY, limit=bad)
        with pytest.raises(ValueError, match=f"more than the row limit \\({rows - 1}\\)"):
            fathom.profile_query(conn, QUERY, limit=rows - 1)
        assert json.loads(fathom.profile_query(conn, QUERY, limit=rows).to_json())["source"]["row_limit"] == rows
    finally:
        conn.close()


def test_bad_queries_raise_clear_errors(tmp_path):
    db, _ = build_db(tmp_path)
    conn = sqlite3.connect(db)
    try:
        with pytest.raises(ValueError, match="nonblank"):
            fathom.profile_query(conn, "  ", limit=5)
        with pytest.raises(ValueError, match=r"query failed \(OperationalError\)"):
            fathom.profile_query(conn, "SELECT * FROM missing", limit=5)
        with pytest.raises(ValueError, match="no result set"):
            fathom.profile_query(conn, "CREATE TEMP TABLE t (a)", limit=5)
        with pytest.raises(ValueError, match="binary data"):
            fathom.profile_query(conn, "SELECT X'00ff' AS blob", limit=5)
        with pytest.raises(ValueError, match="unique, nonblank column headers"):
            fathom.profile_query(conn, "SELECT 1 AS a, 2 AS a", limit=5)
    finally:
        conn.close()


def test_cli_sql_source_writes_profile_and_no_secrets(tmp_path, capsys):
    db, frame = build_db(tmp_path)
    factory = write_factory(tmp_path, db)
    out = tmp_path / "out"
    assert main(["profile", "--source", "sql", "--connect", f"{factory}:make_conn", "--query", QUERY,
                 "--limit", "100", "--out", str(out)]) == 0
    printed = capsys.readouterr()
    doc = json.loads((out / "guide-profile.json").read_text(encoding="utf-8"))
    assert doc["source"]["connector"] == "sql" and doc["source"]["query"] == QUERY and doc["source"]["row_limit"] == 100
    assert without_source((out / "guide-profile.json").read_text()) == without_source(fathom.profile(frame, name="sql query").files["guide-profile.json"])
    # No-secrets rule: the factory's password reaches no output file and no printed line.
    for path in out.rglob("*"):
        assert SECRET not in path.read_text(encoding="utf-8"), path.name
        assert "password" not in path.read_text(encoding="utf-8").lower(), path.name
    assert SECRET not in printed.out + printed.err


def test_cli_withholds_a_failing_factorys_message(tmp_path, capsys):
    db, _ = build_db(tmp_path)
    factory = write_factory(tmp_path, db, fail=True)
    code = main(["profile", "--source", "sql", "--connect", f"{factory}:make_conn", "--query", QUERY,
                 "--limit", "100", "--out", str(tmp_path / "out")])
    err = capsys.readouterr().err
    assert code == 2 and "RuntimeError" in err and "withheld" in err and SECRET not in err
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("args, message", [
    (["--source", "sql", "--query", QUERY, "--limit", "5"], "requires --connect"),
    (["--source", "sql", "--connect", "m:f", "--query", QUERY], "requires --limit"),
    (["data.csv", "--source", "sql", "--connect", "m:f", "--query", QUERY, "--limit", "5"], "takes no input file"),
    (["data.csv", "--limit", "5"], "--limit need --source sql"),
    ([], "needs an input CSV"),
])
def test_cli_argument_rules(tmp_path, capsys, args, message):
    with pytest.raises(SystemExit) as exit_info:
        main(["profile", *args, "--out", str(tmp_path / "out")])
    assert exit_info.value.code == 2 and message in capsys.readouterr().err


def test_cli_bad_factory_specs(tmp_path, capsys):
    for spec, message in (("nocolon", "module:function"), ("no_such_module_fathom:f", "cannot import"),
                          (str(tmp_path / "missing.py") + ":f", "not found")):
        assert main(["profile", "--source", "sql", "--connect", spec, "--query", QUERY, "--limit", "5",
                     "--out", str(tmp_path / "out")]) == 2
        assert message in capsys.readouterr().err


def test_importing_fathom_imports_no_database_driver():
    code = ("import sys, fathom, fathom.api, fathom.sql, fathom.cli, fathom.profiler, fathom.renderers\n"
            "print(sorted(m for m in sys.modules if m.split('.')[0] in "
            "('sqlite3', '_sqlite3', 'duckdb', 'psycopg', 'psycopg2', 'pyodbc', 'pymysql', 'sqlalchemy')))")
    out = subprocess.run([sys.executable, "-c", code], env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
                         capture_output=True, text=True, check=True).stdout.strip()
    assert out == "[]"


def test_cli_sql_source_runs_with_all_sockets_blocked(tmp_path):
    db, _ = build_db(tmp_path)
    factory = write_factory(tmp_path, db)
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "FATHOM_DENY_NETWORK": "1", "PYTHONHASHSEED": "19"}
    r = subprocess.run([sys.executable, str(ROOT / "tests/offline_runner.py"), "profile", "--source", "sql",
                        "--connect", f"{factory}:make_conn", "--query", QUERY, "--limit", "100", "--out", str(tmp_path / "out")],
                       env=env, capture_output=True)
    assert r.returncode == 0, r.stderr.decode()
    assert (tmp_path / "out" / "guide-profile.json").is_file()


def test_cli_withholds_a_factory_modules_import_time_error(tmp_path, capsys):
    """Codex review #53: a module that raises on import must not print its message either."""
    for exc in ("ValueError", "RuntimeError", "ImportError"):
        module = tmp_path / f"bad_{exc}.py"
        module.write_text(f"raise {exc}('login failed: password={SECRET}')\n", encoding="utf-8")
        code = main(["profile", "--source", "sql", "--connect", f"{module}:make_conn", "--query", QUERY,
                     "--limit", "5", "--out", str(tmp_path / "out")])
        err = capsys.readouterr().err
        assert code == 2 and exc in err and "withheld" in err and SECRET not in err


class TupleBatchCursor:
    """A DB-API cursor that returns tuple batches, short ones first (allowed by PEP 249)."""
    description = (("a", None, None, None, None, None, None),)

    def __init__(self, rows):
        self.rows = list(rows)

    def execute(self, query):
        pass

    def fetchmany(self, size):
        batch, self.rows = tuple(self.rows[:min(size, 2)]), self.rows[min(size, 2):]
        return batch

    def close(self):
        pass


class TupleBatchConnection:
    def __init__(self, rows):
        self.rows = rows

    def cursor(self):
        return TupleBatchCursor(self.rows)


def test_short_tuple_batches_are_accumulated():
    """Codex review #53: fetchmany may return tuples, and fewer rows than asked."""
    rows = [(str(i),) for i in range(5)]
    assert query_csv_bytes(TupleBatchConnection(rows), "SELECT a", 5) == b"a\n0\n1\n2\n3\n4\n"
    with pytest.raises(ValueError, match="more than the row limit"):
        query_csv_bytes(TupleBatchConnection(rows), "SELECT a", 4)
