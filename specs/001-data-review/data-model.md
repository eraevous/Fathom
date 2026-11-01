# Data model

- `SchemaContract`: mode unknown/wide/long, key/context tuples, metric/value/type
  optional column names. Unknown resolves to wide for this slice. Long is rejected
  explicitly. Referenced columns must exist; names and role lists are unique.
- `GuideDataFrame`: pandas DataFrame of raw CSV strings or None, SchemaContract,
  source metadata {connector: csv, origin: supplied path, sha256: raw bytes hash}.
- `ProfilingResult`: one version-1 profile document, including source, context,
  purpose, human working record, schema, overview, columns, findings, selection,
  bivariate results, dependency status and empty annotations dictionary.
- Context: snapshot_date (ISO date or null), source (text or null), transformations
  (ordered {type, description} entries), other_changes (ordered strings).
- Human metadata: row_unit, generating_process and missingness_mechanism are text
  or null. Column metadata is {type?, meaning?}. Type is one of numeric,
  categorical, boolean, temporal, string. Decisions are {decision, rationale}.
- Column entry: name, observed_type, count, missing, distinct, examples (first 3
  distinct), frequencies (top 10 by count descending then value), inference
  {type, confidence, reasons, alternatives}, override, effective_type, meaning,
  statistics. Full strings are retained; no domain fact is inferred.
- Numeric statistics: valid/invalid counts, min/max/mean/median, population std,
  zero and negative counts. Round finite metrics to 10 decimal places. Empty or
  non-finite summaries are null. Temporal: valid/invalid counts, min/max ISO date.
- Finding: id, kind enum, message, generator, evidence, uncertainty, provenance.
  Evidence uses {path, value} measurements or finding IDs. Provenance includes
  source hash and rule version. Stable IDs based on column index/rule, no clock.
- Pair selection: target, budget, selected pairs and all excluded candidates with
  reasons. Pair IDs derive from column order. Complete-case counts are explicit.
- Comparison: version, kind, contexts, context_differences, deltas, limitations,
  annotations. Deltas include rows, columns added/removed, duplicates, missing
  cells and shared-column missing/distinct/effective-type changes.

Validation: reject unknown configuration keys, incorrect nested shapes/types,
unknown columns, empty text where required, booleans used as budgets, malformed
ISO dates and unsupported artifact versions/kinds. Report loading validates the
artifact's required shape before rendering/comparison. No persistent state
transition exists: inputs → immutable-by-convention saved profile → derived view.
