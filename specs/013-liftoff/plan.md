# Implementation plan: liftoff

Python>=3.12, pinned pandas2.2.3/PyYAML already in core; all new logic stdlib and
existing modules. Optional SciPy stays optional. No dependency, server or dashboard.
Review-only Chromium/Playwright use the existing environment, not package requirements.

## Constitution check

PASS with disclosed DEC-079 boundary: candidate-only provisional computations are
isolated, not selected stage-two analyses. One connector/profile/artifact path;
Brief/form read saved evidence. Findings typed/provenanced, inference labelled,
no auto-configuration. Deterministic, no runtime dates or network. No protected edits.

## Design

- `liftoff.build_liftoff(data)` profiles once, calls configure.build_schema, existing
  timeseries.undeclared, rows.interval and timeseries.time_series on hypothetical
  declarations. Deep-copy default doc into schema2 profile plus liftoff block.
- `liftoff.zero_contrasts` computes only bounded zero contrasts, emitting no action.
- `liftoff.brief_html` renders plain sentences, rules, process and questions;
  details disclose repetitive/all findings and full measurement tables. Existing
  temporal_view tables/stems reused inside conditional disclosures with labels.
- configure.config_document/YAML_JS/render_page get optional liftoff schema support:
  indexed series checkboxes/value/grain selectors. Default schema remains unchanged.
  Untouched{}; hostile names safe; advisory manifest includes series declaration.
- CLI adds liftoff only (no --config); saves liftoff profile and HTML only after
  validation. Ordinary profile/render/export semantics unchanged. Saved artifact
  validation checks the additive liftoff envelope before rendering.
- Configurator/Brief styles use palette.theme_css plus token aliases; no duplicated
  colour source. Temporal stems/row findings inherit existing palette mapping.

## Verification

Tests first: no-date/short-date decoys; default-profile isolation; interval violation/
clean counts; periodic/constant event series; zeros/clean contrast; candidate caps;
malformed envelope; CLI failure/outputs/fresh seeds; Python/JS selection parity,
existingconfigure compatibility, hostile names and optional stats absence. Browser
DOM checks untouched{}, selections/download→profile, static Brief, 1280/390 light/
dark form/row/temporal views. Public pinned taxis acceptance plus synthetic table.
Full/core tests, fresh declared taxis and liftoff bytes (including exports), AEC
purpose/check/impact. PRmain stacked on#22 if unmerged; Kate first; CLA unticked.
