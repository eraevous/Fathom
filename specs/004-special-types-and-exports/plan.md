# Plan: special types and optional exports

Python3.12, existing pandas/PyYAML and core pytest/SciPy behavior retained.
No new core dependency. Optional `pdf`: reportlab>=4.4,<5 for local PDF layout,
vector charts and bundled Vera font; optional `pptx`: python-pptx>=1.0.2,<2 for
native slide/chart/table serialization. `exports` combines both. Their transitive
font/image/XML/workbook helpers are managed by these packages, not independently
introduced application libraries. Existing installed pypdf/PyMuPDF/Playwright are
local inspection tools only, not project/runtime requirements. Add an exports CI
matrix job; core must run without either serializer.

## Constitution gates

PASS: wrappers/profiler/result/renderers retained; typed evidenced special checks;
inferred syntax not fact; no new relationships; comparisons unchanged; artifact-only
exports; deterministic metadata and test decoys; authored synthetic values only.

## Structure and sequence

Tests first: tests/test_special_types.py, tests/test_exports.py. special.py supplies
name/value recognition, bounded syntax/domain/range stats and findings. models
extends recognized type enum; profiler routes overrides and univariate views remain.
exports.py lazily imports optional serializers, renders saved artifact, normalizes
binary metadata/ZIP members and returns status plus binary payloads. Thin CLI adds
`guide export ARTIFACT --out DIR [--formats pdf pptx]`, also writing core views.

PDF uses a bundled font with explicit unsupported-glyph counts, summarized finding
groups and all sample windows; wide tables split columns. PPTX has one summary,
finding-kind or chart topic per slide, with chart titles/axes from artifact specs.
Fix PDF time/ID and PPTX core/ZIP/nested-XLSX dates; never access network/source CSV.

## Validation/acceptance

Exact special counts, clean decoys, overrides, hostile text, no-network guards,
missing extras, readable PDF/PPTX contents, local PDF inspection, slide/chart counts,
and repeated/fresh-process bytes. Builder planted/clean/late reports include found/
missed/false alarms. No independent acceptance or quality score. Intent note holds
all grammar and export limits. Publish as a second main-targeted stacked PR.
