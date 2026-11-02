# Tasks: 005 plots and layout

## Setup / foundation

- [x] T001 Write tests/fixtures/layout and tests/test_plots_layout.py for exact plots, time-name decoys and formatted views (FR-001–005).

## US1 — readable entries

- [x] T002 [US1] Add presentation.py tables/formatting and full-width HTML/Markdown entries in renderers.py; remove time-name cues in profiler.py/univariate.py (FR-001,002,004).

## US2 — distributions

- [x] T003 [US2] Implement bounded histogram/ECDF/category/text/date/mask specs in univariate.py/profiler.py/models.py and static SVG charts.py (FR-003,005).
- [x] T004 [US2] Integrate shared tables and new vector/native chart kinds in exports.py; verify optional absence and fresh-process bytes (FR-003,005).

## US3 — visual review

- [x] T005 [US3] Capture real HTML/PDF/PPTX before/after at1280/390 in specs/005-plots-and-layout/review with reproducible script; visually inspect, compare practice and fix/list issues (FR-006).
- [x] T006 [US3] Record planted/clean/late found/missed and proposed FT-R15 changes in validation.md; update README.md (FR-006).

## Publication

- [x] T007 Append implementation claim/evaluation/evidence; regenerate .aec/edges.jsonl/check/impact; verify protected originals and publish one PR with CLA unchecked (FR-005,006).

Dependencies: T001→T002→T003→T004→T005→T006→T007. Serializer tests can run
independently; edits stay sequential. All six FRs covered; no unmapped story tasks.
