# Schema flattening proposal

**Status:proposed for Zach, not implemented.** Schema2 and all profile bytes stay unchanged in spec020.

## Measurement

Canonical authored fixture:60 rows ×9 columns (`tests/fixtures/summary/mixed.csv`, configuration beside it). Artifact SHA256:`619d3240ebc00895694f601620eefc96d5dad57bda3e595781426f5946ae1dc2`. The report dependency environment is fixed in the review. These are empirical depths for this artifact, not bounds for every possible schema2 profile.

Depth is container-edge count below each top-level value; scalar/empty container depth0; arrays count one edge per index. Global depth includes the top-level edge. Median over all terminal leaves.

| Top-level key | Max depth below value | Median depth | Terminals |
| --- | ---: | ---: | ---: |
| `annotations` | 0 | 0 | 1 |
| `bivariate` | 5 | 3 | 78 |
| `columns` | 7 | 6 | 1733 |
| `context` | 1 | 1 | 4 |
| `dataset` | 3 | 3 | 20 |
| `dataset_summary` | 3 | 2 | 32 |
| `dependencies` | 1 | 1 | 1 |
| `findings` | 8 | 3 | 838 |
| `kind` | 0 | 0 | 1 |
| `missingness_patterns` | 4 | 3 | 24 |
| `overview` | 1 | 1 | 4 |
| `purpose` | 1 | 1 | 5 |
| `quality` | 3 | 2 | 58 |
| `report` | 1 | 1 | 4 |
| `row_structure` | 3 | 2 | 30 |
| `samples` | 4 | 4 | 674 |
| `schema` | 1 | 1 | 6 |
| `schema_version` | 0 | 0 | 1 |
| `selection` | 3 | 3 | 62 |
| `source` | 1 | 1 | 3 |
| `target_analysis` | 7 | 5 | 531 |
| `time_series` | 11 | 11 | 904 |
| `working_record` | 1 | 1 | 5 |

Global maximum from root:**12 edges**. Deepest paths (first20, lexicographic; 496 additional ties omitted):

- `/time_series/series/0/groups/0/granularities/0/wavelength/occurrence/dominant_lags/0/acf`
- `/time_series/series/0/groups/0/granularities/0/wavelength/occurrence/dominant_lags/0/family_band`
- `/time_series/series/0/groups/0/granularities/0/wavelength/occurrence/dominant_lags/0/lag`
- `/time_series/series/0/groups/0/granularities/0/wavelength/occurrence/dominant_lags/1/acf`
- `/time_series/series/0/groups/0/granularities/0/wavelength/occurrence/dominant_lags/1/family_band`
- `/time_series/series/0/groups/0/granularities/0/wavelength/occurrence/dominant_lags/1/lag`
- `/time_series/series/0/groups/0/granularities/0/wavelength/occurrence/dominant_lags/2/acf`
- `/time_series/series/0/groups/0/granularities/0/wavelength/occurrence/dominant_lags/2/family_band`
- `/time_series/series/0/groups/0/granularities/0/wavelength/occurrence/dominant_lags/2/lag`
- `/time_series/series/0/groups/0/granularities/0/wavelength/occurrence/lags/0/acf`
- `/time_series/series/0/groups/0/granularities/0/wavelength/occurrence/lags/0/acf_outside_band`
- `/time_series/series/0/groups/0/granularities/0/wavelength/occurrence/lags/0/band`
- `/time_series/series/0/groups/0/granularities/0/wavelength/occurrence/lags/0/estimable`
- `/time_series/series/0/groups/0/granularities/0/wavelength/occurrence/lags/0/family_band`
- `/time_series/series/0/groups/0/granularities/0/wavelength/occurrence/lags/0/lag`
- `/time_series/series/0/groups/0/granularities/0/wavelength/occurrence/lags/0/pacf`
- `/time_series/series/0/groups/0/granularities/0/wavelength/occurrence/lags/0/pairs`
- `/time_series/series/0/groups/0/granularities/0/wavelength/occurrence/lags/0/supported`
- `/time_series/series/0/groups/0/granularities/0/wavelength/occurrence/lags/1/acf`
- `/time_series/series/0/groups/0/granularities/0/wavelength/occurrence/lags/1/acf_outside_band`

The depth comes largely from time-series group/grain/wavelength/signal/lag objects; findings repeat rich evidence, and columns nest statistics and plot metadata. Median depths show that a shallow scalar overview coexists with deep analytic evidence. Reproduce with the review build and `fathom.tidy.nesting_metrics`; [machine measurement](../specs/020-paired-summaries/review/nesting.json).

## Proposed schema3 shape

Keep source/context/purpose and typed findings, but normalize shared measurements into named records:

```json
{"schema_version":3,"columns":{"amount":{"effective_type":"numeric","stats":{"mean":{"value":14.25,"unit":"credits","basis":"measured"},"missing_share":{"value":0.0166666667,"unit":"proportion","basis":"measured"}}}},"findings":[{"id":"example","kind":"observation","message":"Saved wording","evidence":{"group.mean":{"value":31,"unit":"credits","basis":"measured"},"rest.mean":{"value":6.3,"unit":"credits","basis":"measured"}}}],"series":{},"samples":{}}
```

Illustrative values only; this is not a committed schema, implementation or new statistical computation. Columns are keyed by exact name with a separate ordered column-name array for stable display. Stats maps are flat metric names; each atom holds value/unit/status/basis/method/source reference as appropriate. Missing unit is null, never a guessed domain meaning. Count/proportion/physical units stay distinct; declared/inferred/measured remain explicit.

Findings retain stable IDs, kind, generator, uncertainty and provenance; their evidence is a flat key/value map or references to canonical measurement atoms, instead of copied nested profiles. Preserve every gate and eligibility state, including failed, unavailable and unsupported. Paths/names need an escaping contract; map-key and schema evolution rules need owner acceptance.

Series and group/window/grain results become keyed entities with flat metric maps and separate ordered lag/period tables. Charts reference those measurements rather than embed another data copy. Samples remain separate rows keyed by column name, with source position, sample role, seed and truncation metadata. Relations similarly reference named columns, methods and measurement atoms. A presentation adapter joins these records for existing report views; storage normalization must not select analyses or erase source context.

## Migration and compatibility plan

1. Zach reviews the proposed atoms, ordering, naming/escaping, units and reference semantics; freeze a schema3 contract and independent fixtures before code.
2. Keep schema1/2 loaders/read-only artifacts supported. Add an explicit copy-only `upgrade` operation, never rewrite historical files in place. Preserve original schema/hash and source values, and mark irrecoverable units/semantics unknown. Conversion must not recompute metrics or re-evaluate gates.
3. Translate versions into a shared renderer view model; retain source-order arrays and stable finding/column IDs. Unknown extension fields require a preserved extension area or a clear conversion refusal, not silent deletion.
4. Prove JSON-level value/type/units/finding lineage preservation, fresh/loaded equivalence, legacy rendering, deterministic output and optional-dependency degradation. Round-trip reversible fixtures and enumerate information a downgrade cannot represent.
5. Publish migration tooling and version negotiation only after acceptance; keep schema2 export available during a documented compatibility window. Do not claim a lossless downgrade when normalization drops copies or stores references; require explicit limitations.

## Left open

Exact metric vocabulary, reference IDs, chart-storage boundary, unknown extensions, units/basis atoms, long-versus-wide evidence tables and the support window need Zach’s decision. CSV export in spec020 is a derived convenience and does not implement any of these changes. No final schema3 JSON validator, adapter, migration command or new measurement ships in this PR.

## Note: spec027 `type_pair` blocks

The additive `bivariate[i].type_pair` block (spec027) is validated as a closed shape: unknown keys
inside it are rejected on load, and a nested addition needs the producer, the allowlist, the
validator and the tests updated together. This is a validation rule for that block only; it does
not decide schema 2 versus schema 3, which remains Zach's decision.
