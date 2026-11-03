# Research decisions

Spec Kit plan research used one read-only measure-review agent inside Fathom.
Decision: Pearson/eta/Cramer's V core, scaled arithmetic and explicit unlike-measure
ranking caveat. Why: small descriptive methods, no per-column model or new dependency.
Alternatives: Spearman (useful monotone sensitivity, deferred), mutual information
(binning/units choices), model comparisons (out of scope). Retain legacy Pearson
optional p-values independently of selection.

Decision: pair-local group summaries, count/share/valid/missing denominators and
small-group cautions; no group×all-column sweep. Explicit grouping slot shares
existing budget. Why: serves within-group understanding without Cartesian growth.

Decision: human leakage exclusion, no automatic perfect-correlation rejection.
Why: rank/affine leaks and genuine predictors can be observationally indistinguishable.
Misses disclosed. Thresholds proposed in intent, not accepted by agent.

Decision: static sticky statistics rather than a two-up chart grid. Why: two-up
charts would become narrow beside the statistics; stickiness preserves chart width
and review proximity without a layout builder, reordering controls or script.
