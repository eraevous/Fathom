# Builder visual review — FT-R17

HO-20261102-002, codex:aec. Actual Chromium HTML, ReportLab PDF, and
LibreOffice Impress-rendered PPTX were inspected. Phone width is390px; desktop
1280px. Before is cc74ff0, after spec005. All inputs are authored synthetic data.
This is the builder pass; claude:aec's independent review remains pending.

## Screenshot matrix

| Format | Desktop before / after | Phone before / after |
| --- | --- | --- |
| HTML | [before](before-html-1280.png) / [after](after-html-1280.png) | [before](before-html-390.png) / [after](after-html-390.png) |
| PDF | [before](before-pdf-1280.png) / [after](after-pdf-1280.png) | [before](before-pdf-390.png) / [after](after-pdf-390.png) |
| PowerPoint | [before](before-pptx-1280.png) / [after](after-pptx-1280.png) | [before](before-pptx-390.png) / [after](after-pptx-390.png) |

Additional desktop/phone HTML captures: [categories](after-category-1280.png) /
[phone](after-category-390.png), [ECDF/log](after-ecdf-1280.png) /
[phone](after-ecdf-390.png), [calendar](after-calendar-1280.png) /
[phone](after-calendar-390.png), [missingness](after-missingness-1280.png) /
[phone](after-missingness-390.png). Export details: [native XY ECDF](after-pptx-ecdf-1280.png),
[long slide labels](after-pptx-long-label-1280.png), [PDF box/ECDF](after-pdf-box-1280.png).
[PDF contact sheet](after-pdf-contact.png) and [PPTX contact sheet](after-pptx-contact.png)
cover every exported page/slide. Representative full-size views were inspected
alongside contact sheets; this is not a claim of exhaustive pixel-level inspection.

## Concrete problems and dispositions

| ID | Observed problem | Fix / open disposition |
| --- | --- | --- |
| V01 | Old evidence occupied a narrow right-hand table cell; large unused left area | Fixed: full-width column entries, overview above inline plots |
| V02 | Ungrouped million-scale measures and excessive decimals | Fixed: comma counts, bounded measurement precision, percent shares, human units/unknown |
| V03 | Frequency/count values were stacked nested blocks | Fixed: aligned value/count/share tables with explicit denominators; lexical value labels stay exact |
| V04 | Bar labels distant from bars, counts floating at fixed far edge | Fixed:10px label/bar gap and end-relative counts, wrapping long labels |
| V05 | 'Running Time min', Full_time, Part_time described as dates | Fixed: removed time-only sketch/partial-parse cues; actual parsed dates/human declarations retained |
| V06 | Plots hidden with raw evidence | Fixed: all column plots inline; raw evidence separate and closed |
| V07 | Skewed box quartile labels overlapped | Fixed: separate five-number summary row/text, preserving numerical geometry |
| V08 | PDF put every chart on a sparse standalone page after relations | Fixed: column-local vector charts flow with formatted tables |
| V09 | First review found PDF headings orphaned from chart | Fixed: keep chart and heading together |
| V10 | Slide title and native chart title duplicated/crowded | Fixed: one24pt slide title, consistent plot frame and smaller ticks |
| V11 | Long slide categories overflowed off left side | Fixed: explicit ellipsis, original labels in slide notes/artifact; PDF shortening also disclosed |
| V12 | First review's long tables delayed plots | Fixed: HTML plots follow overview, other statistics follow plots or human-table disclosure |
| V13 | Fixed-width charts clip at phone viewport edge | Open by static-layout reading: chart-region panning with visible instruction; phone table labels can wrap aggressively; exact-value disclosure remains usable. No new responsive reflow under DG-D7 |
| V14 | Fixed PDF/PPTX fit-to390px text is too small | Open: zoom required; no mobile export redesign authorized |
| V15 | Rotated y-axis titles, few intermediate SVG/PDF ticks | Open: labelled and exact tables available, but less readable than horizontal titles/richer ticks recommended by guidance |
| V16 | Many plots make a long report (31 PDF pages /48 slides here) | Open: static comprehensive output, no dynamic filtering/rearrangement; accepted section order retains summary after dictionary |
| V17 | PDF's bundled font has limited Unicode coverage | Existing open limit, disclosed replacement count; exact text in core artifact/views |

## Comparison with practice and another profiling report

[GOV.UK table guidance](https://design-system.service.gov.uk/components/table/)
recommends right-aligned numeric columns. Fathom now uses that alignment, tabular
figures, labelled tables, stable units and restrained rules/spacing; raw category
lexemes remain unchanged rather than being silently reformatted as quantities.

[Analysis Function chart guidance](https://analysisfunction.civilservice.gov.uk/policy-store/data-visualisation-charts/)
was compared for clear labels, readable type, thousands grouping and simple marks.
Fathom's bar ends were visually checked, not assumed successful. Supplemental
exact-value tables support the plots. Rotated titles, sparse ticks and phone-scale
limitations remain explicit departures, not claimed conformance with every guideline.

[YData profiling documentation](https://docs.sdk.ydata.ai/latest/getting_started/profiling/)
and its [published univariate screenshot](https://github.com/Data-Centric-AI-Community/fg-data-profiling/blob/master/docs/_static/img/univariate_profiling.png)
were read/viewed. The reference places a named/type-labelled variable, ruled
statistics and distribution chart close together, with secondary details separated.
Fathom follows that proximity/hierarchy with full-width static entries and overview
above plots; it does not copy the reference's interactive tabs or side-by-side
composition. No earlier Data Guide implementation was read. External reference
images were inspected locally and linked, not copied into this repository.

## Reproduce

Use Python3.12 with existing test/stats/exports extras. Review-only tools used:
Playwright with system Chromium, PyMuPDF/pypdf, Pillow, LibreOffice25.2.3. No new
application dependency. Export serializer versions are in export-status.json.

1. Profile layout/planted.csv with layout/review.yaml into reports/layout-after;
   export that saved JSON there. Baseline uses the same fixture/config with cc74ff0
   code, into reports/layout-before. Both use seed23 and3sample rows/view.
2. Run actual LibreOffice Impress headless conversion of each report.pptx into its
   slides/report.pdf: `soffice --headless --convert-to pdf --outdir DIR/slides DIR/report.pptx`.
   In this environment distro packages were downloaded/extracted locally because
   no root install exists; package symlinks/bootstrap paths were relocated and the
   program directory precedes its dependency directory in LD_LIBRARY_PATH.
3. Run `python specs/005-plots-and-layout/review/capture.py before` and `after` from
   repository root. Browser uses set_content because local-file navigation is
   restricted here. Manifests record actual dimensions/page numbers; exports are
   fixed-page rasterizations fitted to the requested widths, not responsive layouts.
4. Inspect full-size images and contact sheets; verify no page-level HTML overflow
   and that column SVGs have no closed-disclosure ancestor. Chart regions can pan.

Screenshot bytes depend on renderer/font versions; application output repeatability
is tested separately. Browser/office export rendering does not feed application
analysis or alter saved data.
