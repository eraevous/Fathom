# Tidy saved-profile export

Run `guide export guide-profile.json --tidy tidy/`. This reads the saved artifact;
it does not read the original CSV, infer types, run tests or change measurements.
No PDF/PowerPoint dependency is needed. To also write the usual report/Office files:
`guide export guide-profile.json --out exports/ --tidy tidy/`.
`--formats` requires `--out`; optional exporters retain their existing degradation.
Profile artifacts including Liftoff are supported; comparisons and panels keep their
existing output paths. No network is used.

| File | Row unit | Fields |
| --- | --- | --- |
| columns.csv | One column × stored metric/leaf | column, effective_type, metric, value, value_type, unit |
| findings.csv | One finding | collection, id, kind, message, generator, uncertainty, then flat evidence/provenance/metadata fields |
| relations.csv | One stored selected bivariate relation | left, right, method, semantics, generator, uncertainty, then flattened stored fields |
| samples.csv | One stored sample row | sample(first/last/random), position, seed, value.COLUMN fields; absent when samples absent |

Column metrics include count/missing/distinct plus stored statistics, univariate
statistics and special-type checks, not chart geometry or a reconstructed statistic.
Root/univariate paths remain namespaced (for example `statistics.mean`); repeated
stored representations are not silently reconciled. Units accompany the value when
known:declared units for dimensional metrics, counts/proportions/bits/characters/days
for those defined metric kinds, otherwise blank. No domain unit is invented.

Finding rows retain source wording and order. `collection` separates ordinary
findings from Liftoff automatic and conditional-preview findings. Evidence becomes
columns such as `evidence.0.value.statistics.mean`, not a JSON object in one cell.
Relations contain the selected stored pairs; excluded/capped pairs are not recomputed.
Since spec027 a selected relationship may also carry `type_pair.*` fields: the pair
type (for example `type_pair.pair_type`), roles, `type_pair.measures.*` (Spearman rho,
rank-biserial, Kruskal-Wallis H, rank eta-squared, bias-corrected Cramér's V, odds
ratio, risk difference, phi), per-group summaries, the capped contingency counts and
the chart data. Missingness-by-group rows and older artifacts leave these blank.
The matching `type_pair_association` observation appears in findings.csv.
Samples preserve the saved first/last/random roles and any saved truncation; they
are not a full-data export or a new random sample. Repeated positions across sample
roles are intentional. Empty relations/findings still have their fixed headers.

Paths use dot separators. Within a dictionary key:escape `~`→`~0`, `/`→`~1`, `.`→`~2`;
array indices are decimal path segments. Thus `a.b` as one literal key becomes
`a~2b`, distinct from nested `a.b`. Escape tilde first; reverse escapes when reading.
Column/sample names are similarly escaped after the `value.` prefix, so a name
cannot collide with position/sample/seed metadata. Row/metric order follows stored
column order, stable field order and sorted dictionary paths. Dynamic evidence
headers sort after fixed metadata headers. Output is UTF8, LF, stdlib CSV quoting;
commas, quotes and embedded newlines remain values, never evaluated expressions.

Scalars retain raw stored precision (not human-report rounding). Null is a blank
CSV cell; empty string is also blank. Empty containers use `[]`/`{}`. columns.csv's
value_type distinguishes null/boolean/number/string/array/object. Findings/relations/
samples are convenient flat views, not a lossless schema migration:blank null/string
and absent fields may coincide. The authoritative JSON retains their exact types.
This deliberate CSV limit is separate from the proposed schema3 compatibility plan.

## Orientation without changing schema2

Use YAML `report: {summary_orientation: metrics_as_rows}` (or `columns_as_rows`, the
default) with `guide profile --config`. For an existing artifact, use
`guide render PROFILE --config view.yaml --out report/` or
`guide export PROFILE --config view.yaml --out exports/`.
Only report options affect saved rendering/export; analytical declarations in that
file are not applied or rerun. They are syntax-checked. Orientation is not added to
the JSON artifact, so repeat the presentation config for later render/export calls.
The table's Transpose button changes only the current HTML view; it never writes
config/data. With scripts off, the configured orientation stays visible and the
button is hidden. Exports paginate the configured cells; default summary decks
share their existing visual-page budget between tables/charts and disclose omissions.
The full deck includes every panel/chart. No new analytical budget or ranking.
