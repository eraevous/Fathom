# FT-R17 repeat: report polish (FT-R18)

HO-20261102-003, codex:aec builder review. Baseline is PR#11 head e82d5e0;
current spec006 uses the same pinned public inputs, default config, sample seed0,
20-row windows and dependency versions. Profile charts gain log/suppression metadata;
raw measurements remain unchanged. This is not claude:aec's independent pass or
Zach/Kate's unseen-table acceptance. No earlier Data Guide implementation was read.

## Heights

Chromium1280x900 /390x900, device scale1, technical/sample/evidence disclosures
closed. “Expanded” opens every column entry, leaving technical disclosures closed.
Document width equals viewport width in every capture; no horizontal page overflow.
[Exact measurements](heights.json) and [capture manifest](manifest.json).

| Table / width | Before | After default | After all columns open |
| --- | ---: | ---: | ---: |
| Films,1280 | 60,186px | 16,861px (72.0% shorter) | 45,082px (25.1% shorter) |
| Films,390 | 65,403px | 17,930px | 47,406px |
| College,1280 | 75,832px | 8,669px (88.6% shorter) | 52,463px |
| College,390 | 76,710px | 9,296px | 56,455px |

The films result reproduces the independent review's approximately61,000px baseline.
Default length falls substantially, but Findings/Relations still occupy many screens;
opening every column remains long. No claim that the complete report fits one screen.

## Screenshot matrix

These are actual browser captures, ReportLab PDF rasterizations, and actual
LibreOffice Impress PPTX conversions rasterized by PyMuPDF. Export screenshots fit
the whole fixed page/slide to the requested width; they are not responsive exports.

| Format | Films1280 before / after | Films390 before / after |
| --- | --- | --- |
| HTML, column | [before](before-movies-column-1280.png) / [after](after-movies-column-1280.png) | [before](before-movies-column-390.png) / [after](after-movies-column-390.png) |
| PDF | [before](before-movies-pdf-1280.png) / [after](after-movies-pdf-1280.png) | [before](before-movies-pdf-390.png) / [after](after-movies-pdf-390.png) |
| PowerPoint | [before](before-movies-pptx-1280.png) / [after](after-movies-pptx-1280.png) | [before](before-movies-pptx-390.png) / [after](after-movies-pptx-390.png) |

Compact headers: [1280](after-movies-headers-1280.png), [390](after-movies-headers-390.png).
Close-quartile HTML box: [1280](after-movies-box-1280.png), [390](after-movies-box-390.png).
Positive log: [1280](after-movies-log-1280.png), [390](after-movies-log-390.png).
PDF box: [1280](after-movies-pdf-box-1280.png), [390](after-movies-pdf-box-390.png).
Optional full-deck box: [1280](after-movies-pptx-full-box-1280.png), [390](after-movies-pptx-full-box-390.png).

College: HTML [1280](after-college-column-1280.png) / [390](after-college-column-390.png),
PDF [1280](after-college-pdf-1280.png) / [390](after-college-pdf-390.png),
PPTX [1280](after-college-pptx-1280.png) / [390](after-college-pptx-390.png).
All-page/slide contact sheets: films [PDF](after-movies-pdf-contact.png) /
[summary deck](after-movies-pptx-contact.png); college [PDF](after-college-pdf-contact.png) /
[summary deck](after-college-pptx-contact.png). Representative full-size views and
contact sheets were inspected; not every pixel/page was inspected at reading size.

## Item dispositions and problems found during this pass

| FT-R18 item | Disposition and evidence |
| --- | --- |
| 1 Length/scaling | Fixed: default-closed compact native column headers; desktop statistics/plot grid, phone stacking, scalable SVG bounded to760px. Global exact-mask table and secondary stats disclosed. Heights above. |
| 2 Intermediate ticks | Fixed: five formatted SVG/PDF positions where range permits; distinct integer count ticks and percent ECDF ticks. Full-deck box shapes also have intermediate tick labels; other native Office charts retain native ticks. |
| 3 Log with zeros | Fixed: Worldwide Gross includes3,147positive values;47zeros explicitly excluded,0negative/invalid. Linear distribution retained. Tests cover negative/zero/constant/no-positive decoys. |
| 4 Box annotations | Fixed: HTML five-number table outside SVG; PDF five separate lines; PPTX summary separated from marks. Median/q3 no longer collide. Numerical geometry retained. |
| 5 Clipped titles | Fixed on reviewed views: horizontal wrapping HTML/PDF captions outside mark area; native PPTX axes fit the slide. Phone HTML contains both full captions. |
| 6 Statistics | Fixed: rows/valid/missing first; min/q1/median/q3/mean/max; spread then zeros/negatives. Compact right-aligned table, large values rounded/grouped, examples146,083 rather than146083.0. Raw precision stays in artifact/evidence. |
| 7 Smaller items | Fixed: capitalized months; identifier/near-unique top-N replaced by repetition reason, other profiles retained. Both public summary decks12slides; films full61slides optional with46charts (summary7, omitted39). College summary7of75charts. |

The first render still had fractional count ticks, a redundant rarity note on numeric
profiles, legacy lower-case month labels, and no ticks on optional full-deck box shapes.
Those were fixed and recaptured. HTML box-summary lines and captions remain readable
at390px. The public films' title top-N is suppressed despite the few repeated titles;
the repeated-title review finding remains available.

Open limitations: PDF53pages for films /80for college remains comprehensive; default
HTML remains long, especially Findings/Relations; fully expanded dictionaries remain
long. PDF/PPTX fit-to390px text requires zoom. Summary chart selection is bounded and
may omit a reader's preferred column; full reports/decks and explicit omission counts
remain available. Native Office axes may still rotate conventionally. Bundled PDF
fonts have limited Unicode coverage (this public run reports0replacements). Arbitrary
unseen fonts/labels/data and independent acceptance remain unverified. No dynamic
layout builder, filtering, target analysis or switchable axes added.

## Comparison with practice and another EDA report

Using the references examined in the [slice-4 review](../../005-plots-and-layout/review/README.md):
[GOV.UK tables](https://design-system.service.gov.uk/components/table/) support the
right-aligned tabular numbers, compact measure/value structure and restrained rules.
[Analysis Function chart guidance](https://analysisfunction.civilservice.gov.uk/policy-store/data-visualisation-charts/)
supports clear full captions, count/percentage units, intermediate formatted ticks,
readable type and uncluttered annotations. Separate box summaries preserve geometry
without squeezing labels onto close quartiles. Count axes no longer imply half-rows.
The [published YData univariate report](https://github.com/Data-Centric-AI-Community/fg-data-profiling/blob/master/docs/_static/img/univariate_profiling.png)
places statistics beside distributions with secondary detail separated: the new grid
uses the same useful proximity, with native disclosure and static CSS rather than
copying tabs/layout machinery. At phone width the HTML stacks; fixed exports' small
fit-to-width type remains a departure from readable mobile typography.

## Reproduce

Public sources/conversion/hashes: [fixtures](../../../tests/fixtures/polish/README.md).
Application never fetches these data. With existing Python3.12 test/stats/exports extras:

```bash
for data in movies college; do
  guide profile tests/fixtures/polish/$data.csv --out reports/polish-after-$data
  guide export reports/polish-after-$data/guide-profile.json --out reports/polish-after-$data
  soffice --headless --convert-to pdf --outdir reports/polish-after-$data/slides reports/polish-after-$data/report.pptx
done
guide export reports/polish-after-movies/guide-profile.json --out reports/polish-full-movies --formats pptx --deck full
soffice --headless --convert-to pdf --outdir reports/polish-full-movies/slides reports/polish-full-movies/report.pptx
python specs/006-report-polish/review/capture.py
```

Baseline directories reports/polish-before-{movies,college} come from running PR#11's
src at e82d5e0 against the exact same input paths, with the same environment. Preserve
those outputs before switching PYTHONPATH to current src. Baseline films PPTX must
also be converted into its slides/report.pdf. Review-only tools: Chromium/Playwright,
LibreOffice25.2.3, PyMuPDF and Pillow; no new application dependency. In this managed
environment LibreOffice uses locally extracted packages, as documented in spec005.
Screenshot bytes depend on font/renderer versions, not runtime analysis randomness.
Fresh processes separately verified identical application HTML/Markdown/PDF/PPTX/
manifest bytes in both deck modes. Screenshot hashes are in image-hashes.json.
