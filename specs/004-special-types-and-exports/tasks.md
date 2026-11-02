# Tasks: 004 special types and exports

## Setup / foundation

- [ ] T001 Write special-type violation/clean tests in tests/test_special_types.py before code (FR-001–003).

## US1 — local special checks

- [ ] T002 [US1] Implement special.py and integrate profiler.py/models.py/univariate.py/renderers.py routing, retained overrides and evidenced special findings (FR-001–003).

## US2 — optional artifact exports

- [ ] T003 [US2] Write missing-dependency/content/determinism tests in tests/test_exports.py; implement optional extras in pyproject.toml, exports.py and CLI export command (FR-004,005).
- [ ] T004 [US2] Verify PDF/PPTX contents and bytes in separate processes; add exports matrix in .github/workflows/tests.yml and exercise core degradation (FR-004–006).

## Acceptance / publication

- [ ] T005 Record planted/clean/late found/missed and export limits in validation.md; update README.md; verify no network, quality score or sensitive tags (FR-006).
- [ ] T006 Append implementation claim/evaluation/evidence, regenerate .aec/edges.jsonl, check protected originals, publish main-targeted dependent PR with CLA unchecked.

Order: T001→T002→T003→T004→T005→T006. Each story has independent synthetic tests;
serializer-specific tests could run in parallel, but implementation stays sequential.
