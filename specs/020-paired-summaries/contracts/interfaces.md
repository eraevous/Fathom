# Interfaces
YAML:report: {summary_orientation: columns_as_rows|metrics_as_rows}; omitted=columns_as_rows.
Profile/config validation accepts it but excludes it from analytical result JSON.
Saved render/export --config reads presentation options, never reruns or changes analysis.
`guide export PROFILE --tidy DIR` needs no --out or Office extras. Optional --out retains
existing reports/Office flow; both may be supplied. --formats requires --out.
CSV UTF8, LF, RFC4180 quoting; deterministic fixed metadata fields then sorted flat
paths. Relation rows stay in artifact order; samples retain first/last/random kind.
HTML:button type=button, initially hidden until script enhancement, native keyboard,
aria-pressed indicates orientation; twice transposing restores data/cell links/marks.
No-script default orientation remains readable, controls hidden; print hides controls.
