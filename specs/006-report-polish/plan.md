# Plan: Report polish

Python3.12 and existing pandas/PyYAML, optional SciPy/ReportLab/python-pptx. No new
runtime dependency. Review-only existing Playwright/Chromium, PyMuPDF/pypdf/Pillow
and locally installed LibreOffice Impress as in spec005; no new rendering service.

## Constitution gates

PASS before/after design: one wrapper→profiler→artifact→renderer flow; labelled
inference, typed/evidenced findings, bounded existing pairs, contextual comparisons,
raw artifact authority, deterministic tests/decoys/optional absence, public/synthetic
fixtures. FT-R18 supersedes builder display choices, not protected charter text.

## Sequence / structure

Tests first tests/test_polish.py. presentation.py: logical metric ordering,
magnitude/units-aware formatted examples and compact tables. univariate.py:
positive-only log coverage metadata, capitalized calendar labels and role/uniqueness
bar suppression. charts.py: scalable plot composition, intermediate tick helper,
separate nonoverlapping box summary and horizontal wrapping axis captions.
renderers.py: default-closed compact native column headers, static CSS grid with
phone stacking and intrinsic chart width. exports.py: PDF ticks/horizontal titles,
box labels and deterministic summary chart/topic selection, full mode. cli.py:
`guide export --deck summary|full` (summary default). Artifact measurements remain
unchanged except additive log coverage/suppression metadata/chart specs.

## Validation / review

Hand-computed skew+zero/negative/constant, ordering/rounding/example/ID/uniqueness
fixtures, summary budget/scope/byte/core tests. Pin public Vega movies and
FiveThirtyEight college CSVs; record URLs/hashes/conversion. Before/after profile
same inputs/default config, seed0, sample20, identical dependencies. Measure1280
height default/all columns expanded. Actual screenshots at1280/390 for HTML/PDF
and office-rendered PPTX; inspect long labels, close quartiles, log counts, native
summary/full decks. Compare public chart/table guidance already used in spec005;
record any residual issue. Builder synthetic/clean acceptance, no independent claim.
AEC purpose/check/impact and protected-prefix verification. User explicitly permits
local decision-branch integration; do not merge PRs or push/force main.
