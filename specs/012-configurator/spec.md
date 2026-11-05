# Feature Specification: Configurator page (`guide configure`)

**Feature Branch**: 012-configurator (stacked on 010-row-level-checks, PR #20)
**Created**: 2026-11-04 (CT) | **Status**: builder readings provisional, for Zach to accept.
**Input**: DEC-067, from an owner-requested debate. Owner's words, as relayed by the lead
session (not yet in `docs/decisions/`): "Fathom should also begin to take configuration,
with the current decisions as Defaults. That should take the form of an HTML config page
that can allow users to select/deselect, pick target, adjust bin sizes, etc, based on
higher-level Fathom analyses on the dataset as a whole. We can also include granularity
and other knobs there."
Serves: P0@2, DG-RA@1, DG-RB@1, DG-RC@1, DG-RE@1, DG-RF@1. Proposed: FT-CFG-R1@1.

## User scenarios

### US1 — Build a config from the table's own profile (P1)
`guide configure DATA.csv [--config existing.yaml] --out DIR` runs the existing profile
(no new analysis) and writes `DIR/configure.html` and `DIR/configure-profile.json`.
The page shows the dataset summary; a column table (inferred type, populated share,
distinct count, parsed date formats) with type override, `date_format` and
`exclude_from_target` controls; a target selector whose candidates carry observable
reasons only; temporal column pairs as unticked interval suggestions; histogram `bins`;
`pair_budget`; `sample_rows`; optional report sections; question and row unit.

### US2 — Three visible states (P1)
Every control shows its state: system default, suggested (from the profile, with its
reason, applied only when the user ticks it), selected, or existing config (`--config`).
The untouched page emits `{}`.

### US3 — YAML out, provenance aside (P1)
YAML is generated live (Copy, Download via data: URL) with existing config keys plus
`bins` and `sections`. No provenance in the YAML; a separate `config-manifest.json`
records the state of each control and is advisory (Fathom does not read it).

### US4 — Nothing evidentiary is a knob (P1)
Contrast thresholds and row-structure rules are shown read-only with their record ids.
No control suppresses a warning or finding. An omitted section is named in the
report's "What the data cannot tell" as "omitted by configuration".

## Requirements
- FR-001: Page is self-contained (inline CSS/JS, no external resources, no dates) and
  byte-identical across runs. Reports stay script-free.
- FR-002: One JSON control schema is embedded; the YAML generator exists in JS and
  Python with the same rules; a test runs the embedded JS under node (if installed) and
  compares it with Python.
- FR-003: Every column name and value is escaped in HTML text, attributes and the JSON
  script block (`<`, `>`, `&` as \u escapes); names never reach `innerHTML`.
- FR-004: Config gains `bins` (1–50; default rule sqrt(n) capped at 10, disclosed) and
  `sections` (`samples`, `missingness_patterns`, default true). Omission affects HTML,
  Markdown, PDF and PPTX views only; `guide-profile.json` keeps the data.

## Builder readings (narrower, recorded)
1. "Exclude" a column is read as `exclude_from_target` only. Dropping a column from
   profiling would suppress its findings (US4), so it is not offered.
2. Granularity / time series: no `time_series` key on this branch; the page lists it as
   an extension point and offers no control. *Updated 2026-11-05 after merging main
   (#21 added `time_series`):* the page now offers series unticked, chosen by the
   report's own undeclared-series rule (temporal column with >= 30 distinct periods;
   event counts, or the sum of a numeric column that is not identifier-like), each with
   an optional `by` column and granularity checkboxes. `max_lag` and `top_n` are not
   offered (defaults apply; values from `--config` are kept). See
   `codex_++/intents/2026-11-05__reconcile-22.intent.md`.
3. Omitting `samples` departs from FT-R9 only by explicit configuration and is disclosed.
