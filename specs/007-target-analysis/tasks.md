# Tasks:007 target analysis

## Setup

- [ ] T001 Record spec/plan/clarifications and provisional AEC requirement; verify purpose/check gates in specs/007-target-analysis before code (FR-001–008).

## US1 — rank target relationships

- [ ] T002 [US1] Write exact measure/clean-decoy, exclusion, budget/reservation, config and legacy tests in tests/test_target.py (FR-001,002,003,006).
- [ ] T003 [US1] Implement core target.py measures/config.py declarations and profiler.py selection integration; models.py validation and presentation tables (FR-001,002,003,006).

## US2 — review groups

- [ ] T004 [US2] Test and implement target.py group counts/shares/valid/missing/rates/rest contrasts, n<5cautions and evidenced findings in tests/test_target.py (FR-004).
- [ ] T005 [US2] Implement target_marks.py bounded scatter/group-box/rates and renderers.py/exports.py artifact-only tables/plots (FR-004,005).

## US3 — distribution polish

- [ ] T006 [US3] Test/implement original-unit log ticks, positive log ECDF, slim box/noY and static sticky statistics in univariate.py/charts.py/renderers.py/exports.py (FR-007).

## Verification / publish

- [ ] T007 Create tests/fixtures/target planted/clean/late synthetic tables and sourced public target configs; inspect report-only found/missed ledger in specs/007-target-analysis/validation.md (FR-008).
- [ ] T008 Capture and visually inspect actual HTML/PDF/PowerPoint1280/390 in specs/007-target-analysis/review; fix or list open problems with practice comparison (FR-005,007,008).
- [ ] T009 Run full/core and fresh-process bytes; append AEC claim/evaluation/evidence, edges/check/impact, protected-prefix verification; rebase after#14merges and publish one CLA-unticked PR then stop (FR-006,008).

Dependency sequence:T001→T002→T003→T004→T005→T006→T007→T008→T009.
Read-only research/tests in independent environments may run concurrently; shared
file edits remain sequential. All8FRs mapped;0critical ambiguity/constitution issue,
0unmapped task. Checklists16/16pass. US1 gives useful ranking alone; later stories
add group context/plots and polish. No checklist is implementation acceptance.
