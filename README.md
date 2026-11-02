# Fathom

Fathom turns raw or semi-cleaned tabular data into understanding someone can use and pass on: an enhanced data dictionary, a diagnostic EDA engine and a repeatable working record. It answers what is in a dataset, what can't be known from it, and what it is good for.

**Status: report and univariate slice.** Fathom is the successor to Data Guide.
It starts from guiding documents and decisions, with no earlier implementation,
and is built with [AEC](https://github.com/eraevous/AEC) and Spec Kit.

Fathom helps decide **what needs review before using a table**: an
enhanced dictionary, evidenced review actions, explicit unknowns, human decisions
and context-first before/after comparison. The slice-3 report scope is accepted; FT-R14 detail and
its algorithmic refinements and usefulness
remain for review. Tests and merge do not accept requirements.

## Try it with synthetic data

Python 3.12+:

```bash
python -m venv .venv
.venv/bin/pip install -e '.[test]'
.venv/bin/python -m pytest
.venv/bin/guide profile tests/fixtures/review.csv --config tests/fixtures/review.yaml --out reports/before
.venv/bin/guide profile tests/fixtures/revised.csv --config tests/fixtures/revised.yaml --out reports/after
.venv/bin/guide compare reports/before/guide-profile.json reports/after/guide-profile.json --out reports/comparison
.venv/bin/guide render reports/before/guide-profile.json --out reports/rendered
.venv/bin/guide validate tests/fixtures/review.csv --config tests/fixtures/review.yaml
```

Open `reports/before/report.html` offline. Its two review actions link to the
observed missing amount and repeated full row. They recommend investigation,
not deletion or imputation. The clean fixture produces neither review action.
The report also asks about unsupplied row unit, meanings, generating process and
missingness mechanism. It never guesses a domain explanation.

`guide-profile.json` (schema version 1) is the interface. Markdown and self-contained
HTML with embedded charts derive solely from that artifact. Re-rendering does not
need the CSV. Repeated runs with identical input paths, bytes, configuration and
dependency availability produce byte-identical outputs. No runtime date is added.

## Declare a question and keep a working record

YAML configuration supports `question`, `target`, `pair_budget` (0–20, default 5),
column meanings/type overrides, row unit, generating process, missingness mechanism,
human decisions/rationales, and profile context. See the
[synthetic example](tests/fixtures/review.yaml) and [CLI contract](specs/001-data-review/contracts/cli.md).
Unknown keys and column references fail before output is written.

Existing target-related value routes and quality missingness contrasts share the
budget. They rank by declared focus, descriptive strength, case count and lexical
ties, rather than input column order. Near-duplicate and near-constant value
columns are excluded. Numeric pairs retain complete-case Pearson coefficients;
category/boolean × numeric pairs retain group counts and means. Quality contrasts
show group sizes and missing rates, including without a target. Ranking and
exclusions are disclosed; associations never establish causation. No new general
target-analysis methods are included in this slice.
Optional `pip install -e '.[stats]'` adds SciPy p-values with stated assumptions.
Without it, coefficients/counts remain available and p-values are labelled unavailable.
P-values do not choose review actions.

Inferred types retain uncalibrated confidence, reasons and alternative readings.
Human overrides take effect without erasing inference. Leading-zero codes remain
strings by default; blank/whitespace cells are missing, while `NA`, `null` and `0`
are literal values. Date inference recognizes strict ISO, English month names and slash dates with
recorded ambiguity and a fixed two-digit-year pivot (69). Numeric
overrides count incompatible/non-finite values rather than silently coercing them.

## Data quality and readable reports

```bash
.venv/bin/guide profile tests/fixtures/quality/workshop.csv --out reports/quality
.venv/bin/guide profile tests/fixtures/quality/holdout.csv --out reports/quality-holdout
```

The report orders Dictionary, Provenance, Dataset summary, Findings and Relations.
Technical detail starts collapsed. The summary records completeness, duplicate and
lockstep columns, inferred types, constants and missing cells, with finding links,
usefulness and unknowns. Findings are plain sentences; evidence and uncertainty expand in one
click. **Show full per-item detail** switches grouped column findings to their
complete original items and back. The HTML is self-contained and uses no script.
Both views come from the same saved artifact; Markdown has static disclosures.

Quality findings cover suspected sentinel/placeholder/dummy values, dominance,
duplicate/lockstep/near-copy columns, co-missingness and segment-dependent missing
rates, inferred date-cadence gaps, strong skew and repeated rows. Heuristics, sample
minima and screening limits are disclosed. They never confirm a defect or domain
meaning. For example, the holdout's valid extreme 999 triggers an unnecessary
sentinel review, while its unlisted 888, compound dummy label and intended monthly
gap are only partially found or missed. See the complete
[builder found/missed ledger](specs/002-data-quality/validation.md) and
[slice-2 intent note](codex_++/intents/2026-11-01__data-quality.intent.md).

Old version-1 artifacts remain renderable. New completeness measurements requiring
raw rows are explicitly unavailable there. The quality helper uses no new optional
dependency. FT-R7 target methods and FT-R8 switchable chart axes remain later work.

## Univariate profiles and samples

```bash
.venv/bin/guide profile tests/fixtures/univariate/film.csv --config tests/fixtures/univariate/film.yaml --out reports/film
```

Dictionary disclosures include first/last/random rows (20 each by default), with
a recorded fixed seed, original lexical values and explicit bounded-text truncation.
Config accepts `title`, `description`, `sample_rows`, `sample_seed`, `sample_text_limit`,
and column `units`, `role` and `date_format`; supplied identity is human-labelled,
otherwise a filename/schema description is labelled inferred.

Numeric profiles include percentiles, population skew/excess kurtosis, zero/negative
shares, histogram and box views. Text profiles include raw blank candidates, length,
casing, punctuation, word tokens, rare levels, coverage and entropy. Date profiles
include span/calendar counts, gaps, lag-one monthly-count correlation, invalid dates,
century ambiguity and after-snapshot/placeholder review. Every chart has a title
and labelled axes. Repeated identifier/title and unusual-zero findings remain
conditional review suggestions. See [spec003](specs/003-report-and-univariate/spec.md)
and its [found/missed ledger and proposed FT-R14 changes](specs/003-report-and-univariate/validation.md).

## Scope and limits

This is a local, in-memory, single CSV/wide slice under `DG-D1`'s data-to-decisions
definition. It does **not** complete the April connector/CLI checklist. Globs,
Excel/JSON/database connectors, long tables, interactive guidance, broader EDA,
dashboards, PDF and narrative generation are deferred. Explicit long contracts
are rejected. No data is changed or transmitted by the application.

Comparisons state both source contexts, dates, declared transformations and other
changes before aggregate measured deltas. They cannot reconstruct row-level
lineage or establish why a difference occurred. Type/meaning changes are flagged.

All committed fixtures are authored synthetic examples. Exported reports can
include values/examples from the supplied table. Use public or synthetic inputs
for this run. Tests demonstrate conformance on those examples; usefulness for
most projects and business fitness have not been established.

The [slice-1 spec](specs/001-data-review/spec.md) and
[slice-2 spec](specs/002-data-quality/spec.md), with their plans and intent notes,
record scope, dependencies, clarification readings and trade-offs.

| Start here | What it holds |
|---|---|
| `AGENTS.md` | how agents work in this repository |
| `.aec/records.jsonl` | the accepted purpose, requirements, assumptions and decisions |
| `docs/decisions/` | Zach's own words behind them |
| `CHARTER.md` | engineering rules |
| `docs/vision.md`, `docs/design.md` | the vision and the distilled April 2026 design |

License: MIT. Contributions are welcome under the [CLA](CLA.md).
