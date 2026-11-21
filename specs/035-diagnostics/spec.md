# Spec 035: diagnostics about the data, for a declared task and model family

**Serves:** P0@2 (understanding before modeling), DG-RA (typed, attributed findings), DG-RB (inference never presented as fact), DG-RC (the question selects the analysis), FT-R7 (byte-identical output).
**Requested by Zach, 2026-11-21:** "… and a diagnostic tests module for common predictive tasks and modeling families." He chose diagnostic framing (fits only as evidence about the data, never shipped as models), optional extras only, and speed first (handoff HO-FTH-20261121-0ETR in relay-kit-private).
**Status:** spec only, provisional. No code in this PR. Spec 033 slice 1 (#67) and spec 034 (#68) are open and waiting for Zach; this spec is written from main rather than stacked on either.
**Records:** `FT-DX35-R1` to `FT-DX35-R5`, written by API Kate (`author_role: independent`, reply `kate-replies:replies/HO-FTH-20261121-0ETR--6a3ca5c12dc3.md`, ask `6a3ca5c12dc3`), committed verbatim in `.aec/records.jsonl`. Her per-family "add / cut / limit" list (same reply) shaped the tables below. The tables, bounds and acceptance are the implementer's reading of her text, not her text.

## What exists today

- A declared `target` gets a linear screen against every other column (`target.py`), with the standing warning that "unmarked leakage cannot be inferred reliably from correlation", and a per-pair `action` asking the reader to review meanings, timing and possible leakage.
- `quality.py` reports duplicated and lockstep columns, missingness that varies with a group, and other bounded quality checks.
- `identifiers.py` documents identifier-like columns; `columns.<name>.role` can declare `identifier` or `quantity`, and `exclude_from_target` removes a column from the screen.
- `time_series` declares time, value and grouping columns and reports the observation process, sparsity and ACF/PACF up to a declared `max_lag`; `panel.py` profiles a declared long panel.

None of this is organised around a predictive task or a model family, and none of it reads a declared train/evaluation partition.

## What this spec adds

A `diagnostics` block in the configuration. Nothing runs unless it is present.

```yaml
target: churned
diagnostics:
  task: classification          # classification | regression | count | forecast
  families: [linear, tree]      # any of: linear, tree, distance, time_series
  features: [tenure, plan, …]   # optional; default below
  split: {column: fold, train: [train], evaluation: [test]}   # optional
  entity: customer_id           # optional
  time: signup_date             # optional; required for forecast and time_series
  exposure: months_active       # optional; count task only
```

**Default feature set.** When `features` is omitted, it is every column except the target and the declared structural roles (`split.column`, `entity`, `time`, `exposure`), minus columns with `exclude_from_target`. It is **not** the target screen's selection: that screen drops near-copies of the target (row agreement ≥ 95%), which W5 exists to find, and it keeps the split column, which would stop W2 matching otherwise identical rows across the split. Structural roles are never part of a duplicate key; W2 and W3 use them only to say which side a row is on.

### The context gate (R1)

Every diagnostic lists the roles it needs. If a role is missing, the diagnostic doesn't run and the report says which role would let it run, as a `question` finding ("Declare `diagnostics.time` to check temporal ordering across the split."). Fathom never infers the task from the target's type, never picks a target, and never guesses a time or entity column.

### The applicability contract (R2)

Each diagnostic is a row in one registry with: id, task(s), family or families, required roles, inputs, computation, threshold (if any), limitations, finding type. Each run of a diagnostic ends in exactly one status:

| Status | Meaning | Shown as |
|---|---|---|
| `signal` | the check ran and found the condition it looks for | `observation` with evidence |
| `no_signal` | the check ran and didn't find it | one line: "checked, not found", with what was checked; never "passed" or "OK" |
| `not_applicable` | the task, family or a role rules it out | listed once, with the reason |
| `insufficient_data` | too few usable rows or levels to compute | listed with the count and the minimum |
| `failed` | the computation raised or went non-finite | listed with the error class; the run continues |

There is no summary score, no "ready" flag and no traffic-light total.

### Data-level only (R3)

Every diagnostic in this spec is computed from the table alone. Checks that need fitted values or residuals (linearity of a fitted relationship, heteroscedasticity, influence, separation in a fitted logistic model) belong to spec 036, where a fit is explicit and its analysis population is recorded. This moves three items that the plan in the handoff listed under 035 ("linearity and heteroscedasticity, outlier influence") to 036; see "Change from the plan" below.

### Warning signals, not certificates (R4)

| # | Diagnostic | Needs | Signal |
|---|---|---|---|
| W1 | Duplicate rows with different targets | target | count of exact feature-duplicate groups whose target differs, with up to 5 example row numbers |
| W2 | Duplicates across the split | split | rows whose features (or whose entity) appear on both sides |
| W3 | Entity crossing the split | split, entity | entities with rows in both train and evaluation; rows per entity (min, median, max) |
| W4 | Temporal order across the split | split, time | evaluation rows dated before the latest train row, with the count and the overlap window |
| W5 | Possible target-derived features | target | a feature that equals the target, is a one-to-one relabelling of it, or has a level (with at least 30 rows) that maps to a single target value; for a numeric target, a feature with \|Spearman\| ≥ 0.98 |

W5 says "possible", names the rule that fired, and is followed by a `question` ("When is this value known relative to the target?"). A run with no signals says which checks ran and adds the fixed sentence "These checks can't show that the data is free of leakage; that needs when each value becomes available." There is no "leakage-free" wording anywhere.

### Task checks

| # | Diagnostic | Task | What it reports |
|---|---|---|---|
| T1 | Class support | classification | share and count of each class; smallest class count; classes under 30 rows named |
| T2 | Class support by split | classification, split | the T1 table per side, and classes missing from one side |
| T3 | Target range and dispersion | count | mean, variance, variance/mean ratio, share of zeros; exposure ≤ 0 or missing counted |
| T4 | Target range by split | regression, count, split | evaluation target values outside the train range (count, share) |
| T5 | Horizon and history | forecast | history length per entity (or overall), the declared horizon against it; gaps and duplicate timestamps from the existing `time_series` evidence |

### Family checks (R5): conditions, not verdicts

Each family gets its own short section. The same table can get cautions in several families; nothing ranks families or says which to use.

| Family | Diagnostic | What it reports | Kate's cut, kept out |
|---|---|---|---|
| linear | L1 design rank and conditioning | over the declared numeric features (at most 12, as spec 034): rank deficiency and condition number of the standardized design, with the columns involved | predictor-normality gates |
| linear | L2 sparse levels | category levels under 30 rows that would become near-empty indicator columns | stepwise selection |
| linear | L3 complete separation in the data | for a classification target: a category level or a single numeric threshold on one feature that splits the classes with no overlap (a data fact; the fitted-model version is 036) | coefficient-significance rankings |
| tree | E1 rare-level support | levels under 30 rows per categorical feature, and their share of rows | normality and scaling requirements |
| tree | E2 identifier-like features | features `identifiers.py` already marks, or with distinct share ≥ 0.9, named as likely to be memorised | impurity importance as relevance |
| tree | E3 missingness against target | features whose missing share differs by class (or whose target mean differs when missing) | training a model to judge suitability |
| tree | E4 evaluation range coverage | split: evaluation values outside the train range or unseen levels, per feature | |
| distance | K1 scale dominance | the share of total variance carried by each numeric feature on its stored scale; features over 50% named | universal dimensionality cutoffs |
| distance | K2 duplicates and zero distances | the share of rows with an exact duplicate in the features | optimal-k claims |
| distance | K3 distance concentration | on a fixed sample of at most 1,000 rows (seed `sample_seed`), the ratio of farthest to nearest neighbour distance, on standardized features | |
| distance | K4 metric compatibility | categorical or identifier features in the feature set, which a numeric metric can't use as declared | |
| time_series | S1 ordering and cadence | duplicate timestamps, gaps, and cadence per entity, reused from `time_series` | random-split validation |
| time_series | S2 split respects time | W4, shown in this section too | exhaustive lag search |
| time_series | S3 bounded lag and season | the existing ACF up to the declared `max_lag`; no lag beyond it | "stationary, therefore ready" verdicts |

Every family section opens with its limit from Kate's list, for example (distance) "Geometry depends on the representation and the metric; these figures describe this table on its stored scale, not the data in general."

### Bounds (CHARTER 4)

- Every per-feature check is linear in the number of declared features.
- The only pairwise feature work is L1 (at most 12 numeric features, as in spec 034) and K3 (a fixed sample of at most 1,000 rows, so at most 499,500 distances).
- No diagnostic searches over subsets, lags beyond `max_lag`, thresholds beyond the fixed ones above, or cluster counts.

### Dependencies

Standard library only. No extra is needed for 035. The thresholds are fixed constants in the registry and printed beside each result.

## Change from the plan

The plan in HO-FTH-20261121-0ETR listed "linearity and heteroscedasticity, outlier influence" and "stationarity" under 035. Following R3, residual-based checks move to spec 036, where a fit is explicit. Following Kate's time-series cut, there is no stationarity test or verdict; S1–S3 report the evidence instead. This is the implementer's reading; if Zach wants a stationarity test back, it is a one-line change to this spec.

## Acceptance (from Kate's records, made concrete)

- **R1:** with `diagnostics` absent, the artifacts are byte-identical to today's. With `task: forecast` and no `time`, the report contains a `question` naming `diagnostics.time` and no time-series check runs. No test fixture produces an inferred task.
- **R2:** a fixture triggers each of the five statuses at least once; `no_signal` and `not_applicable` render differently from each other and from `signal`. A test asserts every registry row has all eight fields.
- **R3:** a grep over the new templates finds no "residual", "heteroscedastic", "influence" or "fitted" wording; those words belong to 036.
- **R4:** planted fixtures fire W1–W5, each with its evidence; a clean fixture fires none and shows the fixed sentence; no template contains "leakage-free", "no leakage" or "safe".
- **R5:** one fixture declared with `families: [linear, tree, distance]` gets a different caution in each section; no template contains "best", "recommended model", "suitable for" or "ready".
- Two runs of every fixture produce byte-identical artifacts.

## Slices

1. Config block, registry, the five statuses, the context gate, W1, W5, T1, T3. About 300 lines.
2. Split and entity: W2, W3, W4, T2, T4, E4.
3. Linear and tree: L1–L3, E1–E3.
4. Distance and time series: K1–K4, S1–S3, T5.

Each slice is one PR from main, ready when CI is green.

## Out of scope

Fitting any model, residuals, influence or fitted separation (spec 036); new relationship measures (spec 034); the 3D view (spec 037); a readiness score or family leaderboard; AutoML, hyperparameter search, deployment advice; definitive leakage detection; automatic target, task, time or entity selection; p-values and significance wording.
