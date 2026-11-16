# 029: Notebook API, inline display and relaxed dependency ranges

Handoff HO-DG-20261106-NZ0P, PR 1 of 2 (the opt-in SQL source is PR 2). Owner request, Zach 2026-11-06: "It would be good to have this runnable on [a hosted notebook service] …" (product name redacted per Zach 2026-11-15).

Proposed for Zach. Serves: P0@2, DG-RE@1, DG-RF@1.

## US1: Profile a DataFrame from Python (P1)

- `fathom.profile(df, config=None, out=None, *, name="dataframe")` and `fathom.api.liftoff(df, out=None, *, name="dataframe")`.
- `config` is None, a dict, or a YAML path. A dict is dumped to YAML and read with the file loader, so a dict and the same file give the same config.
- The DataFrame is serialised to CSV bytes in memory (header, rows, index dropped, `\n` line ends; missing values as empty fields; other values with `str()`), then parsed by the same function the CLI uses for a file. After that the code path is the CLI's.
- **Byte-identical:** for the same CSV bytes and config, `report.md`, `report.html`, `guide-profile.json`, `liftoff.html` and `liftoff-profile.json` equal the CLI's except the recorded `source.connector` (`dataframe`) and `source.origin` (`name`).
- **Provenance:** `source.sha256` is the SHA-256 of the serialised bytes (content hash; the name doesn't change it). It equals the CLI's hash only when the file has exactly those bytes: a file with CRLF line ends, extra quoting or a BOM keeps its cell text through `dtype=str` but gets a different hash (Copilot review, 2026-11-16).
- Column names must be unique, nonblank strings; a clear `ValueError` otherwise.
- `import fathom` stays light: it imports neither pandas nor the API until `fathom.profile` is used.

Deviation from the handoff, recorded: the handoff names `fathom.liftoff(df)`. `fathom.liftoff` is already the Liftoff module; the import system rebinds that name on the package whenever the module loads, so a function there would be replaced. The function is `fathom.api.liftoff`.

## US2: Inline display (P1)

- `result.show()` and `result._repr_html_()` give a collapsed view: Key findings plus the dataset summary table (profile), or the Brief (Liftoff), and the path of the full report when `out` was given.
- No scripts, no external URLs, no `@import`, inline CSS only, and in-page evidence links removed, so it works in sandboxed notebook outputs. Narrower reading, recorded: the cell always shows the collapsed view; the full report is the written HTML file.

## US3: Install beside a managed notebook image (P1)

- `pandas>=2.0,<3` and `PyYAML>=6.0,<7` replace the exact pins; `requires-python >=3.11`.
- CI: the main job installs `requirements/ci-lock.txt` (the former pins plus resolved dependencies); a compat job tests lowest (Python 3.11, pandas 2.0.3, PyYAML 6.0, numpy 1.26.4) and latest (Python 3.13, newest pandas 2.x).
- Python 3.10 isn't supported: not tried in this PR (the cost wasn't measured); a candidate follow-up. Supporting 3.11 needed one change (a nested same-quote f-string in `timeseries.py`).
- pandas 3 is outside the range until tested.

## US4: Doc page (P2)

`docs/notebooks.md`: `%pip install` into the notebook's own kernel, profile a DataFrame, show inline, save outputs to the notebook's storage. No admin rights.

## Tests

`tests/test_notebook_api.py`: byte identity against the CLI (with and without config; Liftoff), dict config equals file, content hash, typed and missing values, bad inputs, the inline view (collapsed, no scripts or URLs), the light import, and the API under the all-sockets-blocked harness.

## Unchanged

CLI behaviour and artifacts, the CSV parsing rules, determinism and offline behaviour.
