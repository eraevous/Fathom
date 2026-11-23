# Spec 034: more relationships, still bounded

**Serves:** P0@2, DG-RC (selection and budget), FT-R7 (byte-identical output), CHARTER rule 4 (the question selects the analysis; no all-pairs explosions).
**Requested by Zach, 2026-11-21:** "Fathom should be faster, should have far more bivariate and multivariate analyses, …". He chose diagnostic framing, optional extras only, and speed first (handoff HO-FTH-20261121-0ETR in relay-kit-private).
**Status:** spec only, provisional. No code in this PR. Speed (spec 033) is still first: slice 1 is Fathom#67; slice 2 waits for it to merge, so this spec is written now rather than stacked on it.
**Records:** `FT-REL34-R1` to `FT-REL34-R5`, written by API Kate (`author_role: independent`, reply `kate-replies:replies/HO-FTH-20261121-0ETR--6a3ca5c12dc3.md`, ask `6a3ca5c12dc3`), committed verbatim in `.aec/records.jsonl`. The table, bounds and acceptance below are the implementer's reading of those records, not Kate's text.

## What exists today

With a declared target, `target.target_candidates` scores the target against every other column once (linear in the number of columns, not quadratic), records an exclusion reason for each column it skips, ranks the rest and gives `pair_budget` (0–20, default 5) of them the type-pair measures from spec 027. Nothing relates two non-target columns, and nothing conditions on a third column. Without a target there are no pairs.

## What this spec adds

Each addition runs only when the configuration asks for it. Nothing here runs on an undeclared table, and no addition widens the existing target screen.

| # | Analysis | Runs when | Bound | Kate's record |
|---|---|---|---|---|
| A1 | **Declared association matrix:** the 027 measure for each pair inside a declared column set (Pearson and Spearman for numeric pairs, eta for category×numeric, bias-corrected Cramér's V for category pairs) | `relationships.sets: [{name, columns}]` | at most 12 columns per set (66 pairs), at most 3 sets | R1, R2, R3 |
| A2 | **Conditional association:** a selected target pair re-measured within each level of a declared conditioning column, beside the marginal value | `relationships.condition_on: [column]` | conditioning column of 2–10 levels; levels under 30 complete cases are reported, not measured | R3, R4 |
| A3 | **Partial correlation:** a numeric target pair with the declared numeric controls removed (residual-on-residual, stdlib least squares) | `relationships.controls: [columns]` with a numeric target | at most 5 controls; skipped with a reason when the controls are collinear | R4, R5 |
| A4 | **Collinearity within a set:** variance inflation factor for each numeric column of a declared set | a declared set with 3 or more numeric columns | the set's bound | R2, R3 |
| A5 | **Principal components of a set:** scree (share of variance) and loadings of standardized numeric columns | a declared set with 3 or more numeric columns | the set's bound; components shown up to 90% of variance or 6, whichever comes first | R2, R4 |

A4 and A5 have stdlib fallbacks for small sets (Gaussian elimination and Jacobi rotation are enough at 12 columns). With numpy present they may use it only where the stored numbers are identical; otherwise the stdlib path stays the one that writes the artifact (CHARTER 7).

### The no-all-pairs reading (Kate's dissent, adopted)

"A capped output is not a bounded analysis." The bound is on what is **computed**, not what is shown. A1 computes only pairs inside a declared set, so the number of pairs is fixed by the configuration before any data is read. There is no "screen every pair, keep the top ten" mode, and the spec does not add one. An undeclared wide table gets the same target screen as today and nothing more.

A budgeted screen of non-target pairs (a deterministic candidate policy, as R1 allows) is **out of this spec**. If Zach wants one, it is its own `Decision:` PR, because choosing pairs without a question is the thing CHARTER 4 guards against.

### Wording

Every result is an `observation` with its measure, usable n, exclusions and the sampling policy (R3). Conditional and partial results say "within levels of X" or "with X held linear", never "controlling for confounding" or "the effect of". A5 loadings are described as directions of shared variance in this table, not as latent factors. No addition creates an `action` finding or a ranking of "important predictors" (R5).

## Acceptance (from Kate's records, made concrete)

- **R1:** a 200-column fixture with no declared set produces exactly the findings it produces today; with one 12-column set it computes 66 pairs and the run log says so. Two runs produce byte-identical artifacts.
- **R2:** integer-coded category columns declared `kind: category` are measured as categories; constant, all-missing, over-20-level and fewer-than-3-case columns produce a named skip, not a number.
- **R3:** with planted missingness, each result's n plus its exclusions reconcile to the table's row count.
- **R4:** a confounded fixture (X and Y both driven by Z, no direct link) shows a marginal correlation near 0.7 and a partial and within-level correlation near 0; the finding names Z and how it was declared.
- **R5:** no wording rule produces "significant", "causes", "drives" or "important"; a test greps every new template.

## Slices

1. A1 and its wording, in two PRs to stay near 300 lines: **1a** config, measures, JSON and the set finding; **1b** the HTML/Markdown table and CSV export.
2. A2 and A3.
3. A4 and A5, with the stdlib fallback and the identical-numbers check.

Each slice is one PR from main, ready when CI is green.

## Out of scope

Exhaustive or top-k pair search; any fitted model (spec 036); diagnostics for a model family (spec 035); the 3D view (spec 037); p-values or significance language; causal wording.
