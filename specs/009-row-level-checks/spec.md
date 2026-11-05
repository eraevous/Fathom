# Feature Specification: row structure and conditional zeros

**Feature Branch**: `009-row-level-checks` | **Created**: 2026-11-04 CT
**Status**: Draft for Zach; specification/fixtures only in this PR.
**Input**: HO-DG-20261104-XKSJ, authorized next-slice spec items.
Serves: P0@2, DG-RA@1, DG-RB@1, DG-RC@1, DG-RE@1, DG-RF@1,
DG-A1@1, FT-R4@2, FT-R6@3. Proposed requirement: FT-ROW-R1@1.

The objective is to reveal row structure an analyst could overlook, without
claiming a row's domain meaning or prescribing an analysis. All thresholds and
inferred scopes below are proposed implementation readings, not accepted policy.
The historical experiment concerned slice1, not today's main. Its private reports
were read as authorized; no held-out data or other arms' code was opened or copied.

## User Scenarios & Testing

### US1 — See rows with no recorded values (P1)

An analyst sees that rows retain names/metadata but no measured values.
Given `empty-values.csv`, profiling must state **9 of18rows have no recorded values
in2010/2011/2012**; identify the value-column scope as inferred; give row positions
and a short label sample behind evidence. Ask whether those rows should represent
unmeasured entities, omitted observations or a different row unit. Do not recommend
dropping rows. `empty-values-clean.csv` must produce no such finding; zero is present.

### US2 — Notice a possible mix of row units (P1)

Given `mixed-units.csv`, state **5 of12labels match disclosed aggregate cues**, with
the exact matched phrases and labels. Ask whether these aggregate-labelled rows and
the7other rows have comparable units, overlap or belong in separate documentation.
Other labels remain unclassified; do not assert they are countries. The clean decoy
has no aggregate cues and produces no mixed-unit finding. This is lexical evidence,
not geographic verification, and never establishes the true grain by itself.

### US3 — Understand repeated keys before treating rows as independent (P1)

Given `repeated-key.csv`, report **210distinct individual labels,4rows per label**,
100% of nonmissing keys covered by that pattern; `hinc` and `psize` vary between
keys but are constant within every key; **exactly one choice=1 in every key**.
Ask whether rows represent alternatives/repeated observations for an entity.
Do not claim `individual` is an accepted key, that the rows are independent, or
select a conditional-choice/repeated-measures analysis. The unique-key decoy must
not produce a repeated-key finding. Changing one key's `choice` to two1s must
report209/210passing groups, not repeat the universal statement. Missing/invalid
choice values make that group's result unknown, never an implicit zero.

### US4 — Locate category-concentrated zeros (P1)

Given `zero-concentration.csv`, state **210of210ttme zeros occur at mode4**;
mode4's zero rate is210/210, the rest0/630. Ask whether zero is structural,
a placeholder, or a recorded value under different collection rules. Treat mode
as observed labels/codes with inferred meaning. Do not recode, impute, transform,
choose a model or select a pair/plot. The balanced-zero decoy has210zeros spread
across4groups at similar rates and must not produce this concentration finding.

### Edge cases

Empty tables; no scoped value columns; all-missing value columns; literal0;
whitespace-only cells; literal NA/NULL remain recorded strings under the existing
connector; missing keys; one key only; irregular repetitions; missing/invalid
binary cells; all-zero columns; one category; a dominant category with equal zero
rates; labels that resemble aggregates but mean something else; more candidates
than the screening cap; renamed/reordered columns; stable tie ordering and examples.

## Requirements

### Functional Requirements

- **FR-001 — Scope and provenance.** Each check records its generator/rule version,
  complete scope, threshold values, eligible/omitted candidate counts, denominators,
  total matches and at most10row-position/label examples. Evidence is saved in the
  artifact; every report is derived from it. Examples are original1-based data-row
  positions, not physical CSV lines. No raw rows beyond existing sample limits.
- **FR-002 — Blank value rows.** Scope is declared value columns if supplied;
  otherwise infer it only from at least3four-digit year headings1900..2099 whose
  cells are numeric-compatible or empty. Mark that inference. Scan every row;
  blank means the connector's canonical missing cell, not numeric0. Report if at
  least1row is empty across every scoped value column. Without a defensible scope,
  say this check is unavailable and why; wholly blank rows may be counted separately.
  Metadata never silently counts as a measured value.
- **FR-003 — Possible unit mix.** Prefer declared row-label/aggregate-label metadata.
  Otherwise screen at most2text label columns (name/label/entity cues first, then
  lexical); match case-insensitive whole words/phrases, after whitespace normalization:
  `aggregate`, `region`, `total`, `World`, `East Asia & Pacific`, `Europe & Central Asia`,
  `Latin America & Caribbean`, `Middle East & North Africa`, `Sub-Saharan Africa`.
  Record the cue list and matching rule. Report a mixed-unit question only when
  1..n-1nonmissing labels match. Never classify the remainder by exclusion. No
  network lookup or authoritative geography claim; qualifiers/unseen names can miss.
- **FR-004 — Repetition.** Screen at most3declared or name-cued key columns
  (`id`, `_id` suffix, `individual`, `identifier`, `key`), declared first then lexical.
  Require at least3distinct nonmissing keys and a modal group size2..20covering
  at least90% of nonmissing-key rows. State the full size distribution and exceptions,
  including missing keys. Examine within-key invariance over complete groups;
  report counts, unknowns, and up to5constant-within-key columns that have at least
  2different values between keys. Global constants are a different existing check.
- **FR-005 — One-positive-per-key.** For the repeated keys above, inspect at most
  3declared/target or name-cued binary columns (`choice`, `selected`, `chosen`), then
  lexical; observed finite0/1 values only. State number of keys with exactly one1,
  failures and unknown groups. A universal statement requires every eligible key
  to pass with no unknowns. Preserve the per-key count distribution in evidence.
- **FR-006 — Conditional zeros.** Numeric columns with at least10finite zeros are
  screened by zero count descending then lexical, at most5. Grouping candidates are
  declared group/target first, then low-cardinality observed labels or whole-number
  codes (2..20levels), at most5; key candidates excluded. Group-versus-rest finite n
  must each be at least10. Report only if a group contains at least90% of all zeros
  and its zero-rate exceeds the rest by at least0.30. State all zero counts, finite
  denominators, missing/invalid counts and both rates. All-zero or rate-balanced
  columns do not meet the contrast. At most5reported patterns; disclose omissions.
- **FR-007 — Observation and question only.** New measured facts are observations;
  possible meanings are questions, explicitly uncertain. New rule IDs never emit
  actions, enter selection/ranking inputs, change `pair_budget`, alter chart lists,
  or cause any other rule to select an analysis. Existing independent checks can
  still speak. Assert selected pairs/charts are identical with these checks on/off.
- **FR-008 — Human report.** One short sentence per pattern and a bounded count/
  denominator table, grouped in Observations/Open questions. At most one repetition
  summary per key and one mix question per label column. Preserve FT-R6@3 section
  order and existing summary/full toggle. Technical objects, thresholds, row samples
  and uncertainty details stay behind native disclosures in HTML; Markdown uses
  readable tables and optional detail. Never dump serialized evidence as report prose.
- **FR-009 — Reproducibility/degradation.** Fixed ordering, no sampling without the
  recorded seed; same artifacts and fresh-process reports are byte-identical in a
  fixed environment. Checks use the core path and work with optional statistics/
  export packages absent. Older artifacts remain renderable; new fields are additive.

### Key Entities

Value scope (columns/status/basis); row-blank result; label-cue result; repeated-key
summary (size distribution/invariant columns/binary counts); conditional-zero
summary; typed findings; exact evidence; candidate coverage and omissions.

## Success Criteria

- **SC-001:** All four planted fixture pairs meet the exact assertions in US1–4;
  each clean decoy is silent for its corresponding rule. A failure in any group
  prevents a universal claim. Boundary/unknown cases do not invent domain facts.
- **SC-002:** From the report alone a reader can identify the pattern, affected
  rows/columns, count/denominator, inferred scope and what remains unknown, without
  opening the data or a raw JSON object. Owner-held usefulness acceptance remains
  separate; fixture truth checks are not proof that the feature is useful generally.
- **SC-003:** Every new finding is an observation/question with evidence/provenance;
  unchanged selection/ranking/charts and clean/violation/absence/fresh-byte tests pass.
- **SC-004:** Actual1280/390HTML and available PDF/PPTX views are inspected under
  FT-R17 when implemented, with found/missed and readability limits in that PR.

## Assumptions

This PR proposes the specification and fixtures, not a built slice or new accepted
requirements. Metadata controls, cue vocabulary and numeric thresholds are narrower
readings for Zach; a later plan must choose their exact configuration keys and
artifact shape. Core dependencies remain enough; no new dependency proposed.
C-22 exponent-first display is parked because it is undecided and unrelated to row
structure. Arbitrary mixed-unit recognition, composite keys, network verification,
causal conclusions, transformations and automatic analysis selection are out of scope.
