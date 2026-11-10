# Visual review (FT-R17) — type-pair views

Builder's own pass, not the independent one. Reports come from synthetic generators shared
with `tests/test_type_pairs.py`: `python3 build.py OUT && python3 capture.py OUT` (offline
Chromium via Playwright; uses `$CHROME`, `chromium` or `google-chrome`; all Relations
disclosures opened). 40 element screenshots: every type-pair article (numeric target: 6;
categorical/binary target: 3; capped 15×13 table: 1) at 1280 and 390, light and dark.
`checks.json`: 12 page states, no network requests, no page horizontal overflow, no SVG
past the viewport.

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
