# Feature Specification: Target analysis and distribution polish

**Feature Branch**:007-target-analysis | **Created**:2026-11-02 (CT)
**Status**: Authorized scope; implementation readings provisional.
**Input**: HO-20261103-001.
Serves: P0@2, FT-R7@2, FT-R19@1, FT-R17@1, DG-RC@1, DG-RB@1, DG-RE@1, DG-RF@1.

## User Scenarios & Testing

### US1 — Identify relationships worth reviewing (P1)

An analyst declares a target and receives a ranked column table with measure, value,
complete cases, selected status and clear exclusion reasons. Selected relationships
include an appropriately labelled plot. The analyst can distinguish observed
association from a domain explanation or causal claim.

Acceptance: known numeric/category relationships outrank independent decoys;
configured leakage and near-copy/identifier/near-constant columns are excluded;
changing input-column order does not change tied ranking. Without a target, an
explicit skipped reason preserves documentation/QA fallback. Zero budget shows
ranking but no detailed relationship/plot; unknown config references fail clearly.

### US2 — Understand groups without hiding small samples (P1)

A categorical target, or a selected grouping category with a numeric target,
provides within-group counts, shares, valid/missing counts and numeric mean/median
or category rates. Marked differences from the rest produce evidenced review
observations/actions. Small groups remain visible and labelled too small to read
reliably. A declared grouping category is preferred within the same shared budget.

Acceptance: a planted small group with a shifted amount/missingness pattern appears
with its actual size and caution; a balanced clean decoy produces no marked contrast.
No group-by-every-column or target-versus-two-predictor expansion is performed.

### US3 — Read skewed distributions and exports (P2)

Log-scale ticks show original values with known units; single-variable box plots
are slim and omit the meaningless column y-caption. Statistics stay in view while
reviewing a long plot stack. Eligible positive-only log ECDFs accompany log
histograms with explicit positive denominators and exclusions. Linear views remain.

Acceptance: skew+zero fixture and public films show original-value log ticks,
positive-only cumulative coverage, slim boxes and usable statistics/plots at desktop
and phone widths. HTML, PDF and actual PowerPoint1280/390 undergo FT-R17 review.

### Edge cases

Missing/nonfinite/constant targets, unsupported dates/text types, one group/too many
groups, sparse contingency tables, small groups, tied numeric values, huge/small
magnitudes, zeros/negatives on log views, all exclusions, budget0/1/20, optional
serializer/SciPy absence, old artifacts, long/unicode labels and explicit leakage.

## Clarifications

No critical ambiguity needs chat clarification: measures and bounded presentation
are chosen transparently in the plan/intent, subject to Zach's acceptance. Existing
value routes are extended; quality contrasts retain their selection path and share
pair_budget. Lightweight candidate ranking is permitted for each target column;
only budgeted pairs get detailed group summaries/plots. No model/p-value selection,
HTML script, switchable axes, quality score or dynamic layout builder.

## Requirements

- **FR-001**: Compare each eligible target-column pair with light type-appropriate
  association; rank deterministically and label all measures descriptive, not causal.
- **FR-002**: Show measure/value/complete n/selection and excluded columns/reasons;
  support explicit config exclusions and disclose unrecognized leakage limits.
- **FR-003**: Keep selected target and quality pairs within pair_budget0–20; disclose
  the grouping reservation and rankings of candidates beyond the detail budget.
- **FR-004**: Provide bounded within-group summaries, missingness/rate denominators,
  group counts/shares, marked contrasts/rest comparison and small-group cautions.
- **FR-005**: Plot selected numeric pairs and category-bearing relationships with
  labelled original-value ticks, appropriate log views and explicit plotted coverage.
- **FR-006**: Explicitly skip target analysis without a target or with unusable target;
  preserve fallback, old artifacts, independent optional exports and deterministic bytes.
- **FR-007**: Implement all four FT-R19 follow-ups across supported report formats,
  keeping the HTML self-contained and script-free.
- **FR-008**: Check own planted/clean/late tables against docs/acceptance.md, repeat
  FT-R17 at1280/390 and publish found/missed/fixed/open evidence in one CLA-unticked PR.

### Key entities

Target ranking/exclusion, budgeted relationship, within-group summary/contrast,
relationship plot, positive-log coverage. All are derived evidence in the saved
artifact; source meanings remain inferred or explicitly supplied.

## Success Criteria

Every eligible target column has a ranking row or explicit exclusion. Hand-computed
Pearson/eta/Cramer's V fixtures and clean decoys pass, selected pair count never
exceeds budget, and planted group differences include size/caution/action. Reports
show all eight functional requirements and four polish items through tests/images.
All six format/width review combinations are inspected, with known misses openly
listed. Fresh processes produce identical outputs in a fixed dependency environment;
AEC has0errors. These do not claim independent owner acceptance.

## Assumptions

Per-group diagnostics are descriptive review prompts, not significance tests.
Cross-family association strengths are prioritization heuristics, not calibrated
comparable effects. Undeclared leakage cannot reliably be inferred from correlation.
No new runtime dependency; public fixtures remain source-pinned. PR#14's authorized
duplicate-line removal is inherited unchanged, not repeated by this implementation.
