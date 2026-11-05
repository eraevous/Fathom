# Fathom

Fathom turns raw or semi-cleaned tabular data into understanding someone can use and pass on: an enhanced data dictionary, a diagnostic EDA engine and a repeatable working record. It answers what is in a dataset, what can't be known from it, and what it is good for.

**Status: target-analysis and distribution-polish slice.** Fathom is the successor to Data Guide.
It starts from guiding documents and decisions, with no earlier implementation,
and is built with [AEC](https://github.com/eraevous/AEC) and Spec Kit.

Fathom helps decide **what needs review before using a table**: an
enhanced dictionary, evidenced review actions, explicit unknowns, human decisions
and context-first before/after comparison. The slice-3 report scope is accepted; FT-R14 detail and
its algorithmic refinements and usefulness
remain for review. Tests and merge do not accept requirements.

## Try it with synthetic data

Python 3.12+. The package is `fathom-guide`; it installs one command, `guide`
(`python -m fathom` is the same CLI). `guide profile` and `guide validate` echo the
question, target and row unit they resolved. Column `type` overrides use the names
`numeric`, `categorical`, `boolean`, `temporal` (dates), `string`, `phone`, `email`,
`url`, `latitude` and `longitude`; `date_format` takes `ISO`, `ISO_DATETIME`
(`YYYY-MM-DD HH:MM[:SS]` or with a `T` separator, profiled by calendar date), `MDY`, `DMY` or `MON_D_Y`,
not strftime patterns. `guide export` without the extra still exits 0 and says on stderr
to run `pip install -e '.[exports]'` from the clone (the package is not on PyPI).

```bash
git clone https://github.com/eraevous/fathom.git && cd fathom
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

`guide-profile.json` (schema version 2; version 1 still loads) is the interface. Markdown and self-contained
HTML with embedded charts derive solely from that artifact. Re-rendering does not
need the CSV. Repeated runs with identical input paths, bytes, configuration and
dependency availability produce byte-identical outputs. No runtime date is added.

## Declare a question and keep a working record

YAML configuration supports `question`, `target`, `pair_budget` (0–20, default 5), `bins` (1–50),
`sections` (`samples`/`missingness_patterns`: true or false),
column meanings/type overrides, row unit, generating process, missingness mechanism,
human decisions/rationales, and profile context. See the
[synthetic example](tests/fixtures/review.yaml) and [CLI contract](specs/001-data-review/contracts/cli.md).
Unknown keys and column references fail before output is written.

A declared target produces a descriptive ranking: Pearson r for numeric pairs,
correlation ratio eta for category/numeric, and Cramer's V for category/category.
The table shows each measure, signed value, complete cases and selection; unlike
measures are a priority heuristic, not interchangeable effect sizes or causation.
Constant/near-constant/copy and identifier-like predictors have explicit exclusions.
`columns.NAME.exclude_from_target: true` marks known leakage/unwanted predictors;
unmarked derived predictors may remain ranked. Unique continuous numbers stay eligible.

Target pairs and quality missingness contrasts share pair_budget0–20. Light target
candidate ranking is separate from selected detail. Selected category-bearing pairs
carry within-group count/share/valid/missing, means/medians or rates, marked contrasts
and n<5cautions. For numeric targets one category slot is reserved at budget>=2;
`group_by` can name a category and reserve it at budget1. Group summaries remain
pair-local; this does not summarize every column under every grouping. The report
discloses the reservation and exclusions. No target gives an explicit skipped reason
and keeps documentation/QA fallback. Selected numeric relationships have bounded
scatter views; categories use group boxes or target rates by group/bin. No target
versus two-predictor or model-based analysis is added.

Optional `pip install -e '.[stats]'` retains existing Pearson p-values with stated
assumptions. Without it, core measures/counts remain available; p-values never select
relationships. See [spec007 and found/missed ledger](specs/007-target-analysis/validation.md)
and its [visual review](specs/007-target-analysis/review/README.md).

Inferred types retain uncalibrated confidence, reasons and alternative readings.
Human overrides take effect without erasing inference. Leading-zero codes remain
strings by default; blank/whitespace cells are missing, while `NA`, `null` and `0`
are literal values. Date inference recognizes strict ISO, English month names and slash dates with
recorded ambiguity and a fixed two-digit-year pivot (69). Numeric
overrides count incompatible/non-finite values rather than silently coercing them.

## Configure

```bash
guide configure data.csv --out configure/            # optional: --config existing.yaml
```

writes `configure/configure.html`, a self-contained page (inline CSS and JavaScript,
no network), and `configure/configure-profile.json`, the profile it was built from.
The page lists each column's inferred type and observable facts (populated share,
distinct values, parsed date formats) with controls for a type override, a
`date_format`, and `exclude_from_target`; a target selector whose candidates carry only
observable reasons ("numeric; 96.0% populated; 14 distinct"); temporal column pairs as
unticked interval suggestions (written as `intervals: [{start, end}]`); time series
offered unticked by the report's own rule (a temporal column with at least 30 distinct
periods, as event counts or as the sum of a numeric column that is not identifier-like),
each with an optional `by` column and granularities (`auto`, `hour`, `day`, `week`,
`month`); histogram `bins` (default: square root of n, capped at
10; a declared value applies to every histogram, including string lengths and the
positive log view); `pair_budget`, `sample_rows`; optional report `sections` (`samples`,
`missingness_patterns`); and the question and row unit. Every control starts at the
system default; a suggestion applies only when you tick it. The page writes YAML live
(Copy or Download), using only keys `guide profile --config` accepts, and a separate
`config-manifest.json` saying which values were default, suggested or selected. The
manifest also carries the sha256 of the exact YAML bytes it
describes; it is advisory, not an audit certificate, and Fathom does not read it.
Settings the page does not offer (`time_series.max_lag` and `top_n`, or a series on
other columns) may be declared directly in YAML; values from `--config` are kept. Evidentiary thresholds are shown
read-only with their record ids; no control suppresses a finding. An omitted section
is named under "What the data cannot tell" as omitted by configuration, and stays in
`guide-profile.json`.

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

What it finds at row level (spec010; counts plus the first 10 row positions, 1-based,
header excluded; each paired with a question, never a cleaning step):

- wholly blank rows, and rows not wholly blank but empty in every numeric column (needs
  >=2 numeric columns); positions of repeated rows;
- "most nonmissing rows belong to groups of exactly k by `col`" (with the coverage share),
  and the columns that never change within a group;
- observations of selected temporal structures (not anomaly detection): date values outside the dominant month/year or beyond quartiles ± 3×IQR, and repeated
  event timestamps. Day resolution: same-day stragglers, and stragglers inside the
  dominant month/year, are not detected;
- declared `intervals: [{start: a, end: b}]`: end before/equal to start and durations
  in seconds (full ISO date-time parsed; unparsed pairs are counted and asked about);
  two undeclared date columns only raise a question.

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

## Special types and optional exports

Phone, email, URL and latitude/longitude readings are inferred and retain human
overrides. Local syntax, repeated-digit placeholders, test-like emails, domains
and independent degree ranges produce counts/examples and review suggestions.
No ownership, deliverability, reachability, geocoding or sensitive-data tags are
inferred; the application performs no network lookup.

```bash
.venv/bin/pip install -e '.[exports]'  # or [pdf] / [pptx] independently
.venv/bin/guide profile tests/fixtures/special/planted.csv --out reports/special
.venv/bin/guide export reports/special/guide-profile.json --out reports/exports
```

Export works solely from the saved artifact. HTML/Markdown are always available;
`export-status.json` records each requested binary as written or unavailable, its
serializer version, artifact hash, PDF unsupported-glyph replacement count and
slide count. Missing extras do not crash. PDF includes the summarized findings
and all sample windows; wide samples split into column batches. Bundled-font
unsupported characters become `?` with an explicit notice; exact text stays in
core views/JSON. PowerPoint has summary, key finding topics and native charts;
it does not carry the full dictionary/sample tables. Metadata and nested workbook
ZIP times are fixed. Bytes are repeatable with identical dependency versions.
See [spec004](specs/004-special-types-and-exports/spec.md) and its
[found/missed ledger](specs/004-special-types-and-exports/validation.md).

## Plots and review layout

Column entries now span the content width, with formatted overview tables and
inline static plots. More statistics use value/count/share tables; raw evidence
stays disclosed. Numeric ECDF/eligible additional log views, category remainder and
coverage, string lengths, calendar bars and exact row-missingness patterns come
from the saved artifact. Time alone no longer suggests a date. Old artifacts and
optional exports remain supported; no new runtime dependency.

Column headers start collapsed. Expanded entries place compact statistics beside
plots, stacking at phone width; charts scale without horizontal page overflow.
Intermediate formatted ticks, wrapping horizontal HTML/PDF axis captions and a
separate box summary avoid crowded annotations. Skewed columns with zeros retain
a positive-only log histogram and ECDF with explicit exclusion counts and original-value
ticks. Single-variable box plots are slim strips; desktop statistics stay in view
while plots scroll (the statistics panel itself can scroll). Identifier-like/near-unique
top-N charts are replaced by a repetition explanation.

PowerPoint defaults to a summary of at most12slides, with omitted chart counts;
`guide export PROFILE --out DIR --deck full` selects all topics/charts.
Fixed PDF pages and slides still require zoom on phones; dynamic layout building
remains future work under DG-D7. See
[spec005](specs/005-plots-and-layout/spec.md), its
[builder found/missed ledger](specs/005-plots-and-layout/validation.md) and
[slice-4 visual review](specs/005-plots-and-layout/review/README.md), plus
[polish review and current open issues](specs/006-report-polish/review/README.md).

## Small numbers, missingness by group and themes

Stored statistics keep at least 6 significant figures (never fewer than the earlier
10 decimals), so a column at the 1e-12 scale keeps its percentiles, mean and SD
instead of storing 0; normal-scale and large-offset values are unchanged.
Dimensionless coefficients (skewness, kurtosis, r, eta, V) keep 10 decimals so
symmetric data does not report float noise. Artifacts are schema version 2.

A missingness-by-group test reports "Missingness in X varies with G" as an
observation only: chi-square on missing/present by group, groups of at least 10,
Bonferroni over the tests run (family alpha 0.01) and Cramér's V ≥ 0.15, all
disclosed under `quality.missingness_tests`. It never suggests an action or selects
pairs; on 20 null tables it reports nothing. HTML findings carry kind-coloured tags,
and the report follows the system light/dark setting (`data-theme="light"` or
`"dark"` on `<html>` overrides it). Colours come from one palette, `fathom/palette.py`.
See [spec008](specs/008-salvage-decisions/spec.md) and its
[visual review](specs/008-salvage-decisions/review/README.md).

## Time series

Declare a series; Fathom never infers one from column names.

```yaml
time_series:
  - time: pickup          # strict ISO date/date-time (or the column's date_format)
    value: null           # null counts rows (events); a column sums its values
    by: zone              # optional: top_n groups by row count (default 5, max 20)
    granularities: [hour, day]   # or [auto]: hour/day/week/month as the span allows
    max_lag: 48           # optional; defaults 168/28/26/24 by granularity
```

The report gains a **Temporal structure** section (artifact key `time_series`): the
observation process (raw rows, distinct and repeated timestamps, missing observations
vs explicit zeros vs periods with no event), the four sparsity dimensions per
granularity — **frequency** (zero share, inter-event interval; ADI alias),
**amplitude** (non-zero quantiles, CV²), **wavelength** (ACF/PACF of values and of
the occurrence indicator, dominant and calendar lags, optional periodogram peak with
the `stats` extra) and **duration** (zero-run and burst lengths) — ACF/PACF stem plots
for two granularities, and a present / absent / insufficient-evidence summary with
each rule. Fewer than 30 periods is insufficient; a constant series is undefined; lags
beyond n/4 are marked poorly supported. Without a declaration, one question suggests
one. See [spec011](specs/011-time-series/spec.md).

## Scope and limits

This is a local, in-memory, single CSV/wide slice under `DG-D1`'s data-to-decisions
definition. It does **not** complete the April connector/CLI checklist. Globs,
Excel/JSON/database connectors, long tables, interactive guidance, broader EDA,
dashboards and narrative generation are deferred. Explicit long contracts
are rejected. No data is changed or transmitted by the application.

Comparisons state both source contexts, dates, declared transformations and other
changes before aggregate measured deltas. They cannot reconstruct row-level
lineage or establish why a difference occurred. Type/meaning changes are flagged.

Committed fixtures are authored synthetic examples or [pinned, sourced public
review tables](tests/fixtures/polish/README.md). Exported reports can
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

## Liftoff: discover, then configure

```bash
guide liftoff DATA.csv --out discovery
# Open discovery/liftoff.html; read the Brief, then explicitly choose controls.
# Download liftoff.yaml from the page.
guide profile DATA.csv --config liftoff.yaml --out report
```

Liftoff writes liftoff-profile.json(schema2) and a self-contained Brief +
Configurations page. Automatic facts and questions are separate from conditional
**If you declare…** interval/event-count previews. No target or declaration is
applied; untouched YAML is{}. The configurator carries offline JS; the Brief
and ordinary report sections are static. The advisory manifest stays separate
from effective YAML. `guide render discovery/liftoff-profile.json --out restored`
restores the same page. `guide configure` keeps its existing behavior.

Previewed series use events and auto granularities, up to20candidates; changing
value/granularity changes the question. All caps/omissions and rules are disclosed.
The narrow all-zero-category observation asks whether zeros are structural or
unrecorded; it does not assert a mechanism or add a stage-two zero rule. Brief/
conditional temporal exports to PDF/PPTX are not added. See
[spec013](specs/013-liftoff/spec.md) and [validation](specs/013-liftoff/validation.md).

### Offline installation and panel profiling

Prepare wheels on a connected machine with the **same Python version, OS and CPU
architecture** as the offline target. Build from the reviewed repository checkout:

```bash
python -m pip wheel --wheel-dir wheelhouse .
# Optional existing statistics and Office serializers:
python -m pip wheel --wheel-dir wheelhouse '.[stats,exports]'
```

Transfer the wheelhouse using an approved local process, then on the target:

```bash
python -m pip --disable-pip-version-check install --no-index --find-links wheelhouse fathom-guide
# If the optional wheels were prepared:
python -m pip --disable-pip-version-check install --no-index --find-links wheelhouse 'fathom-guide[stats,exports]'
```

No source build or package index is needed on the target. Keep the reviewed
wheelhouse/version inventory for reproducibility. Fathom reads local files, has no
telemetry or network connector, and its generated HTML embeds its resources.
The offline regression harness denies socket creation before application import
and compares command output bytes; it also checks page resources. Existing optional
serializers may import unused standard-library URL helpers, but no network attempt
is allowed. No current command needs even loopback sockets; no server is included.

`guide panel LONG.csv --config panel.yaml --out DIR --aggregate week,month`
profiles declared long panels. Configuration names the series key(s), ISO date,
nonnegative value, native day/week/month period, and optional exposure/state columns.
Windows separate training signals from evaluation-volume context. Missing, absent,
closed and observed-zero periods remain distinct; unequal exposure is a separate flag.

Outputs include `panel.json`, a static HTML/Markdown report and `series-signals.csv`.
Optional generated views have separate artifacts and source/state/exposure lineage.
Declared metric CSVs join by series/model/window/horizon with explicit unmatched keys;
selected metrics reuse the existing target-analysis report. Metric disagreement is
not failure; repeated series across models/windows are not independent evidence.
No volume boundaries or metric definitions are supplied by default. See
[spec014](specs/014-offline-panel/spec.md) and its [CLI contract](specs/014-offline-panel/contracts/cli.md).
