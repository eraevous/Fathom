# 028 — Whole-number histogram bins

Relayed owner feedback, 2026-11-11 (Zach, after inspecting real profiles): "When we have histograms or other charts that allow a hover over, and it's on a numeric that is functionally integer, the hover over items should also be integer. Hovering over how much mana something has and it says 6 to 7.2 something whatever, is... that's not right."

Proposed for Zach. Serves: P0@2, DG-RB@1, DG-RE@1, DG-RF@1, FT-R17@2.

## US1: Whole-number series get whole-number bins (P1)

When every finite value of a linear-scale histogram series is a whole number, and magnitudes are within the exactly representable float range (|x| ≤ 2^53):

- each bin holds a contiguous run of whole values;
- the label is inclusive (`3`, or `0 to 2`); it is used by the SVG hover title, the chart-values table, Markdown, PDF and PowerPoint categories;
- membership is exact (`(v − min) // width`): no overlap, no gap, counts sum to the series total;
- the bin count follows the existing rule (declared `bins:` or √n capped at 10) as a maximum. The width is the smallest whole number that keeps the count at or below it, so short ranges give one bar per value;
- geometry sits on half-integers so each bar is centred on its values; axis ticks are whole numbers;
- the chart carries `whole_number_bins: {width}` (additive, schema 2), and the figure states the layout in one line.

Applies to value histograms and string-length histograms. Never to the log10 view.

## Unchanged

Series with any fractional value keep equal-width real-valued bins and `.5g` labels. Stored values, statistics, percentiles, the box and ECDF views, verdicts and thresholds don't change. Determinism and offline behaviour are kept.

## Out of scope (separate design question)

Approximate display of fractional values ("about 5" for 4.93) is left open by Zach and recorded as a separate issue. Changing the √n/10 default bin count for whole-number data is a possible follow-up, not done here.

## Acceptance

Violating fixture (0–16 whole values, previously `0 to 1.6`) and clean decoys (a genuine 2.5; powers of ten on the log view; magnitudes above 2^53). Negative, constant, float-typed whole, boundary and very large values. SVG titles and ticks contain no fractional values for whole-number charts. Salvage decoys reproduce saved artifacts except re-binned whole-number histograms, whose totals must match. Full suite with export extras; byte-identical reruns across hash seeds; screenshots at 1280 and 390 px, light and dark (`review/`).
