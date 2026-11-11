# Whole-number histogram bins (spec 028)

**Trade-offs taken**

- *Re-bin rather than relabel.* Rounding the existing real-valued edges would make labels overlap or misstate membership (a 0–1.6 bin holds 0 and 1, but "0 to 2" would claim 2). Bins are rebuilt on whole values instead, so the label is exactly what each bar holds.
- *Bin count stays a maximum under the existing rule.* Width is rounded up, so whole-number charts may show fewer bars than before (never more). Narrower reading than "one bar per value": that would change the disclosed default and is left for Zach.
- *2^53 guard.* Beyond it every float is integral, so integrality isn't evidence about the data; those keep real-valued bins.
- *Log view excluded.* Its axis is log10, which is never a whole-number scale.
- *Additive artifact key* (`whole_number_bins`), so existing readers keep working; frozen salvage artifacts compare everything else unchanged.

**Open, for Zach**

1. Approximate display ("about 5" for 4.93): whether, where (hover, tables, prose) and how. Recorded separately; not started.
2. Should whole-number data with a small range (say ≤ 30 distinct values) always get one bar per value, instead of the √n/10 maximum? The mana example (0–16) currently gets bars two values wide.
