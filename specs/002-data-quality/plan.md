# Implementation Plan: Data quality

**Branch**: `002-data-quality` | **Date**: 2026-11-01 | **Spec**: [spec.md](spec.md)

## Summary

Extend the existing profiler with deterministic quality checks, share the pair
budget between relevant existing value routes and conditional-missingness evidence,
and replace primary JSON dumps with a readable report. Keep full evidence in the
artifact and provide a native HTML switch between grouped and full finding views.

## Technical Context

**Language/Version**: existing Python 3.12+.
**Dependencies**: no new application dependencies. pandas 2.2.3 retains the frame;
PyYAML 6.0.3 retains safe configuration; optional scipy >=1.14,<2 retains existing
p-value enrichment. Existing pytest 9.2.0 and setuptools >=68 remain test/build tools.
AEC stays at the AGENTS pin. All were justified in spec 001's plan; no optional
library is required for any new diagnostic. Playwright, if available, is only a
local verification tool for the native view switch, not a project dependency.
**Storage**: existing saved JSON/Markdown/self-contained HTML; no state store.
**Testing**: synthetic violation/decoy pairs, hand-calculated summary/ranking,
report-visible findings, fresh-process bytes, legacy artifact rendering and
acceptance ledgers. Run existing and new tests with/without SciPy.
**Platform/type**: existing local library/CLI. No hosted app.
**Performance/scope**: local in-memory use; at most 2000 near-duplicate vector
comparisons, 20 grouping columns, 20 reported detailed temporal intervals; share
pair_budget (0..20) across reported quality/value relationships. Report coverage
and truncation, never imply an exhaustive clean bill.

## Constitution Check

Pre-research and post-design gates PASS: one flow retained; typed attributed
findings/evidence; no inferred domain facts; shared bounded ranking; context-first
comparison unchanged; artifact-only views; exact/decoy/degradation/reproducibility
checks; authored synthetic fixtures only. No charter amendment or exception.

## Project Structure

- `src/fathom/quality.py`: plain-data helper for quality diagnostics/summary and
  bounded conditional-missingness candidates, called only from the profiler.
- `src/fathom/profiler.py`: integrate quality findings; relevance screening/ranking
  of existing routes plus missingness candidates; no new target-analysis methods.
- `src/fathom/renderers.py`: human HTML/Markdown, typed groups/evidence, compact
  dictionary, native CSS switch; retain comparison and legacy version-1 rendering.
- `src/fathom/models.py`: validate additive dataset_summary/quality fields when
  present, without rejecting legacy version-1 documents.
- `tests/test_quality.py`, `tests/test_readability.py`, `tests/test_pairs.py`:
  diagnostic, ranking, report, compatibility and toggle verification.
- `tests/fixtures/quality/`: synthetic workshop, clean and later holdout tables,
  plus explicit planted lists; `specs/002-data-quality/validation.md` is the ledger.

## Research decisions and detailed rules

Use the thirteen readings in the intent note as the algorithm contract: conservative
sentinel/token/dominance thresholds, fingerprint redundancy, exact missing masks,
segment-rate gaps, inferred day cadence and limited moment-based skew. Every rule
carries sample size, threshold and evidence. Structural groups use fingerprints
rather than outputting an all-pairs matrix. Missingness relationships are selected
under the same budget as existing value pairs; rejected candidates retain reasons.

Ranking uses focus, strength, complete-case count, then lexical names/method. A
near-duplicate equivalence uses a lexical representative so column order cannot
change the winner. The focus parser matches literal column names in the question;
no semantic understanding is claimed. Rank with core metrics; optional SciPy runs
only on selected numeric pairs, so excluded candidates don't require it.

## Implementation sequence and acceptance

Tests precede each implementation group. Build summary/findings, ranking and then
report views; run builder acceptance report review after each group. Freeze rule
choices before making an additional holdout. Document found/missed/false alarms,
including limitations not fixable without domain knowledge. Passing builder checks
is not independent acceptance under FT-R4. Stop at one PR with the CLA unchecked.

## Drift review

Quality is a helper inside the profiler, not a new subsystem. Selection changes
from input-order to measured relevance under FT-R3. Renderers change responsibility
only in presentation, still reading results exclusively. The modular relations
section leaves room for later target methods and axis controls without adding them.
