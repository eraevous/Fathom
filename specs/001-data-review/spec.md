# Feature Specification: Data review to decisions

**Feature Branch**: `001-data-review`

**Created**: 2026-11-01

**Status**: Provisional — proposed for Zach to accept, not accepted by implementation or merge.

**Input**: HO-20261101-004: build the smallest data-to-decisions MVP from repository documents.

Serves: P0@2, DG-RA@1, DG-RB@1, DG-RC@1, DG-RD@1, DG-RE@1, DG-RF@1,
DG-D1@1, DG-D2@1, DG-D3@1, DG-D4@1, DG-A1@1, DG-A3@1, DG-A4@1.
Feature requirement: FT-R1@1 (provisional).

## Clarifications

### Session 2026-11-01

No owner questions asked: the handoff explicitly requires documented narrower
readings. These are agent resolutions, not answers attributed to Zach.

- MVP breadth → choose a CSV/wide review decision loop (`DG-D1` takes precedence
  over April phasing); all deferred breadth is listed under Assumptions.
- Meaning of decision → evidenced conditional review actions plus human rationale;
  no automatic cleaning or general fitness claim (`DG-D1`, `DG-RB`).
- Selection/unknowns → explicit target within a budget; unsupplied semantics remain
  questions (`DG-RC`, `DG-RB`, AGENTS). Detailed readings: intent note items 3–6.
- Artifact/context → a versioned saved profile, explicit unknown dates, aggregate
  comparisons and context first (`DG-RE`, `DG-RD`). Intent note items 7–8.
- Operational breadth → local in-memory use; no service/scale commitment or remote
  credentials needed for the CSV slice. Intent note items 1, 9–10.

Coverage scan: functional scope, domain model, interaction/errors, integration,
constraints, terminology and completion signals resolved within this slice.
Performance/scalability are deliberately bounded to local in-memory use; service
availability and localization are outside scope. Security is local safe input and
text-only report rendering. No outstanding question prevents planning.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Decide what needs review before using a table (Priority: P1)

An analyst supplies a public or synthetic CSV and optionally declares a decision,
target, variable meanings/types, row unit and generating process. They receive a
standalone dictionary and an evidenced review queue: inspect missing values,
review repeated records without assuming they are errors, and resolve unknown
semantics before proceeding. They can retain a human decision and its rationale
in a repeatable working record. Without a question, the purpose is reference,
understanding, QA and validation. Fathom recommends review; the analyst decides.

**Why this priority**: a decision about the data itself satisfies `DG-D1`; this
vertical slice includes the documentation and uncertainty needed to act on it.

**Independent Test**: profile the synthetic dirty and clean tables. A reader can
locate each proposed action's counts and source, see the unknown row unit and
missingness mechanism, and record whether to investigate or proceed.

**Acceptance Scenarios**:

1. **Given** missing cells and repeated rows, **When** profiled, **Then** measured
   observations support separate review actions; clean decoys do not get them.
2. **Given** encoded numeric values with no domain explanation, **When** profiled,
   **Then** the numeric reading is labelled inferred with reasons, confidence and
   alternatives; a human categorical override is effective and keeps the inference.
3. **Given** no declared intent, **When** profiled, **Then** the artifact and
   offline report describe documentation/QA usefulness and open questions, not
   invented business meaning or permission to model.

### User Story 2 - Investigate only a declared relationship (Priority: P2)

An analyst names a target and a question. Fathom screens other columns in input
order within a declared pair budget, shows numeric associations or grouped numeric
summaries as appropriate, and explains every exclusion. Useful results based on
inferred types stay visible and labelled. Relationships never imply causation.

**Why this priority**: it extends the working record to explicit questions without
turning the first pass into an all-pairs report.

**Independent Test**: a known numeric relationship produces its expected
coefficient; a categorical target produces group counts/means; absent targets,
incompatible types, constant values and budget limits get explicit reasons.

**Acceptance Scenarios**:

1. **Given** a numeric target and a budget of one, **When** three candidates are
   available, **Then** at most one eligible relationship is measured and every
   remaining candidate has an exclusion reason.
2. **Given** no target, **When** profiled, **Then** no pair analysis occurs and the
   report explains how to request one.

### User Story 3 - Decide what to review after a transformation (Priority: P3)

An analyst profiles a changed CSV and compares saved profiles. Snapshot dates,
sources, transformations and other recorded changes appear before measured
deltas. Changes in row/column counts, missingness, duplicates and shared-column
types are explicit. Row-level lineage and causes remain unknown.

**Why this priority**: provides the accepted iterative workflow without adding a
transformation engine or claiming to know why a delta occurred.

**Independent Test**: compare the dirty table with its documented synthetic
revision; confirm contexts precede exact deltas and no causal claim is added.

**Acceptance Scenarios**:

1. **Given** two contexts and an added column, **When** compared, **Then** both
   contexts and their differences precede deltas and added/removed columns.
2. **Given** two identical profiles, **When** compared, **Then** measured deltas
   are zero and lineage is still explicitly unknown.

### Edge Cases

- Empty/header-only tables retain their schema; no undefined numeric result is
  invented. Duplicate/blank headers, ragged rows, invalid configuration, unknown
  column references, unsupported schema modes and unsupported artifact versions
  fail with a useful error before reports are written.
- Blank/whitespace cells are missing; literal `NA`, `null` and `0` remain values.
- Numeric-looking identifiers with leading zeros remain strings unless overridden.
  Non-finite numbers never enter metrics or serialized non-standard numbers.
- Unavailable optional analysis enrichments leave core results available and
  explicitly mark the omitted enrichment.
- User text and table content are displayed as text in exported reports.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Load a single local UTF-8 CSV, preserving input column order and raw
  values, plus explicit source context and optional human metadata. Support wide
  tables; reject a declared long contract with a clear limitation.
- **FR-002**: Produce shape, duplicate count, column counts/nulls/distinct values,
  bounded examples/frequencies, observed storage type, inferred semantic reading
  and effective type. Route numeric, categorical, boolean, temporal and string
  profiles; preserve overrides separately from inference.
- **FR-003**: Produce typed, attributed findings with evidence, uncertainty and
  provenance. Link review actions to observations; retain human decisions and
  rationales separately. Unknown row unit, generating process, meanings and
  missingness mechanism must remain questions unless supplied by a human.
- **FR-004**: Select pairs only against a declared target, with budget 0–20
  (default 5); give excluded columns/reasons. Numeric pairs use complete finite
  cases; categorical/boolean × numeric pairs show group counts/means. Unsupported
  combinations are reported, not guessed. Never assert causal explanations.
- **FR-005**: Emit versioned `guide-profile.json` as the interface; derive Markdown
  and self-contained HTML with embedded visual evidence entirely from a saved
  artifact. Keep the narrative annotations slot empty in this slice.
- **FR-006**: Re-profile and compare artifacts, presenting context differences
  before measured deltas and explicitly disclaiming row-level lineage.
- **FR-007**: Provide quick-file, non-interactive configuration, render, compare,
  schema validation and version commands. Interactive guidance is deferred.
- **FR-008**: All outputs are byte-identical for identical inputs, configuration,
  artifact version and available dependency set. Never insert runtime timestamps.
  Each diagnostic has a violating fixture and a clean decoy. Test metrics,
  routing, optional-dependency degradation and the decisions supported.
- **FR-009**: Keep data processing local, with only public/synthetic committed
  examples. No credentials, remote connector, model fitting or AI narrative.

### Key Entities *(include if feature involves data)*

- **Table and schema contract**: ordered columns/rows, declared shape, source.
- **Profile context**: declared snapshot date, source, typed transformations and
  other changes; absent fields remain unknown.
- **Column dictionary entry**: measured facts, inferred reading, human override,
  meaning and type-directed summaries.
- **Finding**: observation, interpretation, hypothesis, action or question; stable
  identity, evidence, generator, uncertainty and source provenance.
- **Working record**: declared purpose, human context and decisions with rationale.
- **Profile artifact / comparison**: versioned evidence and its derived views.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every review action in the dirty fixture links to its measured
  evidence; the clean decoy produces zero missingness/duplicate review actions.
- **SC-002**: A reader can identify what to inspect, what remains unknown and why
  a result is shown from the exported report alone, without the original CSV.
- **SC-003**: All numeric fixture counts and summaries match hand-calculated
  expectations; selected relationship count never exceeds the stated budget.
- **SC-004**: Repeated runs and fresh rendering of a saved artifact produce
  identical bytes; comparison shows both contexts before any measured delta.
- **SC-005**: An unavailable optional enrichment leaves every core statistic and
  supported decision intact, with an explicit unavailable status.

## Assumptions

- Small, in-memory, single-table use is sufficient to demonstrate the decision
  loop. No performance/service-level claim or general project coverage is made.
- The later `DG-D1` outcome takes priority over the April connector/CLI checklist.
  This MVP slice uses CSV/wide only; the full April connector list, globs, long
  shape support, guided UI and advanced EDA remain future slices, not completed.
- Review actions are conditional suggestions, never automatic deletion/imputation
  or a claim that a dataset is fit for a business use.
- Exact rules/thresholds, wire format and command names are proposed in the plan.
  The scope and all narrower readings are recorded in the intent note.
