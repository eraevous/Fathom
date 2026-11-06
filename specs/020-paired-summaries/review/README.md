# Spec020 review — HO-DG-20261106-XZSM

Builder review, provisional; Kate reviews first and Zach decides. Synthetic fixture only.

## Validation

- Full installed test/stats/export suite: **441 passed, 2 skipped**, 1 dependency deprecation warning; [output](tests.txt).
- Pinned Telosmith b0e202fa4b20: **0 errors, 100 inherited warnings**; [check](aec-check.txt), [report-only impact against main e6af6a1](code-impact.txt). Structural evidence does not establish usefulness.
- [Identity evidence](identity.json): all nine generated JSON/HTML/Markdown/PDF/PPTX/CSV files byte-identical on rerun; parent and new schema2 SHA256 `619d3240ebc00895694f601620eefc96d5dad57bda3e595781426f5946ae1dc2`.
- Existing full offline CLI harness passes (including all optional exports); new saved-render orientation and tidy-only subprocesses run under socket denial. Browser contexts offline; no requests; no document overflow. Enter/Space transpose twice restores exact table text and links. [Browser checks](browser-checks.json).
- [Export checks](export-checks.json): actual ReportLab PDFs and actual PowerPoint rendered through LibreOffice Impress, then PyMuPDF rasterized. PDF 35 pages; summary deck 12 slides; full deck 56 slides. The full deck includes all 11 summary panels and all 29 charts; summary omissions are explicitly counted in export status.

## Found, fixed, open

The before screenshots use the same authored table and prior renderer (stack #30); before-summary shows its dataset summary because per-column metric tables did not exist.

- Fixed dense paired prose: source group/rest valid counts and each passing/failing gate are separate bullets. False missing-share gates stay visible. Source finding order and stored messages are unchanged.
- Fixed all-empty string count discovered visually: n is zero nonmissing; top-value share is unavailable. Entropy/length retain their stored raw-string basis (including blanks), disclosed beside tables. No recomputation.
- Fixed missing-font PDF gate arrows: generated connectors say “leads to”. Other unsupported literal glyphs retain the existing explicit replacement warning and exact HTML/JSON source.
- Fixed faint informative marks: axes/box fills use accent_faint rather than decorative grid, opaque scatter replaces insufficient-contrast opacity. Exact supplied palette/kind tokens retained; actual text >=4.5 and informative marks >=3 on panel and surface in both modes. Accent_faint minima 3.218 light/3.413 dark; categorical minima 3.267/7.049. Reserved-hue clearance is disclosed 25-degree HSV heuristic, not perceptual certification.
- No clipping/overlap found in reviewed new tables/finding pages. HTML wide tables intentionally scroll inside their container; fixed pages need zoom at 390px. Configured orientation works without JavaScript; controls are hidden. Export table pagination repeats labels rather than shrinking to fit every metric.
- Left out: transpose for unrelated pre-existing tables; no new dynamic layout, schema3 implementation, stats reconstructed from raw samples, network feature or dependency. Coordinate mean/SD and constant skew stay “Not stored”. Temporal coverage means parsed/nonmissing, never calendar completeness. Cadence is displayed only from declarations/YEAR precision. Existing conservative generic prose splitting can make long technical gates verbose.

## Acceptance table and decoys

`tests/fixtures/summary/mixed.csv` is authored 60x9 with known groups, seven west zeros, one missing amount, all-empty column, constant column, near-unique notes, date gaps, invalid date and latitude 95. Configuration declares target/time/type intent.

| Planted issue | Report found | Missed / narrower reading |
| --- | --- | --- |
| Group contrasts | east mean31 (valid19) vs rest6.3 (40), gap24.7 >= SD12.21; west1.6 (20) vs rest20.74 (39), gap19.14 >= SD12.21 | Middle has no marked contrast; failed missing-share gates preserved, no invented interpretation |
| Missing amount + all-empty column | 1/60 amount missing; empty60/60 missing; complete rows0; summary n59/0 | Cause remains unknown |
| Constant fixed=1 | Explicit constant finding; SD0, distinct1 | Skew unavailable; not manufactured |
| Seven zero amounts | Zero share7/59=11.9% in summary/profile | No new zero-by-category finding/rule introduced |
| Invalid temporal value + date gaps | One invalid; two inferred-cadence coverage gaps; declared daily series has five periods without observations | Invalid/absent date causes unknown; inferred gaps do not assert collection failure |
| Latitude95 | 1/60 fails declared local range | No geolocation/network lookup |
| Near-unique note | Distinct60, top share1/60=1.7%, length16–17 | Meaning remains unknown |

Clean/violating decoys additionally cover no-contrast middle, small groups and multiple categorical contrasts, literal names containing operators, hostile labels/escaping, empty/legacy artifacts, absent optional exporters and CSV null/empty/path collisions. This is builder conformance evidence, not acceptance on unseen tables.

## Nesting and proposals

[Measured nesting](nesting.json), [definitions and every top-key depth](../../../docs/schema-flattening.md). Global maximum12 edges; deepest time_series subtree11 below its top value (median11), columns7/6, findings8/3, target_analysis7/5. Schema3 is a proposal only, with migration/compatibility; tidy CSV is not a lossless schema migration. [CSV contract](../../../docs/tidy-export.md).

## Reproduce

Use pinned pandas2.2.3, test/stats/export extras. `PYTHONPATH=src python specs/020-paired-summaries/review/build.py /tmp/view20-after`; run again with `/tmp/view20-metrics metrics_as_rows`. Parent output was captured separately at `/tmp/view20-before`; `capture.py` reads those artifacts. Chromium context is offline. `export_capture.py` uses actual PDFs and LibreOffice-converted decks at the documented /tmp paths; no mock slides. No external CSS/JS, new dependency or downloaded data.

## Screenshots

| View | 1280px | 390px |
| --- | --- | --- |
| after-finding-dark | [open](after-finding-dark-1280.png) | [open](after-finding-dark-390.png) |
| after-finding-light | [open](after-finding-light-1280.png) | [open](after-finding-light-390.png) |
| after-pdf-finding | [open](after-pdf-finding-1280.png) | [open](after-pdf-finding-390.png) |
| after-pdf-metrics | [open](after-pdf-metrics-1280.png) | [open](after-pdf-metrics-390.png) |
| after-pdf-rows | [open](after-pdf-rows-1280.png) | [open](after-pdf-rows-390.png) |
| after-pptx-full | [open](after-pptx-full-1280.png) | [open](after-pptx-full-390.png) |
| after-pptx-metrics | [open](after-pptx-metrics-1280.png) | [open](after-pptx-metrics-390.png) |
| after-pptx-rows | [open](after-pptx-rows-1280.png) | [open](after-pptx-rows-390.png) |
| after-summary-metrics-dark | [open](after-summary-metrics-dark-1280.png) | [open](after-summary-metrics-dark-390.png) |
| after-summary-metrics-light | [open](after-summary-metrics-light-1280.png) | [open](after-summary-metrics-light-390.png) |
| after-summary-rows-dark | [open](after-summary-rows-dark-1280.png) | [open](after-summary-rows-dark-390.png) |
| after-summary-rows-light | [open](after-summary-rows-light-1280.png) | [open](after-summary-rows-light-390.png) |
| before-finding-dark | [open](before-finding-dark-1280.png) | [open](before-finding-dark-390.png) |
| before-finding-light | [open](before-finding-light-1280.png) | [open](before-finding-light-390.png) |
| before-summary-dark | [open](before-summary-dark-1280.png) | [open](before-summary-dark-390.png) |
| before-summary-light | [open](before-summary-light-1280.png) | [open](before-summary-light-390.png) |
| nojs-columns_as_rows-dark | [open](nojs-columns_as_rows-dark-1280.png) | [open](nojs-columns_as_rows-dark-390.png) |
| nojs-columns_as_rows-light | [open](nojs-columns_as_rows-light-1280.png) | [open](nojs-columns_as_rows-light-390.png) |
| nojs-metrics_as_rows-dark | [open](nojs-metrics_as_rows-dark-1280.png) | [open](nojs-metrics_as_rows-dark-390.png) |
| nojs-metrics_as_rows-light | [open](nojs-metrics_as_rows-light-1280.png) | [open](nojs-metrics_as_rows-light-390.png) |

## PR34 independent-review correction
The historical screenshots above exposed merged relationships and an Adventure group mean presented beside the rest label. They are superseded by the [structured-only corrective review](structured-fix/README.md), with exact public-film regressions and before/after light/dark screenshots. Generic prose splitting has been removed; unstructured findings remain single lines.
