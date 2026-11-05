# Tasks: offline panel signals
## Setup
- [x] T001 Record scope, requirements and contracts in specs/014-offline-panel/ and .aec/records.jsonl.
## US1 — Offline
- [x] T002 [US1] Write failing socket/import/resource tests in tests/test_offline.py.
- [x] T003 [US1] Document wheelhouse install in README.md; enforce runtime locality in src/fathom/cli.py.
## US2 — Panel
- [x] T004 [US2] Write analytic and synthetic violation/decoy tests in tests/test_panel.py and tests/fixtures/panel/.
- [x] T005 [US2] Implement eligibility/calendar/windows and estimators in src/fathom/panel.py and panel_stats.py.
- [x] T006 [US2] Add artifact validation and renderer/CLI dispatch in models.py, renderers.py, cli.py, panel_view.py.
## US3 — Views and metrics
- [x] T007 [US3] Test and implement view lineage/leakage in tests/test_panel.py and src/fathom/panel.py.
- [x] T008 [US3] Test and implement keyed metrics, disagreement and profile reuse in tests/test_panel.py and src/fathom/panel.py.
## Review
- [x] T009 Run full/core/offline/fresh-process checks and visual review in specs/014-offline-panel/review/.
- [x] T010 Append claim/evidence, regenerate edges, run check/impact, and prepare one PR for Kate to review.
Dependencies: T001→T002→T003; T004→T005→T006→T007→T008→T009→T010.
Independent tests: each US has its own family. T002 and T004 fixtures can be prepared
independently; implementation stays sequential to preserve test-first evidence.
