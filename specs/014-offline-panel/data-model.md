# Data model
Panel artifact: schema_version2, kind panel, source and configuration, rules,
rows (series key, model, window, optional horizon, train/eval bounds, duration,
amplitude, wavelength, frequency, SBC, conditional noise, volumes, thresholds),
periods with state/flags/exposure/known subtotal, views/lineage, comparison,
joined rows, unmatched keys, disagreement, target-profile artifacts, typed findings.
A scalar estimate always has value/null, status and reason/denominator where needed.
Panel artifact load validates all required nested collection and scalar shapes.
CSV flattens estimate values plus adjacent status columns. IDs are strings, keys
are tuples internally and structured JSON arrays externally; no delimiter encoding.

Analytical signal/join CSVs carry estimate values and adjacent statuses. Repeated
reason/formula/model/estimator notes stay in the full panel artifact and report,
not as misleading pseudo-feature columns. Target input follows the same blank-cell
semantics as CSVConnector; its target-analysis payload equals profiling the exported
joined CSV with the declared key overrides and chosen target.
