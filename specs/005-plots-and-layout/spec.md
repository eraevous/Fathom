# Feature Specification: Plots and layout

**Branch**: 005-plots-and-layout | **Created**: 2026-11-02
**Status**: Authorized scope; FT-R15 detail/readings provisional.
**Input**: HO-20261102-002, following merged specs001–004.

Serves: P0@2, FT-R15@1, FT-R16@1, FT-R17@1, FT-R10@1, FT-R4@2,
DG-A1@1, DG-RB@1, DG-RE@1, DG-RF@1, DG-D7@1.

## Clarifications

Fixed single-column composition, existing disclosures, no new responsive
breakpoints/rearrangement/filtering/chart switching. Phone review includes
fixed-page/slide scaling and chart panning limits. Missingness uses exact row
masks, not new pairs or within-group analysis. Algorithm choices remain proposals.

## User Scenarios & Testing

### US1 — Review a column without technical evidence (P1)

Full-width entries show meaning/type basis, formatted aligned statistics,
frequency tables and inline plots. Raw evidence is separately disclosed.
Independent test: long names, million-scale numbers, fractions, unknown units and
time-named numeric columns in a synthetic report. Labels left/numbers right;
consistent widths and grouped counts; value/count/share tables; bar labels beside
bars with counts at ends. Time alone implies no date semantics.

### US2 — Inspect distributions and missingness (P1)

Numeric histogram/box/ECDF and additional log view for strong positive skew;
category other/coverage; text length histogram; date counts/weekday/month;
exact missingness masks. Independent test: exact counts/shares, violating and clean
decoys. ECDF monotone/end100%; log never silently excludes zeros/negatives;
every chart titled/labelled. Old artifacts remain usable.

### US3 — Review the delivered report (P1)

Render HTML, PDF and PPTX at1280px/390px, visually compare with chart/typography
practice and comparable profiling reports. Fix or list problems with PR screenshots.
Independent test: before/after screenshots, reproduction instructions, source
references, issue ledger and planted/clean/late found/missed results.
claude:aec's independent pass follows; builder does not simulate it.

### Edge cases

Empty/constant/all-missing columns; zero/negative/huge values; many categories/masks;
long/unicode/HTML-like labels; long date spans; absent extras; old artifacts; phone.

## Requirements

- **FR-001**: Full-width entries expose formatted aligned statistics and inline
  titled/labelled plots; nested raw evidence stays disclosed.
- **FR-002**: Value/count/share tables state denominators; chart labels/end counts
  remain adjacent; section widths/spacing remain consistent.
- **FR-003**: Provide US2 plots with truthful scales, counts, coverage and bounds.
- **FR-004**: Remove time-only date hints from sketch and partial-parse routing;
  actual parsed dates and human declarations retain their authority.
- **FR-005**: Artifact-only HTML/Markdown/PDF/PPTX remain offline/deterministic;
  old artifacts and optional absence work without new runtime dependencies.
- **FR-006**: Complete screenshot/practice review and acceptance-table ledger before
  one PR with CLA unchecked; report all observed remaining problems.

### Key entities

Column review entry, labelled chart specification, exact missingness-mask summary,
visual-review issue/screenshot. All content comes from the saved result.

## Success Criteria

- **SC-001**: Every tested column has visible statistics/plots without raw evidence;
  chart totals agree with planted tables.
- **SC-002**: All six format/width combinations are visually reviewed and linked;
  every observed issue is fixed or explicitly open.
- **SC-003**: Repeated bytes and regression/degradation checks pass; AEC0errors/warnings.
- **SC-004**: Planted consequences/unknowns are clear from reports alone; misses
  disclosed without claiming independent acceptance.

## Assumptions

No dynamic layouts, target/group analysis, switchable axes, score or AI layer.
Public practice references guide review, not scope. FT-R15 detail stays provisional.
