# Visual review (FT-R17) — type-pair views

Reports come from synthetic generators shared with `tests/test_type_pairs.py`:
`python3 build.py OUT && python3 capture.py OUT` (offline Chromium via Playwright; uses
`$CHROME`, `chromium` or `google-chrome`; all Relations disclosures opened; scrollbars shown,
because Playwright's default `--hide-scrollbars` removes the scroll cue). 80 screenshots
(page screenshots clipped to each element): every type-pair article (numeric target: 6;
categorical/binary target: 3; capped 15×13 table: 1) and every target chart the layer
references (scatter for numeric×numeric, grouped box for category×numeric, rates), at 1280
and 390, light and dark. `checks.json`: 12 page states, no network requests, no page
horizontal overflow; `table_overflow` counts type-pair frames that scroll sideways.

## Builder pass

## Found and fixed (first capture → this capture)
1. The "Wording" row held the full wording rule, a ~25-line cell at 1280 and worse at 390.
   The row now says only "near zero" or "headline magnitude X"; the rule is a muted note below.
2. The counts table repeated the heat table's own chart values and carried the cap basis in
   its caption even when nothing was capped. Counts table removed (chart values keep the
   counts); the cap basis appears as a note only when levels were capped.
3. At 390 the per-group table broke numbers mid-value ("11 / 6", "42. / 33") and the wide
   count tables collapsed to one character per line (fixed table layout plus
   overflow-wrap:anywhere). Type-pair tables now use auto layout, normal wrapping and
   unbroken numbers; wide tables scroll inside their own container.
4. Heat-table column labels overlapped at 11 columns; labels now rotate 45° when they do not
   fit, and heat-table text is 15px instead of 13px.
5. Tried and reverted: keeping first-column cells on one line pushed measure values off-screen
   at 390.

## Observed, not changed
- The grouped-box marks (existing shared target-chart code) have small text at 390, the same
  as existing target charts; changing them would alter every target chart.
- At 390 the 7-column per-group table and the 11×11 chart values scroll horizontally inside
  their container; "Level-00" style row labels wrap at the hyphen. Readable, not ideal.
- The chart-values caption wraps narrowly at 1280 because the table is sized to its content.
- PDF/PowerPoint are not covered (T009).

## Reviewer 2 (independent FT-R17 pass on b689989) — findings and disposition
Pre-existing items were checked on main (f600888) by rendering the same synthetic reports
with main's code; they are not changed here so the PR does not widen.

1. Unformatted floats in the plotted five-number table ("42.330000000000005") and Cramér's V
   shown as 0.44 in one table and 0.440 in another. **Fixed (this PR):** the type-pair box chart
   opts into display formatting (`values_format: display`), and type-pair measures and
   messages use the report's `formatted()` everywhere (0.44 in both tables). Test:
   `test_type_pair_views_use_display_formatting`. **Pre-existing:** existing target
   group-box charts on main show the same raw floats in their chart values (unchanged).
2. Tables clipped at 1280 with no scroll cue; a table heading clipped at 390. **Fixed (this
   PR):** type-pair charts and tables may use the article width (the Max column and the 12-column
   counts now fit at 1280); frames that still scroll show a styled scrollbar, the block starts
   with "Wide tables and charts scroll sideways inside their frame." (as the target section
   already says for its tables), and captions stay pinned and wrap inside the frame.
3. Chart text scaled with width (about 4–6 px at 390, about 24 px at 1280). **Fixed (this PR):**
   the heat table is now an HTML table (`heat_table_html`, page text size at every width, a
   solid share bar per cell), and type-pair SVG charts draw at their native 560 px so mark text
   keeps its designed size; on phones the figure scrolls sideways. Test:
   `test_heat_table_is_an_html_table_with_fixed_size_text_and_scroll_cue`.
   **Pre-existing:** target charts (scatter, grouped box, rates) still scale with width on main.
4. Box ticks at min plus equal steps (0.355, 17.7, …) and a caption mentioning log exclusion
   on a linear scale. **Pre-existing** shared target-chart code (`target_marks.axis`,
   `coverage_note`), identical on main; the type-pair box reuses it. Not changed.
5. "Relationship statistics / Groups" table with group labels last under "Value". **Pre-existing**
   generic stored-statistics table (same on main). The type-pair per-group table puts Group first.
6. Scatter and box charts for numeric×numeric and category×numeric were not captured.
   **Fixed:** `*-target-chart-*` screenshots.

Reviewer 2's 4 suite runs at b689989 passed; the builder's single earlier unexplained failure
was not identified (the run printed only a count) and has not recurred.
