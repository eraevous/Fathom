# Feature Specification: Report polish

**Branch**:006-report-polish | **Created**:2026-11-02 | **Input**:HO-20261102-003
**Status**: Authorized FT-R18 scope, implementation readings provisional.
Serves: P0@2, FT-R18@1, FT-R17@1, FT-R16@1, DG-A1@1, DG-RE@1, DG-RF@1.

## Clarifications

FT-R18 supersedes the builder's fixed-width/all-positive-log readings in spec005.
Native column disclosures and static CSS grids/scaling are explicitly authorized
here; no layout builder, chart/axis switch, filtering or target/group analysis.
Summary PPTX is <=12slides by default, full deck explicitly optional. Data and
inference authority unchanged. Wider design questions take narrower documented
readings; no chat clarification needed.

## User Scenarios & Testing

### US1 — Scan and inspect a column (P1)

Default report shows compact collapsed column headers with name/type/missing count;
expanding one reveals compact logical statistics beside charts, scaling to available
width. At phone width normal CSS stacking preserves readable labels. Examples are
formatted with raw values preserved separately. Numeric tick labels show intermediate
positions; box annotations and axis titles remain distinct/unclipped. Months are
capitalized; identifier/near-unique top-N plots are replaced by an explanation.
Independent test: synthetic large/skewed/close-quartile columns and public films;
measure default and fully expanded heights at1280, visually inspect1280/390.

### US2 — Inspect zeros and positive distributions (P1)

Skewed measures containing zeros retain a positive-only log view with explicit
positive/zero/negative/invalid counts. No silent exclusion. Linear view remains.
Independent test: positive+zero skew versus benign/constant/no-positive decoys.

### US3 — Share a concise deck (P1)

Default export provides a deterministic summary near a dozen slides: identity,
overview, bounded review findings/unknowns and selected representative charts.
Omitted detail is stated; full deck is optional and includes all available topics.
Independent test: synthetic multi-column report, both modes, optional absence and
fresh-process byte repeatability; actual PowerPoint screenshots.

### Edge cases

Empty/constant/all-zero/all-negative columns, close quartiles, long labels, huge/tiny
numbers, unknown/declared units, identifier overrides, <5values, legacy artifacts,
missing export packages, phone width, more charts/findings than summary budget.

## Requirements

- **FR-001**: Reduce default report height through compact column disclosures/grid;
  statistics compact and charts scale; report both default/expanded heights.
- **FR-002**: Intermediate formatted ticks; no overlapping box annotations or clipped
  axis titles at1280/390; title/axis text alternatives remain available.
- **FR-003**: Positive-only log views accept zero-containing skewed columns and
  explicitly count excluded zeros/negatives/invalid values; retain original data.
- **FR-004**: Logical ordered statistics, magnitude/unit-aware rounding and formatted
  examples; capitalized months; identifier/near-unique top-N suppression explained.
- **FR-005**: Summary PPTX defaults<=12slides with visible scope/omission notice;
  full deck optional; all outputs remain deterministic/artifact-only/offline.
- **FR-006**: Repeat FT-R17 for HTML/PDF/PPTX1280/390, check acceptance tables, list
  fixes/open issues with screenshots; open one stacked PR, CLA unchecked, then stop.

## Key entities

Column disclosure/grid; formatted statistic/example; tick specification; positive
log coverage; summary/full deck selection. Raw artifact values remain authoritative.

## Success Criteria

All seven FT-R18 items have explicit fixture/image checks; public films default
height falls by at least50% on the same input/config/width, and expanded height
is disclosed. Tick positions include interior values, zero exclusions are explicit,
summary<=12slides and full optional. Tests/bytes/core degradation pass; AEC0errors.
All six format/width combinations reviewed; independent acceptance not claimed.

## Assumptions

FT-R18 authorizes simple grid/disclosure/viewport fitting despite earlier builder
limits. No new runtime dependency. Public fixtures pinned/sourced; no earlier
Data Guide code. PR#11/#12 integration/rebase follows user instruction, no PR merges.
