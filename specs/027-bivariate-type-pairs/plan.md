# Plan
Python 3.12+, existing profiler → artifact → renderer flow (CHARTER 1). New module
`src/fathom/type_pairs.py` (stdlib math/statistics only) owns classification and
measures; profiler calls it once per selected pair after `rank_pairs`, so selection
is untouched. `target.py` keeps screening. charts.py gains a `heat_table` SVG; the
grouped box reuses target_marks. finding_view gains a structured tree for the new
rule. Renderers add a short table + chart inside each pair article. tidy needs no
code: relations.csv already flattens every stored pair field.

Constitution gates: one artifact (yes), typed attributed findings (observation only),
inference labelled (roles inherit effective types; binary rule disclosed), question
selects analysis (no new candidates, budget unchanged), artifact is interface
(additive schema 2), tests (violating fixture + decoy per type pair, determinism).
No new dependency. Drift check: this is a new module, but it extends the existing
bivariate responsibility rather than adding a subsystem; no component changes role.

Tests first (tests/test_type_pairs.py): hand formulas, planted pair per type,
null decoys, monotone non-linear, 2×2 zero cell, high-cardinality cap, unchanged
Pearson/ranking, legacy artifact validation, rendering/CSV fields, determinism.
Records: provisional requirement FT-BIV27-R1 before code; claim/evidence after.
