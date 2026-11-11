# Whole-number histogram bins (spec 028)

**Trade-offs taken**

- *Re-bin rather than relabel.* Rounding the existing real-valued edges would make labels overlap or misstate membership (a 0–1.6 bin holds 0 and 1, but "0 to 2" would claim 2). Bins are rebuilt on whole values instead, so the label is exactly what each bar holds.
- *16-bar default for whole numbers* (Zach, 2026-11-11 17:00 CT: "Closest power of 2 under 32 is usually a reasonable option. Values that are in a tail can have a 'callout' inset"). Read as: cap 16; one bar per value up to 16 values; a sparse tail goes to an inset.
- *What counts as a tail* is this lane's choice, not Zach's: at most 5% of rows outside the best 16-value window. Above that, a callout would hide real mass, so the chart falls back to 16 wider bars. 5% is a proposal; easy to change (`TAIL_SHARE`).
- *Declared `bins:` skips the tail logic*: an explicit declaration is honoured as a plain maximum.
- *2^53 guard.* Beyond it every float is integral, so integrality isn't evidence about the data; those keep real-valued bins.
- *Log view excluded.* Its axis is log10, which is never a whole-number scale.
- *Additive artifact key* (`whole_number_bins`), so existing readers keep working; frozen salvage artifacts compare everything else unchanged.

**Open, for Zach**

1. Approximate display ("about 5" for 4.93): whether, where (hover, tables, prose) and how. Recorded separately; not started.
2. Answered by Zach (16 bars, tail callout); the 5% tail threshold is the open part.
