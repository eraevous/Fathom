# Fathom design (distilled from the April 2026 design)

**Status:** the April 2026 Data Guide design spec was marked **Approved** (2026-04-20). This is a distillation of it, written on 2026-11-01 by claude:aec. The original file was left in the archived repository by Zach's choice ("Distil, don't copy"). Its examples and its section about retiring that repository's old code are omitted.

**Later accepted decisions win over this file.** Read `.aec/records.jsonl` first. The ones that change the April design:
- **`DG-A2`:** no code is fixed; only the guiding documents are.
- **`DG-A3`:** room for a labelled AI narrative, possibly through relay-kit.
- **`DG-A1`:** the output also works standalone as data documentation.
- **`DG-RD`:** comparisons state each profile's context first.

Anything below may be changed by a specification. The **Architecture** and **Canonical data model** sections are what the charter's rule 1 points at.

## Architecture

One data flow, four layers:

```
Data source → Connector → GuideDataFrame → Profiler → ProfilingResult → Renderer → Output
```

**Key principle:** every connector produces a `GuideDataFrame`, every renderer consumes a `ProfilingResult`, and the profiler is the only component that touches both.

The April layout put connectors, core models, profilers and outputs in separate packages, with a thin CLI and a programmatic API that composes the layers. The layout itself is open.

## Canonical data model

- **Two table shapes.**
  - **Wide:** arbitrary columns, profiled column by column, with no forced pivoting.
  - **Long:** one row per measurement, with the columns `key` (identifiers), `context` (grouping and segmentation), `metric` (measure name), `value`, and an optional `data_type` hint. When the hint is blank, the profiler infers the type.

  A mode of `unknown` means the shape is detected at load.
- **`SchemaContract`:** names the key and context columns, the metric, value and type columns, and the mode.
- **`GuideDataFrame`:** a thin wrapper around a DataFrame, carrying its `SchemaContract` and its source metadata (connector type, origin path or query).
- **`ProfilingResult`:** the profiler's output: univariate and bivariate results, a data-quality summary, and an `annotations` slot for narratives. Each narrative is keyed by the element it describes and records which framework produced it. Renderers show annotations where present and skip them when absent, so a narrative engine can be added without changing renderers.

## Connectors

Every connector implements `connect()` and `load() -> GuideDataFrame`.

The April MVP list: CSV (path or glob), Excel (sheet selectable), JSON, SQLite, any SQLAlchemy database, and Snowflake.

**Credential safety, as approved:**
- **Resolution order:** an explicit credentials-file flag, then an environment variable naming a credentials file, then per-connector environment variables, then fail loudly at startup.
- **The credentials file** has a strict schema whose `type` matches the connector. Missing fields fail at startup, not at query time.
- **No credentials in config or code, ever.** Configuration files are safe to commit, and credential file patterns are git-ignored.

## Outputs

- **MVP:** one self-contained HTML report with embedded charts and no external assets. It covers a dataset overview, data quality, per-column profiles, and requested bivariate analysis.
- **Phase 2:** a live dashboard.
- **Phase 3:** a dashboard constructor (design deferred).
- **Later:** PDF export.

The accepted records add a machine-readable profile artifact as the stable interface, with Markdown and HTML derived from it (`DG-RE`).

## CLI

A thin command-line interface named `guide`:
- a guided interactive run;
- a fully non-interactive run from a YAML configuration;
- a quick single-file profile;
- schema-contract validation;
- the version.

Command names are open.

## Phasing (April)

| Phase | Scope |
|---|---|
| 1 (MVP) | connectors, the data model, the static report, the CLI |
| 2 | the dashboard |
| 3 | the dashboard constructor |
| Later | narrative integration, PDF export, a headless mode, optional clustering profilers |

The accepted MVP framing is **data to decisions** (`DG-D1`). A specification should check this phasing against it.
