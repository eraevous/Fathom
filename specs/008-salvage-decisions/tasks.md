# Tasks: 008 salvage decisions

## Setup

- [x] T001 Record spec/plan, intent note and provisional FT-SD-R1 before code (FR-001–009).
- [x] T002 Capture main's artifacts for the normal and offset decoys into tests/fixtures/salvage/ before any source change.

## US1 — significant-figure storage

- [x] T003 [US1] Tests: tiny.csv fails on main/passes after; normal/offset artifacts equal main's; tiny geometry kept; validator accepts 1 and 2, rejects 3 (FR-001–003).
- [x] T004 [US1] Implement `stored`/`geometry` in univariate.py; route profiler/quality/target rounding through it; schema 2 in profiler/models (FR-001–003).

## US2 — missingness-by-group test

- [x] T005 [US2] Tests: stdlib chi-square tail; planted fixture → one observation; 20 null tables → zero; V-gate and size-gate decoys → zero; no action cites the test (FR-004/005).
- [x] T006 [US2] Implement chi_square_sf, missingness_table_test and the scan in quality.py; record thresholds/results in quality.missingness_tests (FR-004/005).

## US3 — palette, kind tags, dark mode

- [x] T007 [US3] Tests: single colour source, AA contrast (with a failing colour as violating case), dark media query plus both data-theme overrides, kind tags, no script, bytes (FR-006–009).
- [x] T008 [US3] Implement palette.py; route renderers/charts/target_marks/exports colours through it; theme CSS and kind tags (FR-006–008).

## Verification / publish

- [x] T009 Screenshot affected views (findings, column entry with charts, target chart) light/dark/override at 1280/390 into specs/008-salvage-decisions/review/; inspect and fix or list.
- [x] T010 Full/core suites, fresh-process bytes, README/CHANGELOG notes, append claim/evaluation/evidence, regenerate edges, `aec check`; push branch and open one CLA-unticked PR, then stop.

Dependency order: T001→T002→T003→T004→T005→T006→T007→T008→T009→T010.
