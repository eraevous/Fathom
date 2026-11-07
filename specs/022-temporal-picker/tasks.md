# Tasks: temporal picker
## Foundation
- [x] T001 Specify/clarify grammar and clock-basis intent; append provisional requirement.
- [x] T002 Research parser consumers/UI seam and plan/data-model/contracts.
- [x] T003 Violating/clean fixtures and tests in tests/test_temporal_formats.py, test_temporal_picker.py.
## US1
- [x] T004 Shared Python temporal_formats parser/validation and profiler routing.
- [x] T005 Add per-basis intraday/date profiles, labelled charts and findings; legacy validation/render/export.
- [x] T006 Refuse incompatible clock chronology explicitly; no date invention.
## US2
- [x] T007 Shared portable JS parser and stored-sample picker descriptors.
- [x] T008 Canonical selected format/YAML, live preview/error/ambiguity and no-script fallback.
## Validation
- [x] T009 Full extras/offline/determinism; actual1280/390light/dark picker screenshots.
- [x] T010 Claims/evidence/edges/check/impact, short PR with CLA unticked, Kate first.
Dependencies:foundation→US1→US2→validation. Research ran concurrently; implementation stays one feature at a time. Deliver smallest complete two-story slice.
