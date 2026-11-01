# Tasks: Data review to decisions

Input: spec.md, plan.md, research.md, data-model.md, contracts/cli.md, quickstart.md.
Tests are required by FR-008 and the charter. Records precede source files.

## Phase 1: Setup

- [ ] T001 Define dependencies, src layout, guide entry point and pytest setup in pyproject.toml (FR-007–009).

## Phase 2: Foundation

- [ ] T002 Implement version-1 result/schema validation and canonical JSON in src/fathom/models.py; mode unknown/wide/long, unknown resolves wide, long rejected; referenced columns exist and role lists are unique (FR-001,005,008).
- [ ] T003 Implement strict safe YAML and metadata validation in src/fathom/config.py; types numeric/categorical/boolean/temporal/string; budgets integer 0–20 excluding bool; ISO dates or null, ordered transformation type/description; unknown keys rejected (FR-001,003,004).
- [ ] T004 Implement strict CSV connector in src/fathom/connectors.py preserving column order and lexical strings/None; duplicate/blank headers and ragged records rejected; source SHA-256 (FR-001,009).

## Phase 3: US1 (P1) — evidenced review decisions

Goal: standalone dictionary, review actions, unknowns and human working record.
Independent test: dirty fixture triggers evidenced reviews and clean decoy does not.

- [ ] T005 [US1] Author synthetic fixtures in tests/fixtures/ and decision/type/metric tests in tests/test_understanding.py before profiler implementation (FR-002,003,008).
- [ ] T006 [US1] Implement conservative inference, effective overrides, all five type summaries, missing/duplicate/invalid observations and linked actions, unknown questions and human provenance in src/fathom/profiler.py (FR-002,003).
- [ ] T007 [US1] Add saved-artifact, text escaping and deterministic report tests in tests/test_outputs.py, then implement artifact-only Markdown/HTML with inline bars in src/fathom/renderers.py (FR-005,008).

## Phase 4: US2 (P2) — question-selected relationships

Goal: bounded meaningful pairs with explicit selection/exclusions and uncertainty.
Independent test: known relationship/group means; no-target, incompatible, constant,
budget and missing optional dependency decoys.

- [ ] T008 [US2] Write exact-coefficient/group summary and selection/degradation tests in tests/test_pairs.py (FR-004,008).
- [ ] T009 [US2] Implement numeric/categorical/boolean pair routes, budget/exclusions and optional SciPy p-values in src/fathom/profiler.py; no causal claims (FR-004).

## Phase 5: US3 (P3) — re-profile and compare

Goal: context-first measured deltas, unknown lineage.
Independent test: documented synthetic revision and identical-profile decoy.

- [ ] T010 [US3] Add context-order/exact-delta/unchanged-decoy tests in tests/test_outputs.py, then implement result-only comparison in src/fathom/profiler.py and views in src/fathom/renderers.py (FR-006).

## Phase 6: Integration and review

- [ ] T011 Write CLI success/failure/reproducibility tests in tests/test_cli.py; implement profile/render/compare/validate/version in src/fathom/cli.py and src/fathom/__main__.py; fail before writing on invalid inputs (FR-007,008,009).
- [ ] T012 Document quickstart/scope in README.md, add test CI in .github/workflows/tests.yml, run all tests and quickstart; record results/limits in specs/001-data-review/validation.md (FR-001–009, SC-001–005).
- [ ] T013 Regenerate .aec/edges.jsonl, append FT-R1 implementation version plus bounded claim/evaluation/evidence in .aec/records.jsonl, run AEC check and impact; review append-only invariants, then push branch and open one PR with CLA unticked.

## Dependencies & Execution Order

T001 → T002 → T003 → T004 → US1 (T005–007) → US2 (T008–009)
→ US3 (T010) → T011 → T012 → T013. Tests precede their implementation.
Stories can be verified independently through their saved/constructed inputs,
but the shared profiler is edited sequentially. No task is parallel-marked because
this run uses a single agent and shared files.

## Parallel Opportunities

With independent authors, fixture assertions and renderer expectations could be
drafted together after foundation; pair fixture design and comparison fixture
design can be reviewed independently. No delegation is needed for this run.

## Implementation Strategy

Validate US1 first for decision value, then bounded relationships and comparison.
One feature spec, one implementation PR. Stop when that PR is opened. No acceptance
of provisional requirements is inferred from completing these checkboxes.
