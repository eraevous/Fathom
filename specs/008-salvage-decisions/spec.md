# Feature Specification: Salvage decisions (DEC-043)

**Feature Branch**: salvage/dec-043 | **Created**: 2026-11-04 (CT)
**Status**: Authorized scope (DEC-043 items 1–3); implementation readings provisional.
**Input**: HO-DG-20261104-9B3S; Data-Guide salvage memo (documents only, DG-D4; no Data-Guide code read or copied).
Serves: P0@2, DG-RA@1, DG-RB@1, DG-RE@1, DG-RF@1, FT-R16@1, FT-R17@1, FT-R14@1.
Proposed record: FT-SD-R1@1 (provisional, for Zach to accept).

Zach's words (DEC-043, 2026-11-03 20:50 CT; repeated 23:27 CT): "Store stats as 6
significant figures instead of 10 decimals? ... - Yes." / "Bring back the
missingness-by-group test - Yes." / "kind-coloured tags, and dark mode - Yes".

## User Scenarios & Testing

### US1 — Small-scale columns keep their values (P1)

An analyst profiles a column measured at the 1e-12 scale (for example a residual or
a physical constant in SI units). Today `guide-profile.json` stores its percentiles,
mean, median and standard deviation as 0.0 because finite metrics are rounded to 10
fixed decimals (specs/001-data-review/data-model.md:21; univariate.py `safe`). After
this change those statistics keep 6 significant figures and the report shows them.

Acceptance: the 200-value fixture `tests/fixtures/salvage/tiny.csv` (mean 0, sd about
1e-12) fails on main (percentiles 0.0) and passes after: every stored percentile,
min/max/mean/median/population SD is nonzero and within 5e-6 relative of the exact
value. A normal-scale decoy (`normal.csv`) and a large-offset decoy (`offset.csv`,
epoch-second-like integers) produce the same stored statistics as main, byte for
byte, apart from the schema version.

### US2 — Missingness that varies with a group is reported, noise is not (P1)

An analyst learns that missingness in one column varies with a grouping column, as
an observation with its test, thresholds and counts disclosed. On data whose
missingness is independent of every group, nothing is reported.

Acceptance: a planted fixture (one region missing about 60% versus about 5% elsewhere)
yields one "varies with" observation; a null-data fixture of 20 seeded tables with
independent missingness yields zero missingness-by-group findings in all 20 (the
Data-Guide lesson: the naive version fired on noise 20 of 20 times); decoys for the
effect-size gate (significant but V < 0.15) and the group-size gate (large gap, small
groups) yield none. No `action` finding ever derives from the test.

### US3 — Readable in light and dark, with typed findings visible at a glance (P2)

A reader sees each finding tagged with its kind (observation, interpretation,
hypothesis, action, question), each kind in its own recorded colour, and the HTML
report follows the system light/dark preference, with a `data-theme` attribute able
to force either.

Acceptance: every colour used by the HTML/SVG/PDF/PowerPoint renderers comes from one
palette record; kind colours meet WCAG AA (4.5:1) against the panel in both themes;
the HTML stays script-free and byte-identical across fresh runs; actual screenshots
of the affected views in both modes at 1280/390 are inspected (FT-R17).

### Edge cases

All-zero and constant columns; negative tiny values; values below 1e-300; mixed
scales within one column (1e-12 and 1); epoch-like integers; non-finite input
(still null). Missingness: no missing values; fully missing columns; a single group;
more than 20 groups; groups below the minimum size; sparse expected counts;
numeric grouping columns (median split); the target column. Themes: print, a
`data-theme="light"` override on a dark system, Markdown (no colour).

## Requirements

- **FR-001**: Stored finite statistics keep at least 6 significant figures. Values
  are rounded to `max(10, 5 - floor(log10|x|))` decimal places: the previous 10
  decimals wherever |x| ≥ 1e-4, 6 significant figures below that. Zero and
  non-finite handling is unchanged.
- **FR-002**: Chart geometry is scale-aware: the same rule with 12 significant
  figures, so tiny-scale histograms and boxes keep their shape while normal-scale
  geometry (and so every normal-scale SVG) is unchanged.
- **FR-003**: The artifact `schema_version` becomes 2 for profiles and comparisons.
  The artifact validator (used by `guide render`, `compare`, `export`) accepts 1 and 2
  and rejects anything else. Version-1 artifacts render as before (their stored
  values are not reinterpreted).
- **FR-004**: A missingness-by-group test: for each column with partial missingness
  and each screened grouping column (the existing first-20, target-first screen;
  categorical/boolean/string labels or a numeric median split), with 2..20 groups,
  every group n ≥ 10 and Cochran's expected-count rule met, compute Pearson's
  chi-square on the missing/present × group table. Bonferroni over the tests actually
  run, family alpha 0.01; report only when p < 0.01/m **and** Cramér's V ≥ 0.15.
  The chi-square tail is computed in the standard library (no new dependency).
- **FR-005**: A reported result is one `observation` finding, generator
  `rule:missingness-test-v1`, rule `missingness_varies_with`, worded "Missingness in
  X varies with G", with the rates, n, chi-square, df, p, the Bonferroni threshold,
  m and V in its evidence. The artifact records the thresholds, m, skipped-test counts
  by reason, and up to 20 reported results under `quality.missingness_tests`.
- **FR-006**: A palette record in the renderer layer (`fathom.palette`) is the only
  source of colour: light and dark tokens, five kind colours per theme, the
  categorical series. CSS custom properties are generated from it; SVG marks keep
  their light colours as attributes (Markdown stays portable) and the HTML maps them
  to theme tokens in CSS.
- **FR-007**: Each finding in HTML carries a kind tag coloured by kind; kind section
  headings carry the same colour. Markdown, PDF and PowerPoint output are unchanged.
- **FR-008**: Dark mode follows `prefers-color-scheme: dark` unless
  `data-theme="light"` is set on the root; `data-theme="dark"` forces it. Print uses
  the light palette. No script.
- **FR-009**: Byte-identical output for identical inputs in a fixed dependency
  environment still holds for JSON, Markdown, HTML, PDF and PowerPoint.

### Reconciliation: "p-values never select actions"

specs/001-data-review/research.md:15 says p-values never select actions. FR-004/005
keep that rule:

1. The test's output is an **observation** with a disclosed threshold. It never
   emits an `action`, `hypothesis` or `interpretation`, and no other rule cites it as
   evidence for one.
2. It does not enter pair ranking, the pair budget, chart selection or target
   analysis. The existing descriptive missing-rate-spread rule (spread ≥ 0.30, which
   does select pairs and suggest a review) is unchanged and is not p-value based.
3. What the threshold selects is which observations are *stated*, the same role as
   every other disclosed rule threshold in `quality.rules`. A reader decides what to
   do; the report does not.

So a p-value can now decide whether an observation is written, never whether an
action is suggested.

### Parked (not implemented)

- **Exponent-first display, "(e-12)1"** (Zach, 2026-11-03: "I kinda want to
  optionally display it as (e-12)1 at some point, as it is a bit clearer to me";
  candidate C-22, DEC-047). Display only; stored values follow FR-001. Fixture when
  built: the sd 1e-12 column; decoy: ordinary-scale values keep plain notation.
  Today's display (`formatted`) shows `1e-12` style for |x| < 0.001.

### Out of scope

Relation strength bands and the 50-level / 50k-row caps (undecided); wide-by-period
and aggregate-row diagnostics (proposal); kind colours in PDF/PowerPoint; a theme
switch control (it would need script or a form hack); `guide validate` reading
artifacts (it validates CSV + config; see intent note).

### Key entities

`quality.missingness_tests` (method, thresholds, m, skipped counts, results); palette
record (light/dark tokens, kind colours, categorical series); artifact schema 2.

## Success Criteria

The 1e-12 fixture fails before and passes after; normal and offset decoy artifacts
equal main's apart from `schema_version` and the additive `quality.missingness_tests`
block. The planted fixture reports one observation; the 20 null tables and the two
gate decoys report none; no action cites the test. Palette tests show a single
colour source and AA contrast in both themes. Full suite passes with extras and in
core; fresh processes give identical bytes; `aec check` has 0 errors. Screenshots of
the affected views in both modes are inspected. None of this claims Zach's acceptance.

## Assumptions

- The minimum group size (10) and the expected-count rule are Fathom's own readings;
  the memo records only "minimum group size". Thresholds alpha 0.01, Bonferroni and
  V ≥ 0.15 are from DEC-043.
- FR-001's "never fewer than 10 decimals" floor is a provisional reading of "6
  significant figures instead of 10 decimals": a literal per-value 6-significant-figure
  rule turns the offset fixture's percentiles 1730000133.67, 1730000656.5 and
  1730001179.33 into the same 1730000000, the same collapse in the other direction.
  For Zach to accept or reverse; the literal rule is a one-line change.
- The light palette keeps Fathom's existing teal colours (no visual churn); the
  Data-Guide hex values were assistant-authored and were not adopted wholesale. Kind
  hues follow the memo's roles (observation blue, interpretation purple, hypothesis
  amber, action green, question red), darkened or lightened to pass AA.
