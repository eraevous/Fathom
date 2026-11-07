# Tasks — 025
## Setup
- [x] T001 Specify scope/intent/provisional requirement in specs/025-time-definition/spec.md and .aec/records.jsonl.
- [x] T002 Research parser/YAML/series seams and record plan in specs/025-time-definition/plan.md.
## US1 — ambiguity and declarations
- [x] T003 [US1] Write violating/clean parser/profile/config tests in tests/test_time_definition.py and tests/fixtures/time_definition/.
- [x] T004 [US1] Extend portable grammar/rate/faults in src/fathom/temporal_formats.py and src/fathom/temporal_picker.py.
- [x] T005 [US1] Thread rate, disclose ambiguity/faults, validate metadata in src/fathom/config.py, profiler.py, univariate.py, temporal_profiles.py and models.py; decline frame chronology in timeseries.py.
## US2 — field card
- [x] T006 [US2] Add field evidence/model and card to src/fathom/temporal_picker.py (or small shared module).
- [x] T007 [US2] Wire explicit card use and rate controls to both YAML paths in src/fathom/configure.py; preserve dropdown/static fallback.
- [x] T008 [US2] Test exact browser/Python grammar/card parity and config round-trip in tests/test_time_definition.py.
## Validation/publication
- [x] T009 Full extras/offline/identity, docs and scripts-on/off1280/390light/dark screenshots in specs/025-time-definition/review/.
- [x] T010 Append claim/evidence, regenerate .aec/edges.jsonl and check/impact; prepare stacked PR with CLA unticked and handoff output.
