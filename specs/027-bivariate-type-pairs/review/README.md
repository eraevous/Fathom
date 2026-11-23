# Visual review (FT-R17) — type-pair views

Reports come from synthetic generators shared with `tests/test_type_pairs.py`:
`python3 build.py OUT && python3 capture.py OUT` (offline Chromium via Playwright; uses
`$CHROME`, `chromium` or `google-chrome`; all Relations disclosures opened; scrollbars shown,
because Playwright's default `--hide-scrollbars` removes the scroll cue). 104 screenshots
(page screenshots clipped to each element): every type-pair article (numeric target: 6;
categorical/binary target: 3; capped 15×13 table: 1; edge cases: 3, with a 56-character
numeric target, a monotone pair and a two-complete-case pair) and every target chart the layer
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

## Reviewer 3 (claude:visual-review, review 5837638868 at b689989) — re-checked at 1802bb0
Classification: **fixed by 1802bb0** / **fixed now** (this PR's code, after 1802bb0) / **pre-existing**
(verified on main f600888 with the same synthetic reports).

| # | Finding | Disposition |
| --- | --- | --- |
| 1 | Bare "undefined" for a null headline (Wording row, tree, report.md) | **Fixed now.** `wording.magnitude_status` stores the headline measure's reason (validated); tables and tree say "headline magnitude not estimable (reason)". Test `test_null_headline_shows_its_reason_not_undefined`. |
| 2 | Disagreement note missing from the HTML measure table | **Fixed now.** The line is "rank and linear measures: disagree (see the disagreement rule)". Test `test_disagreement_note_appears_in_measure_table`. |
| 3 | Heat-table text ~9 px phone / ~20 px desktop | **Fixed by 1802bb0** (heat table is an HTML table). |
| 4 | Hidden columns at 390 with no scroll cue | **Fixed by 1802bb0**: visible scrollbar (screenshots show it; Playwright hid scrollbars before) and a "scroll sideways" note. Columns still scroll by design. |
| 5 | Chart-values table capped at 760 px, cramped at 1280 | **Fixed by 1802bb0** for type-pair charts (full article width). **Pre-existing** for target charts (`.chart{max-width:760px}` on main). |
| 6 | Box ticks unrounded, log notes on linear boxes; Q3 40.2 vs 40.195 | Ticks and log notes **pre-existing** (shared target-chart code, same on main). Q3 mismatch **fixed by 1802bb0** (display formatting); guarded by `test_box_chart_values_match_per_group_table` (green before and after). |
| 7 | "Existing target chart" note without a link | **Fixed now.** Target charts get in-page anchors (`target-chart-N`, HTML and Markdown); the type-pair note links to its chart. Test `test_target_chart_reference_links_to_the_chart`. |
| — | Two-complete-case pair read as "binary (-0.009, 0.048)", phi -1 | Rule unchanged (Zach's binary-rule decision; open question in the PR). Level labels are now shown unrounded (`-0.0093456, 0.0481234`). Test `test_binary_level_labels_are_not_rounded`. |
| nit | "Cramers v" vs "Cramer's V" | **Pre-existing**: "Cramers v" is the generic label for the stored `cramers_v` key in the Relationship statistics table. |
| nit | "not estimable : the" | Not a markup defect: HTML is `<strong>not estimable</strong>: the` (no space); text extraction around the bold tag adds it. |
| nit | Alignment differs from Relationship statistics; captions wrap mid-identifier | Type-pair values mix numbers and reasons, so they stay left-aligned; identifier wrapping is the report's global `overflow-wrap:anywhere` (pre-existing). |

Test flake: the builder's one-off failure was the stale showcase (fixed in 1802bb0). Reviewer 3's
suspected candidate, `test_serve.py::test_idle_timeout_and_unauthenticated_requests_do_not_refresh`
(0.6 s timeout, 0.12 s sleeps), is recorded as a note only; it was not observed failing here.

## Reviewer 3 recheck (review 5837820574 at de828de) — disposition
| Item | Disposition |
| --- | --- |
| New 1: type-pair box SVG had `min-width:560px` (a third of the plot visible at 390, scrollbar far below) | **Fixed** (our regression from 1802bb0). The SVG fits the width like the existing target charts (`width:100%; max-width:560px`), so the whole plot shows at 390 and text keeps its native size at 1280. Test `test_type_pair_box_chart_fits_viewport_css`; captures report no SVG past the viewport. |
| New 2: scroll note on every block | **Fixed** (our regression). No block-level note; a note follows each table that can overflow: 5–8 columns shown on screens up to 700 px (CSS only), 9+ columns always. Byte-deterministic, no script. Tests `test_scroll_note_only_beside_wide_tables`; a 2×2 has no note. |
| "see the disagreement rule" not shown or linked | **Fixed.** The rule is a note under the table with an id; the table cell links to it. Test `test_disagreement_rule_is_linked_and_shown`. |
| "not estimable" said twice in the null headline | **Fixed**: "headline magnitude not estimable: <reason>". |
| "index level" row also holding the reference level | **Fixed**: separate index and reference rows. |
| `formatted()` drops trailing zeros (0.681 next to 0.92) | **Left as is.** `formatted()` is the repo's shared display formatter (pre-existing); type-pair tables adopted it in 1802bb0 to match the Relationship statistics table (reviewer 2, item 1). |
| 11-column table still overflowing at 1280 with long names; row header wrapping | Accepted: it scrolls inside its frame and now always carries the note (9+ columns). |
| Left-aligned measure values; captions wrapping mid-identifier at 390 | Unchanged (mixed numbers and reasons; global wrapping rule is pre-existing). |
| Test-design note: the showcase test repairs the file it checks | Recorded for Zach/Kate; test unchanged in this PR (pre-existing test). |
