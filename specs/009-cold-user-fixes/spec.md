# Feature Specification: Cold-user fixes

**Feature Branch**: 009-cold-user-fixes | **Created**: 2026-11-04 (CT)
**Status**: Builder readings provisional, for Zach to accept.
**Input**: a cold user installed from the README only and profiled the public
seaborn `taxis` table (6,433x14). Findings 1–6 of that run.
Serves: P0@2, FT-R14@1, FT-UNI-R1@2, FT-R13@1, FT-R11@1, DG-RB@1, DG-RF@1.

## User scenarios

### US1 — Date-time columns get the date profile (P1)

`2019-03-23 20:21:09` was read as string and excluded from target ranking as
"identifier-like"; the documented `date_format` override and `type: date` were both
rejected as "unsupported" with no hint of what is supported.

Acceptance: strict ISO date-times (`YYYY-MM-DD[ T]HH:MM[:SS]`) are inferred temporal
and receive the existing FT-R14 date profile (span, calendar counts, gaps, invalid
dates); the time of day is disclosed as not analysed. `date_format: ISO_DATETIME`
works and counts invalid calendar dates. Rejected `type`/`date_format` values name
the accepted values. Decoys: plain ISO keeps `ISO`; out-of-range times, offsets,
one-digit hours and free text containing a time are not dates.

### US2 — The CLI says what it did (P1)

Acceptance: `export` without an extra still exits 0 (spec004 contract, FT-R13) and
prints one stderr line per missing format naming the extra and its install command;
a written format prints none. `profile` prints the paths written and one line with
question, target, target exclusions and row unit. `validate` keeps the resolved
schema keys and adds `resolved` (rows, columns, question, target, group_by,
pair_budget, row_unit, exclude_from_target, column overrides). No timestamps.

### US3 — The header does not contradict the working record (P2)

Acceptance: with `row_unit` declared, the inferred description no longer says the
row unit is unknown; without it, it still does.

### US4 — Install is self-contained (P2)

README Install starts with clone + `pip install -e '.[test]'` and says the CLI is
`guide` from package `fathom-guide`, with the accepted override names.

## Requirements

- FR-001: Recognize strict ISO date-time as temporal (`ISO_DATETIME`), date part only.
- FR-002: Override errors list accepted values; `ISO_DATETIME` accepted as `date_format`.
- FR-003: Temporal columns are not excluded from target analysis as identifier-like.
- FR-004: Export notice on stderr; exit code unchanged.
- FR-005: Deterministic profile/validate echo.
- FR-006: Description consistent with declared row unit.
- FR-007: README Install paragraph only (open PR #16 also edits README).
- FR-008: Diagnose, do not change, the group-contrast threshold and zero-share
  findings; record proposals for Zach.

## Out of scope

All-blank rows, repeated keys, within-key constants, human-readable compare (queued
separately); strftime patterns, time-of-day profiles and time zones; any change to
contrast thresholds or zero rules (proposed only).
