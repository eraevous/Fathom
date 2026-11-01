# Tasks: 002-data-quality

Input: spec, plan, research, model, report contract and quickstart. Existing
accepted records and provisional FT-DQ-R1 precede implementation.

## Phase 1: Setup

- [ ] T001 Capture the merged-main baseline and create builder workshop/clean planted fixtures in tests/fixtures/quality/ with explicit planted.json (FR-007).

## Phase 2: Foundation

- [ ] T002 Add exact diagnostic/summary tests in tests/test_quality.py before source changes; include each violating rule, clean decoy and docs/acceptance.md report assertions (FR-001,002,004).

## Phase 3: US1 — consequential quality findings (P1)

- [ ] T003 [US1] Implement transparent thresholds, fingerprint groups, missingness candidates and linked summary in src/fathom/quality.py; integrate in src/fathom/profiler.py (FR-001,002,004).
- [ ] T004 [US1] Validate additive dataset_summary and quality shapes/links in src/fathom/models.py; preserve version-1 artifacts without new fields; zero-denominator shares are null (FR-006).

Independent test: exact planted evidence and no matching diagnoses on clean decoys.

## Phase 4: US2 — relevant pairs (P2)

- [ ] T005 [US2] Write stronger-later, reordered-column, redundant/near-constant, zero-budget and shared-budget tests in tests/test_quality.py and tests/test_pairs.py (FR-003).
- [ ] T006 [US2] Rank existing value routes plus conditional-missingness candidates in src/fathom/profiler.py by focus/strength/count/lexical ties; preserve optional-dependency degradation and all exclusions (FR-003,006,008).

Independent test: later stronger candidate wins one slot; total pairs <=budget.

## Phase 5: US3 — readable report (P1)

- [ ] T007 [US3] Write section-order/summary-link/evidence/disclosure/legacy/hostile-text tests in tests/test_readability.py before rendering changes (FR-004,005,006).
- [ ] T008 [US3] Replace primary JSON report blocks with prose/tables in src/fathom/renderers.py, derive summarized/full views from the artifact, add native checkbox switch and evidence details; keep comparison context first (FR-005,006,008).

Independent test: report-only inspection and one-click offline switch; all full IDs retained.

## Phase 6: Acceptance and publication

- [ ] T009 Freeze diagnostics before authoring tests/fixtures/quality/holdout.csv; run report-only builder checks for all tables and list found/missed/false alarms in specs/002-data-quality/validation.md (FR-007, SC-001–005).
- [ ] T010 Update README.md and report contract, run core/stats regression and CLI roundtrip/bytes checks, verify the native switch in a browser if available (FR-006).
- [ ] T011 Regenerate .aec/edges.jsonl, append bounded claim/evaluation/evidence and implementation links to .aec/records.jsonl, run AEC check/impact, verify protected originals, publish branch and open one PR with CLA unchecked.

## Dependencies and execution

T001 → T002 → T003–004 → T005–006 → T007–008 → T009–011.
Tests precede implementation for each story. Work is sequential in this run;
independent test-fixture design and report expectation review could proceed in
parallel with separate authors, but shared profiler/renderer edits cannot.

## Implementation strategy

Quality evidence first, shared-budget ranking second, readable artifact views
third. Check each group against acceptance, then a later builder holdout without
tuning away its misses. No FT-R7/FT-R8 methods or axis controls. Stop at PR open.
