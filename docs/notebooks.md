# Fathom in a notebook

Fathom runs inside a Jupyter notebook, including a hosted one, with nothing that needs admin rights. It opens no network connection: the install step is the only one that downloads anything.

## Install into the notebook's own kernel

Run this in a cell, so the package lands in the environment the kernel uses (not the system Python):

```python
%pip install "fathom-guide @ git+https://github.com/eraevous/Fathom.git"
```

Fathom accepts `pandas>=2.0,<3` and `PyYAML>=6.0,<7`, so it installs beside the versions a managed image already has. Python 3.11 or newer. Restart the kernel if pip asks you to.

## Profile a DataFrame

```python
import pandas as pd
import fathom

df = pd.read_csv("data.csv", dtype=str, keep_default_na=False)   # read as text: see the note below
result = fathom.profile(df, config="review.yaml", out="fathom-out", name="data.csv")
result            # shows Key findings and the dataset summary in the cell
```

- `config` can be a YAML path, a dict with the same keys, or left out.
- `out` is a folder; Fathom writes `report.html`, `report.md` and `guide-profile.json` there, exactly as `guide profile` does. Without `out`, nothing is written and `result.files` holds the texts.
- `name` is recorded as the source origin. The source hash is the SHA-256 of the table's content.
- `result.document` is the machine-readable profile; `result.show()` gives the inline view again.

Liftoff (no config):

```python
from fathom.api import liftoff
liftoff(df, out="fathom-out", name="data.csv")
```

## Text in, text profiled

Fathom profiles what the table says as text. A DataFrame read with `dtype=str, keep_default_na=False` keeps every cell's text, so the findings match `guide profile` on the file. The recorded source hash can still differ: Fathom hashes the CSV it writes from the DataFrame (comma-separated, `\n` line ends, quotes only where needed, no byte-order mark), so a file with CRLF line ends, extra quoting or a BOM gets a different `source.sha256`. Artifacts are byte-identical to the CLI's when the file has exactly those bytes, apart from the recorded connector and origin. Typed columns still work: each value is written with `str()` (`1.0`, `2026-01-01 00:00:00`) and missing values (None, NaN, NaT) become empty fields, so the profile describes that text. The index is dropped; call `df.reset_index()` first to keep it. Column names must be unique, nonblank strings.

## Saving to the notebook's storage

`out` is an ordinary local path, so use a folder the notebook service keeps (for example the workspace or home folder it shows in its file browser). Open `report.html` from there for the full report; the cell shows only the collapsed view, because notebook outputs often block scripts.

## Profile a SQL query (opt-in)

Fathom can profile the rows of a query on a connection **you** open. It never opens one itself, never asks for credentials, and imports no database driver.

```python
import sqlite3          # or any DB-API 2.0 driver your notebook already has
import fathom

conn = sqlite3.connect("local.db")
result = fathom.profile_query(conn, "SELECT * FROM orders", limit=50_000, out="fathom-out")
conn.close()
result
```

- `limit` is required: the most rows you expect. More than that is an error, not a silent cut; raise it or narrow the query. Fathom doesn't add a `LIMIT` to your SQL.
- Provenance records the query text, the driver's name (for example `sqlite3`) and the limit, never the connection or its credentials.
- Values are profiled as their text, as for a DataFrame. Binary columns are refused; select them as text.

From a terminal, name a function in your own code that returns an open connection:

```bash
guide profile --source sql --connect my_connect.py:make_conn --query "SELECT * FROM orders" --limit 50000 --out fathom-out
```

Fathom calls `make_conn()`, profiles the query and closes the connection. Keep credentials in that function or its environment; if it fails, Fathom prints only the error type, not its message. Whether a given database may be used is your organisation's call, not Fathom's.

Tests use SQLite files only: `python -m pytest tests/test_sql_source.py`.
