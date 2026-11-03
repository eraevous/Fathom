# Intent: plots and layout (HO-20261102-002)

1. One full-width column entry after another, statistics above plots. No new
   responsive breakpoint, rearrangement, filter or chart switch. Existing
   disclosures remain. Phone may pan fixed charts; exports fit fixed pages/slides.
2. Counts comma-grouped; measurements at most3decimals, scientific below0.001 or
   >=1e12; shares1decimal percent. Exact JSON unchanged; human units or unknown.
3. Top10 category coverage and distinct remainder bucket even for literal Other;
   shares state raw/nonmissing/finite denominator. Text length uses raw lexemes.
4. Right-continuous distinct-value ECDF, <=200 deterministic rank knots with
   approximation disclosed. Additional log10 histogram only for all-positive finite
   values and population skew>=2; zero/negative/constant decoys retain linear plots.
5. Date bins: days if span<=60days, months<=5years, years otherwise; include empty
   periods, <=60 shown bins with omitted-middle notice. Existing lag1 unchanged.
6. Exact canonical-null row masks, no pair search; show20 most frequent patterns
   and20 first missing columns, disclose remainder counts/columns and complete rows.
   Global chart in Dictionary; all per-column plots inline.
7. Remove time-only name cues from sketch and partial-parse inference threshold;
   actual parsed dates and human overrides still govern effective type.
8. Display adapter turns saved measurements into tables; arbitrary nested evidence
   remains disclosed. PDF shares tables; PPTX one topic/chart, ECDF numeric XY axes.
9. Compare GOV.UK tables, Analysis Function chart guidance and YData profiling docs;
   no earlier Data Guide code. Screenshots synthetic, not independent acceptance.
10. No new runtime dependency. Review-only Chromium/Playwright/PyMuPDF/pypdf/Pillow
    and actual office renderer justified in plan. claude:aec independent pass pending.
