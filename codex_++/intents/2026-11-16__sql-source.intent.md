# Intent: opt-in SQL source (spec 030, HO-DG-20261106-NZ0P PR 2)

- **Rows become CSV text, then the one parse.** Same reason as spec 029: `load_csv_bytes` stays the single parse, so the SQL source can't drift from the file and DataFrame paths (AGENTS Drift). The measurements equal `fathom.profile` on the same rows by construction.
- **Extra `source` keys, not a new artifact section.** `adapter`, `query` and `row_limit` sit beside `connector`/`origin`/`sha256`. The artifact check requires only those three; the reports' provenance block already renders extra keys. No schema version bump; for Zach if he wants one.
- **The cap is enforced client-side with `fetchmany(limit + 1)`.** Wrapping the query in `LIMIT` would be dialect-specific and is push-down, which the handoff excludes. The database may still do the full query's work; the cap bounds what Fathom holds.
- **A failing factory's message is withheld.** Driver login errors can echo hosts, users or passwords. Query errors keep their message (they concern the SQL). Narrower reading of "never logs credentials".
- **`--connect path.py:func` is executed as the user's code.** That is what "a user-supplied connection factory module" means; it's no different from the user running it. Fathom doesn't read the module's source or variables.
- **No DuckDB extra.** It would be a new third-party dependency for no new code path (its DB-API connection works through the generic one). Left for a separate decision.
- **Binary values are refused**, not hex-encoded: an encoding choice would be a semantic conversion.
- **A read-only guard, not a SQL parser (Copilot review).** Non-SELECT statements used to run before `cursor.description` rejected them. A dialect-agnostic check of the first keyword and of a second statement runs first. It can't see writes inside `WITH` on some databases, or side-effecting functions, so the docs ask for a read-only connection. Parsing SQL properly would need a dependency or a dialect, both out of scope.
