# FT-R17 affected-view pass: eight PR15 review fixes

HO-20261103-002, codex:aec,2026-11-03CT. Existing spec007/FT-TA-R1@2 only. Main944f82f
was merged into007-target-analysis first, preserving both parents; no rebase/PR merge.
Tests and this review do not accept requirements or replace independent owner review.

## Regression proof

Final tests/test_review_fixes.py against3367ab3 source: **32failed**. Same file against
fixed source: **32passed**, covering all8threads with valid/clean/legacy decoys.
Full suite **196passed**; core **188passed,8optional skipped**. No earlier test removed. AEC check:0errors/0warnings;2276edges/35files.
Appended FT-TA-C2@1 and FT-TA-E4@1/E5@1 only; old records remain historical.
Required fields fail with ValueError during ProfilingResult.load, before rendering.
Fresh processes produce identical HTML/Markdown/PDF/PPTX/status in summary/full modes.

## Fixed items and test mapping

All test names below are in tests/test_review_fixes.py and begin with `test_`.

| Thread | Fixed behavior | Regression name after test_ |
| --- | --- | --- |
| r4451047766 | Box n counts plotted positives; per-box excl counts nonpositive exclusions; small follows plotted n. Complete summaries untouched; legacy counts explicitly unavailable. | r4451047766_box_counts_and_small_caution |
| r4451047591 | Unrounded normalized geometry quantiles preserve1e-12; statistical percentile still rounds as before. Tiny labels use fewer ticks to avoid collisions. | r4451047591_tiny_positive_geometry_preserves_statistics |
| r4451047741 | Horizontal X is target-category share; vertical Y is predictor group/bin, shared by HTML/Markdown/PDF/PPTX. | r4451047741_rate_axes_match_horizontal_shares |
| r4451047657 | Nullable target required and matches purpose.target; no-target/legacy decoys remain valid. | r4451047657_target_envelope_load_rejection |
| r4451047683 | Typed required summary denominators/missing counts, statistics/contrasts, labels and nested rates validated before renderer use. | r4451047683_group_load_rejection |
| r4451047707 | Required n/total_rows and optional plotted/omission counts validated as nonnegative integers, excluding booleans; optional legacy fields remain optional. | r4451047707_chart_count_load_rejection |
| r4451047624 | Every target kind has a native Chart values disclosure with full labels, exact coordinates/quantiles/counts, and per-bin/category rates. Wide tables scroll; tiny values do not wrap into broken exponents. | r4451047624_accessible_exact_chart_values |
| r4451047641 | Tall target charts paginate into group panels and separate legends at readable text sizes; text-frame bounds do not overlap. Global scales/colors shared. Ordinary decks and summary12-slide cap preserved by budgeting panel slides. | r4451047641_powerpoint_minimum_font_layout |

## Actual screenshot matrix

47images with [manifest](manifest.json) and [hashes](image-hashes.json). Offline
Chromium captures HTML at1280/390px; PDF is actual ReportLab output; PPTX is actual
LibreOffice Impress output rasterized by PyMuPDF. Fixed export pages/slides are fit
to width, not responsive layouts. Representative full-size desktop/phone views and
all five high-cardinality target slides were inspected; not every unrelated page.

| View | HTML1280 /390 | PDF1280 /390 | PowerPoint1280 /390 |
| --- | --- | --- | --- |
| Positive/excluded box counts | [desktop](boxes-html-plot-1280.png)/[phone](boxes-html-plot-390.png) | [desktop](boxes-pdf-panel-1-1280.png)/[phone](boxes-pdf-panel-1-390.png) | [desktop](boxes-pptx-panel-1-1280.png)/[phone](boxes-pptx-panel-1-390.png) |
| Tiny positive geometry | [desktop](tiny-html-plot-1280.png)/[phone](tiny-html-plot-390.png) | [desktop](tiny-pdf-panel-1-1280.png)/[phone](tiny-pdf-panel-1-390.png) | [desktop](tiny-pptx-panel-1-1280.png)/[phone](tiny-pptx-panel-1-390.png) |
| Rate captions | [desktop](rates-html-plot-1280.png)/[phone](rates-html-plot-390.png) | [desktop](rates-pdf-panel-1-1280.png)/[phone](rates-pdf-panel-1-390.png) | [desktop](rates-pptx-panel-1-1280.png)/[phone](rates-pptx-panel-1-390.png) |
| Scatter/coordinate view | [desktop](scatter-html-plot-1280.png)/[phone](scatter-html-plot-390.png) | [desktop](scatter-pdf-panel-1-1280.png)/[phone](scatter-pdf-panel-1-390.png) | [desktop](scatter-pptx-panel-1-1280.png)/[phone](scatter-pptx-panel-1-390.png) |
|20×20rates | [desktop](high-cardinality-html-plot-1280.png)/[phone](high-cardinality-html-plot-390.png) | [desktop](high-cardinality-pdf-panel-1-1280.png)/[phone](high-cardinality-pdf-panel-1-390.png) | [desktop](high-cardinality-pptx-panel-1-1280.png)/[phone](high-cardinality-pptx-panel-1-390.png) |

Accessible disclosures: box [1280](boxes-html-values-1280.png)/[390](boxes-html-values-390.png),
tiny [1280](tiny-html-values-1280.png)/[390](tiny-html-values-390.png),
rates [1280](rates-html-values-1280.png)/[390](rates-html-values-390.png),
scatter [1280](scatter-html-values-1280.png)/[390](scatter-html-values-390.png).
High-cardinality continuations: groups9–16 [1280](high-cardinality-pptx-panel-2-1280.png)/[390](high-cardinality-pptx-panel-2-390.png),
groups17–20 [1280](high-cardinality-pptx-panel-3-1280.png)/[390](high-cardinality-pptx-panel-3-390.png),
legend1–10 [1280](high-cardinality-pptx-panel-4-1280.png)/[390](high-cardinality-pptx-panel-4-390.png),
legend11–20 [1280](high-cardinality-pptx-panel-5-1280.png)/[390](high-cardinality-pptx-panel-5-390.png).
[Whole-deck contact sheet](high-cardinality-pptx-contact.png):12slides, including
3group panels and2legend slides for one selected relationship. Summary now reports
chart-slides separately from unique charts and discloses omissions. Full mode keeps
all selected source charts/panels without the presentation slide budget.

## Findings from this pass / remaining limits

The first tiny-value capture had crowded ticks and a narrow420px eight-column values
table. Fixed through reduced tick density for long numeric labels and full-width
scrollable target-values tables with numeric cells kept intact. PowerPoint high-cardinality
labels/legends no longer overlap, including at the8pt floor. Empty positive groups
remain visible as n0/excl10 with a caution. Exact labels survive plot shortening.

Open limits: exported text still needs zoom at390px, wide data tables require
horizontal scrolling, and many-category HTML/PDF charts remain long/small at fit-to-width.
Legacy boxes cannot recover positive counts from quantiles alone; the report explicitly
marks those counts unavailable until reprofiled. Univariate/statistical10-decimal
rounding remains intentionally unchanged (this repair only separates grouped-box
geometry). Very long/unseen labels and every renderer/font combination are not proven.
No remaining open item among the eight reviewed cases on these fixtures.

The pass follows the same [GOV.UK tables](https://design-system.service.gov.uk/components/table/)
and [Analysis Function chart guidance](https://analysisfunction.civilservice.gov.uk/policy-store/data-visualisation-charts/)
used in earlier review: aligned exact values, labels matched to axes, visible sample
sizes/denominators and enough spacing for type. Native disclosures follow the existing
univariate report pattern; no HTML script or interactive layout builder added.

## Reproduce

Fixtures:[authored synthetic tables](../../../tests/fixtures/target-review/README.md).
With existing extras plus review-only Chromium/Playwright, LibreOffice25.2.3,
PyMuPDF/Pillow (no new dependency):

```bash
for data in boxes tiny rates scatter high-cardinality; do
  guide profile tests/fixtures/target-review/$data.csv --config tests/fixtures/target-review/$data.yaml --out reports/fix8-$data
  guide export reports/fix8-$data/guide-profile.json --out reports/fix8-$data
  soffice --headless --convert-to pdf --outdir reports/fix8-$data/slides reports/fix8-$data/report.pptx
done
python specs/007-target-analysis/review-fixes-gallery/capture.py
```

Before-test proof: unpack only3367ab3's src to a temporary directory outside this
repo's AEC scan, then run the current regression file with pytest's pythonpath
overridden to that directory. All32cases fail; normal current-source run passes.
Screenshot bytes depend on fixed renderer/fonts; application determinism is tested
separately across processes. No archived Data Guide implementation was read.
