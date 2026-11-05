# Plan: Salvage decisions (DEC-043)

Python 3.12 CLI/library; existing pandas/PyYAML, optional SciPy/ReportLab/python-pptx.
**No new dependency, runtime or optional.** The chi-square upper tail is the
regularized upper incomplete gamma function Q(df/2, x/2), computed with `math.lgamma`
by series (x < a+1) or Lentz continued fraction (otherwise), as in standard numerical
references. Justification for not using SciPy: SciPy is optional here, and an
observation that appears only when SciPy is installed would make the report depend on
an extra; the stdlib version is deterministic and small. When SciPy is installed, a
test cross-checks the stdlib tail against `scipy.stats.chi2.sf` (skipped otherwise).
Review-only tools (not dependencies): headless Chrome via Playwright for screenshots.

## Constitution check

PASS. One data flow: the profiler computes, renderers read only the artifact.
Findings typed and attributed (the test is an observation with generator and
evidence). Inference not stated as fact (wording: "varies with", no mechanism).
The question still selects the analysis (the test adds no pairs, plots or budget use).
Artifact versioned (schema 2, validator accepts 1 and 2). Deterministic bytes;
optional extras degrade. Synthetic fixtures only. No protected-file edits.

## Design

1. **Storage (FR-001..003).** `univariate.safe` becomes the single stored-number
   rule `stored(n, 6)`; `profiler.rounded`, `quality` rounding and `target` (which
   imports `safe`) use it. `univariate.geometry(n)` (12 figures) replaces `safe` for
   histogram edges and the univariate box. `models.SCHEMA_VERSIONS = (1, 2)`;
   profile/compare write 2. Quality fingerprint rounding (1e-8 affine signature) is
   a comparison tolerance, not a stored statistic, and is unchanged.
2. **Missingness test (FR-004/005).** New functions in `quality.py`:
   `chi_square_sf(x, df)`, `missingness_table_test(groups)` and the scan inside
   `quality_profile` after the existing spread rule, reusing its grouping labels.
   Bonferroni m = number of eligible tests run. Results sorted by (adjusted p, -V,
   column, group) and capped at 20 stored, remainder counted. Findings emitted as
   observations only; the scan does not touch `missing_candidates`.
3. **Palette (FR-006..008).** New `fathom/palette.py` holds the record. It is a
   separate module only to avoid an import cycle (renderers imports charts, charts
   would import renderers); `renderers.PALETTE` re-exports it. `charts.py`,
   `target_marks.py` and `exports.py` read their colours from it (same light values,
   so SVG/PDF/PPTX bytes are unchanged). `renderers.theme_css()` writes `:root`
   tokens, the dark block twice (media query guarded by `:root:not([data-theme=light])`,
   and `:root[data-theme=dark]`), a print block, SVG attribute→token mappings and
   kind-tag classes.

## Validation

Tests first (tests/test_salvage.py), each behaviour with a violating fixture and a
clean decoy: tiny-scale storage vs normal/offset decoys (artifact equality with main's
saved artifacts); validator accepts 1/2 and rejects 3; stdlib chi-square tail at known
values (df=2 exact exp(-x/2), 3.841459/1 → 0.05) and SciPy cross-check; planted vs
null (20 seeds) vs V-gate vs size-gate missingness fixtures; no action from the test;
palette single-source scan (no hex literal outside palette.py in renderer modules),
AA contrast with a violating colour, dark/override CSS present, script-free, bytes.
Two existing expectations change because their accepted semantics change and are
updated with a note: `percentile([1e-12]*9,50)==0` (now 1e-12) and the bad-artifact
mutation `schema_version=2` (now 3). Then full/core suites, fresh-process bytes,
AEC edges/check, screenshots in specs/008-salvage-decisions/review/.
