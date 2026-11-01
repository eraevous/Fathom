# Validation: first data-to-decisions slice

Date: 2026-11-01. Author: codex:aec. Handoff: HO-20261101-004.

## Specification consistency

One feature spec, nine functional requirements, five success criteria, three user
stories and thirteen dependency-ordered tasks. All requirements/criteria have task
coverage; zero critical findings in the pre-implementation analysis. The built-in
spec-quality checklist has 16/16 passing items. Clarifications are agent readings
under the handoff, not owner answers. No requirement acceptance is asserted.

## Executed checks

- Clean Python 3.12.14 virtual environment, installed `.[test]`: **67 passed,
  1 skipped** (the SciPy-present decoy alone is skipped). No SciPy was installed.
- Same clean environment after installing `.[stats]`: **68 passed**. pandas 2.2.3,
  PyYAML 6.0.3, NumPy 2.5.4, SciPy 1.18.1, pytest 9.2.0. `pip check`: no broken
  requirements. Also 68 passed using the preconfigured numerical environment.
- Installed `guide` entry point and ran quickstart profile, re-profile, render,
  compare and validate commands successfully. Saved-artifact HTML and Markdown
  bytes match the initially rendered views exactly.
- Fresh-process tests with distinct hash seeds compare all three profile outputs
  byte for byte. Tests also cover unsafe YAML, duplicate config keys, malformed
  schemas/artifacts, non-finite values, header-only tables and inert hostile text.
- Numeric summaries, population standard deviation, temporal coverage, boolean
  counts, frequencies, associations and grouped means use hand-calculated fixtures.
- Optional-dependency tests force SciPy unavailable and verify the same core
  coefficient/count plus explicit unavailable p-value status. The clean environment
  also exercises actual absence, not just a mock.

## Concrete decision evidence

The four-row synthetic `review.csv` yields one missing amount and one repeated
full row beyond its first occurrence. It produces exactly two conditional review
actions, each linked to the corresponding observation, source hash and rule.
`clean.csv` yields neither action. The working record retains the human decision
to investigate repeated rows before deletion, with its rationale. Unprovided row
unit, generating process, missingness mechanism and meanings remain questions.

The two-row `revised.csv` comparison yields row delta -2, missing-cell delta -1
and repeated-row delta -1. Both declared contexts and transformations precede
these deltas. Semantics changes are flagged; no lineage or causal claim is made.

## AEC and preservation

The purpose-link hook resolves every versioned reference. The before-tasks
structural check had zero errors/warnings. After implementation, regenerate edges
and run the records check and old/new impact commands. Final check: **0 errors,
0 warnings**, including the feature spec anchor and all code references. Snapshot:
447 edges from 13 Python files. The empty-main → implemented snapshot impact report
flags `FT-R1@2` stale and `FT-E1@1` / `FT-C1@1` needs_review: the current records
name code absent from the old snapshot. Eleven other conclusions are unaffected;
no accepted record is changed or invalidated. Follow-up: review those candidate
satisfaction/evidence claims against the tested post-build snapshot; owner
acceptance of FT-R1 remains pending. These are review dispositions, not failed
tests or a claim the obligation disappeared. All pre-existing record bytes and protected guiding documents
are checked against original `main`; only new record lines are appended.

The planning/requirement commit precedes the implementation commit. `FT-R1` stays
provisional; implementation links and candidate conformance evidence do not accept
it. No purpose-outcome claim is made. No earlier implementation was accessed.

## Limits and drift review

The twelve scope readings are in the intent note. In particular, the April MVP
connector/CLI breadth is deferred in favor of DG-D1's decision outcome. The
canonical data flow is retained; no new subsystem or changed responsibility was
needed. The implementation has no credential, network, transformation or narrative
engine. Embedded SVG supplies visual evidence without external assets.

These synthetic tests show conformance to the proposed slice. They do not establish
usefulness across most projects, quality of a domain owner's supplied metadata,
causal validity, production scale or Zach's acceptance. Human usability review and
an outcome observation remain future evidence.
