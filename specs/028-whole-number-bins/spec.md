# 028 — Whole-number histogram bins

Relayed owner feedback, 2026-11-11 (Zach, after inspecting real profiles): "When we have histograms or other charts that allow a hover over, and it's on a numeric that is functionally integer, the hover over items should also be integer. Hovering over how much mana something has and it says 6 to 7.2 something whatever, is... that's not right."

Proposed for Zach. Serves: P0@2, DG-RB@1, DG-RE@1, DG-RF@1, FT-R17@2.

## US1: Whole-number series get whole-number bins (P1)

When every finite value of a linear-scale histogram series is a whole number, and magnitudes keep half-integer bin edges exactly representable (|x| < 2^52; revised from ≤ 2^53 after review, 2026-11-12):

- each bin holds a contiguous run of whole values;
- the label is inclusive (`3`, or `0 to 2`); it is used by the SVG hover title, the chart-values table, Markdown, PDF and PowerPoint categories;
- membership is exact (`(v − min) // width`): no overlap, no gap, counts sum to the series total;
- bar count (owner, 2026-11-11: "Closest power of 2 under 32 is usually a reasonable option. Values that are in a tail can have a 'callout' inset"):
  - a declared `bins:` is a maximum, as before;
  - otherwise the cap is **16 bars**: a range of at most 16 values gets one bar per value;
  - wider ranges where the best 16-value window holds all but a **sparse tail** (≤ 5% of rows) show that window one bar per value; the values outside it go to a **tail callout inset** with its own count scale (up to 6 values per side listed individually, else at most 4 ranges);
  - otherwise up to 16 equal whole-value bars cover the whole range;
- geometry sits on half-integers so each bar is centred on its values; axis ticks are whole numbers at even 1/2/5 × 10^k steps;
- the inset sits in the top corner whose bars it doesn't cover, else in a band below the axis; the chart-values table, Markdown, PDF note and PowerPoint categories carry the tail rows, labelled;
- the chart's `bin_rule` states the whole-number rule; the report-level rule states both;
- the chart carries `whole_number_bins: {width}` (additive, schema 2), and the figure states the layout in one line.

Applies to value histograms and string-length histograms. Never to the log10 view.

## Unchanged

Series with any fractional value keep equal-width real-valued bins and `.5g` labels. Stored values, statistics, percentiles, the box and ECDF views, verdicts and thresholds don't change. Determinism and offline behaviour are kept.

## Out of scope (separate design question)

Approximate display of fractional values ("about 5" for 4.93) is left open by Zach and recorded as issue #44. The log10 view keeps real-valued bins (its ranges are in original units, e.g. "6.96 – 9.19").

## Acceptance

Violating fixture (0–16 whole values, previously `0 to 1.6`) and clean decoys (a genuine 2.5; powers of ten on the log view; magnitudes at or above 2^52). Negative, constant, float-typed whole, boundary and very large values. SVG titles and ticks contain no fractional values for whole-number charts. Salvage decoys reproduce saved artifacts except re-binned whole-number histograms, whose totals must match. Full suite with export extras; byte-identical reruns across hash seeds; screenshots at 1280 and 390 px, light and dark (`review/`).
