# Spec 036: clustering and basic regression, as evidence about the data

**Serves:** P0@2 (understanding before modeling), DG-RA (typed, attributed findings), DG-RB (inference never presented as fact), DG-RC (the question selects the analysis), FT-R7 (byte-identical output), CHARTER rule 4 (no all-pairs or exhaustive searches) and rule 7 (degrade without extras).
**Requested by Zach, 2026-11-21:** "… clustering, some basic regression, …". He chose diagnostic framing (fits only as evidence about the data, never shipped as models), optional extras only, and speed first (handoff HO-FTH-20261121-0ETR in relay-kit-private).
**Status:** spec only, provisional. No code in this PR. Spec 033 slice 1 (#67), spec 034 (#68) and spec 035 (#69) are open and waiting for Zach; this spec is written from main rather than stacked on any of them.
**Records:** `FT-ST36-R1` to `FT-ST36-R6`, written by API Kate (`author_role: independent`, reply `kate-replies:replies/HO-FTH-20261121-0ETR--6a3ca5c12dc3.md`, ask `6a3ca5c12dc3`), committed verbatim in `.aec/records.jsonl`. Her linear/GLM and distance-based "add / cut / limit" lists (same reply) shaped the tables below. The tables, bounds and acceptance are the implementer's reading of her text, not her text.

## What exists today

Nothing in Fathom fits a model. Spec 034 (proposed) adds partial correlation, VIF and principal components inside declared column sets; spec 035 (proposed) adds data-level diagnostics for a declared task and family and, by its R3, leaves every check that needs fitted values or residuals to this spec.

## What this spec adds

A `fits` block in the configuration. Nothing is fitted unless it is present (R1). Ordinary profiling, with or without a target, fits nothing.

```yaml
fits:
  regression:
    - name: tenure_model
      target: churned            # must be declared here, even if `target` is set
      method: logistic           # ols | logistic
      features: [tenure, plan, monthly_charges]
  clustering:
    - name: usage_groups
      method: kmeans             # kmeans | hierarchical
      features: [calls, data_gb, sms]
      k: [3, 4]                  # one to three declared values; no search
  sensitivity: {resamples: 10}   # 0 turns it off; at most 20
```

Every fit names its target or feature set, its method and its configuration. There is no default target, no default feature set, no automatic choice between OLS and logistic, and no "try every method" mode.

### Preprocessing is recorded, not silent (R2)

| Step | Rule | Recorded in the finding |
|---|---|---|
| Missing values | complete cases only on the fit's columns; no imputation | rows used, rows dropped, and the count dropped per column |
| Identifiers | a column `identifiers.py` marks, or declared `role: identifier`, is refused with a reason | the refused columns |
| Categorical features (regression) | one indicator per level, reference level = the most frequent (ties broken by sorted name); more than 10 levels is refused with a reason | levels, reference level, refused columns |
| Categorical features (clustering) | refused with a reason (a numeric distance can't use them as declared; spec 035 K4) | the refused columns |
| Numeric scaling | clustering: z-scores on the analysis population; regression: stored units, with standardized coefficients shown beside them | means and standard deviations used |
| Rows | at most 200,000 rows per fit; above that, a fixed sample (seed `sample_seed`) | the sampling policy and the sample size |

### Regression evidence (R3)

For each declared regression the report shows, as `observation` findings:

| # | What | Wording rule |
|---|---|---|
| G1 | **In-sample fit:** OLS R² and adjusted R²; logistic deviance, null deviance and McFadden's pseudo-R² | always prefixed "in-sample"; never "accuracy", "predictive" or "performance" |
| G2 | **Coefficients:** estimate in stored units, standardized estimate, conventional standard error | a fixed sentence: "Standard errors assume the model is correctly specified and the features were chosen before looking at the data." No p-values, no stars, no "significant" |
| G3 | **Linearity of the fitted relationship** (moved from 035): mean residual by decile of fitted value, and per numeric feature by decile of that feature | the largest decile mean in residual standard deviations, with its decile |
| G4 | **Residual spread** (moved from 035, OLS): residual standard deviation by decile of fitted value; the ratio of largest to smallest | the ratio, and the deciles it compares |
| G5 | **Influence** (moved from 035): leverage and Cook's distance; the five most influential rows by row number; the count over 4/n | "influential in this fit", never "outlier" or "error" |
| G6 | **Fitted separation** (logistic, moved from 035), two separate signals: **G6a non-convergence**, taken only from the solver's own result (IRLS hit its 50-iteration cap without meeting its tolerance, or the coefficient norm was still growing at the cap); **G6b extreme fitted probabilities**, the count of rows with fitted probability within 1e-6 of 0 or 1 | G6a: "the fit did not converge to finite coefficients", naming the features whose coefficients were still growing. G6b: "n rows have fitted probabilities within 1e-6 of 0 or 1", with no convergence wording; a converged fit can have such rows |
| G7 | **Collinearity in the design:** rank deficiency and condition number of the design actually fitted | dropped aliased columns are named |

Each regression section ends with the fixed limits sentence: "This fit describes these rows under this specification. It doesn't show that the relationship is causal, stable in other data, or useful for prediction." No `action` finding recommends a feature, a model or a transformation; a G3–G6 signal may add a `question` ("Is the relationship with tenure expected to bend?").

Kate's cuts, kept out: predictor-normality gates, stepwise selection, coefficient-significance rankings.

### Clustering evidence (R4)

For each declared clustering and each declared `k`:

| # | What |
|---|---|
| C1 | **What was fitted:** algorithm (k-means with k-means++ start, 4 starts, at most 100 iterations; or Ward hierarchical on a fixed sample of at most 1,000 rows), Euclidean distance on z-scores, the features, `k`, the seed |
| C2 | **Sizes:** rows per cluster, and the share of rows; k-means assigns every row, so "unassigned" is 0 and says so; hierarchical lists rows outside the sample as "not clustered" |
| C3 | **Profiles:** each cluster's mean and median per feature, in stored units and in z-scores |
| C4 | **Internal measures:** silhouette (on a fixed sample of at most 1,000 rows) and within-cluster share of variance |
| C5 | **Scale dependence:** the same fit on stored (unscaled) features, and the agreement (adjusted Rand index) between the two labellings; low agreement is reported as "these groups depend on the scaling" |

When more than one `k` is declared, each is reported in declaration order. Nothing picks "the best k", and no elbow or gap search runs.

Wording: clusters are "groups this algorithm formed on these features", never "segments", "types" or "natural groups". A fixed sentence follows C4: "A silhouette describes how separated these groups are under this distance; it doesn't show that the groups exist in the population." Cluster labels may colour the 3D view (spec 037). This spec writes them to no data export, and they are never used as a target or fed into another fit in the same run.

### Sensitivity, bounded (R5)

With `sensitivity.resamples: B` (default 10, at most 20, 0 off), each fit is repeated on B bootstrap resamples of its analysis population (seed `sample_seed`).

- Regression: the range of each coefficient across resamples, and how many resamples kept its sign. Every resample reuses the full fit's design: the same category levels, the same reference level, and the full fit's centring and scaling; preprocessing is never re-derived per resample, so each coefficient keeps the same contrast in every resample. A resample in which a level (or the reference level) has no rows can't estimate that contrast: it is left out of that coefficient's range and sign count, and the finding says how many resamples were left out and why.
- Clustering: the mean adjusted Rand index between the full fit and each resample's fit on the shared rows.

Robustness language follows fixed rules and appears only when sensitivity ran: a coefficient keeps its sign in every resample → "its sign held across B resamples"; a clustering with mean ARI ≥ 0.8 → "the grouping was similar across B resamples"; below that → "the grouping changed across resamples" and no stability wording. With `resamples: 0` no stability sentence appears at all. Nothing searches over `k`, feature subsets or specifications (Kate's cut).

### Execution, budgets and extras (R6)

- **Engine:** numpy only, which pandas already installs. OLS by QR, logistic by iteratively reweighted least squares (at most 50 iterations), k-means and Ward written in numpy. No new dependency is needed for this spec. The `[model]` extra (scikit-learn, statsmodels) in the handoff's plan is **not** added: nothing here needs it, and a second engine would be the "silent algorithm substitution" R6 rules out. (Zach confirmed this reading on 2026-11-23: reading 7, "Correct"; DEC-264 in relay-kit-private.)
- **Budgets:** at most 4 regressions and 4 clusterings per run; at most 12 features per fit (as spec 034); at most 3 values of `k`, each at most 12; at most 20 resamples. A fit over budget is refused with the budget named, as an `insufficient_data`-style status from spec 035's registry (`over_budget`), and the run continues.
- **Determinism:** fixed seeds, fixed iteration caps, fixed tie-breaks; numbers written to 6 significant digits so that floating-point differences in the last bits don't change the artifact. Byte-identical output is claimed for the CI lock (`requirements/ci-lock.txt`) only, not across numpy or BLAS versions.
- **Failures:** a singular design, a non-converged fit or a numpy error ends that fit with status `failed` and the error class; the run continues.

## Bounds (CHARTER 4)

- Fit count, features, `k`, resamples and rows are all bounded by the configuration before data is read (above).
- The only quadratic work is the silhouette and Ward's distance matrix, each on a fixed sample of at most 1,000 rows.
- No search over `k`, features, interactions, transformations or methods.

## Acceptance (from Kate's records, made concrete)

- **R1:** with `fits` absent, artifacts are byte-identical to today's; a test asserts no fit function runs during ordinary profiling, with or without a target.
- **R2:** a mixed-type fixture with missing values and an identifier column reports rows used and dropped per column, the reference level of each category, the refused identifier, and z-score parameters; rebuilding the design from the recorded configuration gives the same row count and columns.
- **R3:** a collinear fixture names the aliased column (G7); a fixture with a curved relationship fires G3 and gets a `question`, not an `action`; a grep over the new templates finds no "significant", "accuracy", "predictive performance", "causes" or "effect of".
- **R3, G6:** a fixture with complete separation fires G6a. A decoy that converges (four rows at x = −1 with one positive, four at x = 1 with three positive, plus correctly classified rows at x = ±100; the fit converges to intercept 0, slope ln 3) fires G6b only and contains no non-convergence wording.
- **R4:** an anisotropic fixture (one feature on a much larger scale) fires C5's scale-dependence sentence; a single Gaussian cloud clustered with `k: [3]` reports its groups without "segments", "natural" or "real" anywhere in the output.
- **R5, fixed contrasts:** a fixture with six A rows (outcome 0) and four B rows (outcome 1) keeps "B versus A" in every resample, including ones where B is the more frequent level, and its sign holds in every resample that has both levels; a resample with no B rows is counted as left out, not as a sign change.
- **R5:** an unstable fixture (two overlapping clouds) gets "the grouping changed across resamples"; the same run with `resamples: 0` has no stability sentence.
- **R6:** a fit over budget is reported `over_budget` and the run continues; a singular design is `failed` with its error class; two runs of every fixture under the CI lock produce byte-identical artifacts.

## Slices

1. Config block, preprocessing record, OLS with G1, G2, G7, and the fixed limits sentence. About 300 lines.
2. Residual and influence evidence: G3–G5.
3. Logistic regression with G6.
4. k-means with C1–C5.
5. Ward hierarchical, and sensitivity (R5) for both kinds of fit.

Each slice is one PR from main, ready when CI is green.

## Out of scope

Shipping, saving or exporting a fitted model or its coefficients as a model artifact; prediction on new rows; held-out or cross-validated scores; model comparison or selection; choosing `k`; Poisson or other GLM families (a count target gets spec 035's T3 only); regularization; interactions and transformations; p-values and significance wording; causal wording; the 3D view itself (spec 037).
