# Feature Specification: Data quality and a readable working report

**Feature Branch**: `002-data-quality`
**Created**: 2026-11-01
**Status**: Implements accepted scope; implementation and usefulness remain for review.
**Input**: HO-20261101-006, slice 2, following merged PR #1 and decisions PR #3.

Serves: P0@2, FT-R2@2, FT-R3@2, FT-R4@2, FT-R5@1, FT-R6@2,
DG-RA@1, DG-RB@1, DG-RC@1, DG-RE@1, DG-RF@1, DG-A1@1, DG-D5@2.

## Clarifications

### Session 2026-11-01

Agent readings from the documents: summary/usefulness/unknowns share the opening;
FT-R3 ranks existing value routes and FT-R2 missingness contrasts, without new
FT-R7 methods; structural quality groups are findings, not association matrices;
thresholds and incomplete screening are explicit. The absent reference is not
needed to implement FT-R6. Scope, entities, interaction/error handling, limits,
terminology and completion signals are clear after these readings. Scale and
independent acceptance are explicitly limited. No owner answers are invented.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Notice consequential quality problems (Priority: P1)

An analyst receives findings rather than a collection of statistics: unusual
placeholder/dummy values, dominant/constant columns, duplicate/lockstep columns,
shared or conditional missingness, temporal gaps, strong mean/median distortion
and repeated rows. Each observation gives counts, scope, evidence and a cautious
interpretation or question, plus a suggested next step.

**Why this priority**: FT-R2 and DG-D5 put data quality first; a dictionary's maximum
alone does not tell an analyst that a sentinel should be investigated.
**Independent Test**: planted violations and clean decoys for every diagnostic,
verified in the report itself under docs/acceptance.md.

**Acceptance Scenarios**:

1. Given a sparse extreme numeric code and a literal dummy label, profiling shows
   their counts/shares, labelled hypotheses and review actions; benign decoys do
   not receive those diagnoses.
2. Given duplicated/lockstep columns or shared missing rows, the report names the
   affected columns and measured agreement/pattern, without asserting a cause.
3. Given missingness concentrated in a segment, a recurring-date gap, or a strongly
   skewed measure, the report explains the observed pattern and its practical
   consequence, with thresholds and limits accessible in evidence.

### User Story 2 - Spend the relationship budget on relevant evidence (Priority: P2)

An analyst declares a question or target and sees the most relevant eligible
relationships first, with a published ranking rule. Reordered columns cannot
promote a weaker association over a stronger one. Redundant and near-constant
value columns do not crowd out useful candidates. Missingness contrasts are
eligible quality relationships; no new general target-analysis engine is added.

**Why this priority**: FT-R3 makes a small output budget useful rather than arbitrary.
**Independent Test**: a stronger candidate placed last wins a budget of one;
near-duplicate and near-constant decoys do not consume it; ties are deterministic.

**Acceptance Scenarios**:

1. Given a stronger later candidate, then it ranks ahead of a weaker earlier one;
   the artifact/report state scores, ranking basis and exclusions.
2. Given more eligible quality/target relationships than the shared budget, then
   total reported relationships never exceed that budget, and omitted candidates
   have reasons; basic structural quality groups still appear as findings.

### User Story 3 - Read the report without reading the raw data (Priority: P1)

A reader first sees dataset-level counts/shares and what they mean for review,
what is useful, and what the table cannot establish. Findings are grouped by
kind with one plain sentence and expandable evidence. Repetitive type/meaning
findings are summarized. Relations follow, then a compact dictionary and provenance.
One HTML control changes the summary into the full per-item view and back.

**Why this priority**: FT-R5/FT-R6 and acceptance require standalone documentation.
**Independent Test**: offline HTML and Markdown from a saved artifact; the native
view switch reveals all original finding items without recomputation or network.

**Acceptance Scenarios**:

1. Given a profile, the opening shows shape, complete rows/columns (counts/shares),
   duplicates/lockstep, inferred type counts, constant/near-constant columns and
   missing cells, each linked to supporting findings.
2. Given many columns, the default collapses repetitive per-column type/meaning
   findings into summaries with affected column lists; one HTML click shows every
   original item and its evidence, and another restores the summary.
3. Given a saved slice-1 artifact, rendering remains supported and clearly marks
   new raw-row-dependent summary measurements unavailable rather than inventing them.

### Edge Cases

Empty tables, all-missing or constant columns, tiny samples, conflicting type
overrides, multiple sentinel candidates, unique identifiers, date schedules not
established by the table, zero budgets, equal scores, wide-table screening limits,
and hostile text remain deterministic and explicitly bounded. Nothing is cleaned.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Surface every FT-R2 diagnostic family as typed evidenced findings,
  not only dictionary statistics. Meanings remain hypotheses/questions. Retain
  violations, clean decoys and exact expected measurements for each family.
- **FR-002**: Publish deterministic thresholds, sample minima, candidate-screening
  rules and any omitted analysis; never equate a diagnostic with a confirmed defect.
- **FR-003**: Rank eligible existing target routes and quality missingness contrasts
  by declared focus then measured strength, within one shared pair budget. Exclude
  near-duplicate and near-constant value columns, explain all exclusions and ties.
- **FR-004**: Add a linked dataset summary containing all FT-R5 figures, including
  complete-row and complete-column counts/shares and inferred type counts.
- **FR-005**: Produce person-first HTML/Markdown in FT-R6 order; no raw JSON dump is
  the primary report. Group repetitive type/meaning findings. Default HTML is
  summarized; one self-contained control switches all findings to full detail.
  Individual evidence is a click away. Keep the complete findings in the artifact.
- **FR-006**: Render solely from the saved artifact. Preserve slice-1 compatibility,
  stable findings/evidence links, context-first comparisons, text escaping and
  byte-identical outputs for fixed inputs/dependencies. Missing optional SciPy
  still degrades cleanly. New analysis is dependency-free.
- **FR-007**: Check each change against docs/acceptance.md using authored synthetic
  planted tables and an additional builder holdout written after the rules; list
  found, missed and false alarms per table in validation.md and the PR. This is
  builder evidence, not Zach/Kate's independent acceptance.
- **FR-008**: Do not implement FT-R7/FT-R8, advanced univariate/bivariate/multivariate
  methods, narratives or new connectors. Relations and dictionary sections remain
  separate so those future capabilities can be added without changing this order.

### Key Entities *(include if feature involves data)*

- Quality evidence: diagnostic rule, counts/shares, affected columns/rows or date
  intervals, thresholds, assumptions and conditional follow-up.
- Dataset summary: counts, nullable shares, inferred-type totals and finding links.
- Ranked candidate: pair/method, eligibility, focus, strength, selection or reason.
- Finding view group: derived summary plus stable IDs of the original findings.
- Acceptance table: public synthetic inputs, planted list and found/missed ledger.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every diagnostic family has a report-visible planted violation and
  clean decoy, with exact expected evidence and no invented domain explanation.
- **SC-002**: The strongest eligible later candidate wins a one-pair budget; all
  omitted candidates have reasons and total displayed relationships obey the budget.
- **SC-003**: Every opening summary figure has a valid finding link, and every
  full-view finding remains accessible from the default report.
- **SC-004**: Saved-artifact rendering and repeated fresh-process runs match bytes;
  summaries, full view, dictionary, uncertainty and provenance are offline-readable.
- **SC-005**: The PR lists what was found/missed on each builder table and leaves
  independent usefulness acceptance explicitly unclaimed.

## Assumptions

Scope remains local CSV/wide. Numeric/temporal checks depend on effective type and
keep inference labels. A free-text question is not interpreted by an AI; literal
column mentions can focus quality contrasts. Exact thresholds are implementation
readings in the plan/intent note. Accepted requirements already cover this feature;
no new requirement acceptance is needed or claimed.
