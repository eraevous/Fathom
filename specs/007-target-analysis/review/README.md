# FT-R17 repeat: target analysis and FT-R19

Builder:codex:aec, HO-20261103-001, 2026-11-02CT. Actual offline Chromium HTML,
ReportLab PDF and LibreOffice Impress/PyMuPDF PowerPoint renderings at1280/390px.
Same pinned public fixtures as polish; seed0, sample windows20, budget5; targets
Worldwide Gross/Median declared in target fixture YAML. Baseline3b89d7c is the old
selection/report implementation. No previous Data Guide implementation was read.
This is the builder review; claude:aec's independent pass and owner acceptance remain
separate. Representative full-size views and all-page/slide contact sheets inspected;
not every pixel/page was inspected at reading size.

## FT-R19 dispositions

| Item | Result | Screenshot checks |
| --- | --- | --- |
| 1 Original log ticks | Fixed. HTML/PDF inverse-transform positions to401,20.6K,1.05M,54M,2.77B in original USD-declared values. Native Office ECDF uses raw positives/logBase10 and compact M/B tick formatting. No currency guessed from lexemes. | Log histogram [1280](after-movies-log-1280.png) /[390](after-movies-log-390.png); native log ECDF below |
| 2 Slim box/noY | Fixed. HTML110-unit-high strip; PDF compact strip/summary; optional full-deck shape slimmed. Single-variable box has no Y:Column caption. Grouped boxes retain meaningful category axes. | [1280](after-movies-box-1280.png) /[390](after-movies-box-390.png); PDF [1280](after-movies-pdf-box-1280.png) /[390](after-movies-pdf-box-390.png); PPTX [1280](after-movies-pptx-box-1280.png) /[390](after-movies-pptx-box-390.png) |
| 3 No empty side beside stack | Fixed in HTML. Static desktop sticky stats panel stays at y12 beside final plot; panel585px high in900px viewport and scrolls internally. Phone stacks normally. This is static CSS, not a layout builder. Fixed PDF/slide formats remain sequential. | [sticky statistics](after-movies-sticky-1280.png); [DOM evidence](dom.json) |
| 4 Log ECDF | Fixed. Additional ECDF uses only3147positive Worldwide Gross values, counts47zeros separately, retains linear ECDF. Positive denominator and other exclusions explicit. Native Office log axis confirmed in actual Impress rendering. | HTML [1280](after-movies-log-ecdf-1280.png) /[390](after-movies-log-ecdf-390.png); PDF [1280](after-movies-pdf-log-ecdf-1280.png) /[390](after-movies-pdf-log-ecdf-390.png); PPTX full [1280](after-movies-pptx-log-ecdf-1280.png) /[390](after-movies-pptx-log-ecdf-390.png) |

## Target report screenshot matrix

| Format | Films1280 /390 | College1280 /390 |
| --- | --- | --- |
| HTML ranking | [desktop](after-movies-ranking-1280.png) /[phone](after-movies-ranking-390.png) | [desktop](after-college-ranking-1280.png) /[phone](after-college-ranking-390.png) |
| HTML scatter | [desktop](after-movies-scatter-1280.png) /[phone](after-movies-scatter-390.png) | [desktop](after-college-scatter-1280.png) /[phone](after-college-scatter-390.png) |
| HTML grouped boxes | [desktop](after-movies-group-1280.png) /[phone](after-movies-group-390.png) | [desktop](after-college-group-1280.png) /[phone](after-college-group-390.png) |
| PDF | [desktop](after-movies-pdf-target-1280.png) /[phone](after-movies-pdf-target-390.png) | [desktop](after-college-pdf-target-1280.png) /[phone](after-college-pdf-target-390.png) |
| PowerPoint summary | [desktop](after-movies-pptx-target-1280.png) /[phone](after-movies-pptx-target-390.png) | [desktop](after-college-pptx-target-1280.png) /[phone](after-college-pptx-target-390.png) |

Planted small group: HTML [1280](after-planted-group-1280.png)/[390](after-planted-group-390.png),
actual PPTX [1280](after-planted-pptx-target-1280.png)/[390](after-planted-pptx-target-390.png).
Late categorical-target rates: HTML [1280](after-late-rates-1280.png)/[390](after-late-rates-390.png),
PPTX [1280](after-late-pptx-target-1280.png)/[390](after-late-pptx-target-390.png).
Before Relations: films [1280](before-movies-ranking-1280.png)/[390](before-movies-ranking-390.png).

All-page/slide contact sheets: films [PDF](after-movies-pdf-contact.png)/[PPTX](after-movies-pptx-contact.png),
college [PDF](after-college-pdf-contact.png)/[PPTX](after-college-pptx-contact.png),
planted [PDF](after-planted-pdf-contact.png)/[PPTX](after-planted-pptx-contact.png),
late [PDF](after-late-pdf-contact.png)/[PPTX](after-late-pptx-contact.png).
[Manifest](manifest.json), [image hashes](image-hashes.json), [DOM measurements](dom.json).
Export images fit actual fixed pages/slides to requested widths; these are not
responsive export layouts.

## Problems found and fixed / still open

Fixed on repeat captures: long group labels clipping (bounded labels and separate
counts, full labels retained in tables); PowerPoint theme shadows on target vector marks
(explicit plain styles); long native log ticks (compact original-value number format);
statistics sliding partly out at column end (bounded sticky panel); narrow420px
ranking/group tables (full available width, phone horizontal scrolling); PDF group
statistics breaking inside quantities (one measure per line and weighted widths);
scatter sample omission note incorrectly called ECDF (kind-specific wording);
missing explicit log-scale captions on target axes (now labelled). Optional Pearson p-value assumption text was also restored and regression-checked
after the final compatibility review. Duplicate raw
method tables are disclosed beneath readable target summaries/plots.

Open: full-deck single-chart slides retain their fixed white canvas even for slim boxes; fixed exports need zoom at390px, fine target-plot tick/group text is small on
phones, wide target tables require horizontal scrolling, and long labels are shortened
visibly in plots. Statistics require internal scrolling on desktop. Comprehensive PDF
and fully opened HTML remain long; summary decks stay12slides with omissions shown.
Rate/group plots with many categories may need zoom; no dynamic controls added.
Plots can omit individual points through disclosed deterministic200-point sampling;
log plots omit nonpositive cases visibly. No arbitrary-leak detection, nonlinear
association completeness, population inference or independent acceptance is claimed.

Default DOM heights grow with the new ranking/groups/plots: films1280 before14304px,
after18868px; college after17019px. The earlier slice's no-target height is a different
configuration. Document width remains1280/390 in captures; tables scroll internally.
Counts/pages/plot denominators are measurements, not quality scores.

## Comparison with practice

Using the public references examined in [spec005 review](../../005-plots-and-layout/review/README.md):
[GOV.UK table guidance](https://design-system.service.gov.uk/components/table/)
supports aligned numeric columns and compact formatting; the new ranking is an actual
column/measure/value/n table, not nested key/value blocks. Group statistics were
visually checked for broken numbers and allocated more width after that failed.
[Analysis Function chart guidance](https://analysisfunction.civilservice.gov.uk/policy-store/data-visualisation-charts/)
supports explicit original units, legible ticks, restrained marks and labelled
scales. Flat native shapes remove decoration; separated labels/counts preserve
proximity. Positive-log denominators remain visible rather than implying all rows.
The [published YData univariate report](https://github.com/Data-Centric-AI-Community/fg-data-profiling/blob/master/docs/_static/img/univariate_profiling.png)
keeps statistics near distributions. Static sticky statistics now preserve that
proximity through a long plot stack. Phone/fixed-export typography limits remain
explicit departures, not claimed conformance with every guideline.

## Reproduce

Existing extras plus review-only Playwright/system Chromium, PyMuPDF/Pillow and
LibreOffice25.2.3; no new runtime dependency. Public sources/hashes/conversion in
[polish fixtures](../../../tests/fixtures/polish/sources.json); authored fixtures and
config in [target fixtures](../../../tests/fixtures/target/README.md).

```bash
for data in movies college planted clean late; do
  folder=target
  case "$data" in movies|college) folder=polish;; esac
  guide profile tests/fixtures/$folder/$data.csv --config tests/fixtures/target/$data.yaml --out reports/s7-after-$data
  guide export reports/s7-after-$data/guide-profile.json --out reports/s7-after-$data
  soffice --headless --convert-to pdf --outdir reports/s7-after-$data/slides reports/s7-after-$data/report.pptx
done
guide export reports/s7-after-movies/guide-profile.json --out reports/s7-full-movies --formats pptx --deck full
soffice --headless --convert-to pdf --outdir reports/s7-full-movies/slides reports/s7-full-movies/report.pptx
python specs/007-target-analysis/review/capture.py
```

Before directories use3b89d7c src against the same public paths/config/environment;
preserve before outputs before current profiling. Capture uses browser set_content
with offline mode, not scripts in the report. In this managed environment LibreOffice
uses extracted local packages as documented in spec005. Convert sequentially with
one Office profile. Screenshot bytes depend on renderer/fonts; application byte
repeatability is checked separately in fresh processes. No external data sent by app.
