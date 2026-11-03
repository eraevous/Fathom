# Plan: Target analysis and distribution polish

Python3.12 CLI/library; existing pandas/PyYAML, optional SciPy/ReportLab/python-pptx.
No new application dependency. Existing review-only Chromium/Playwright,
LibreOffice/PyMuPDF/Pillow render actual screenshots. Storage is additive artifactv1.

## Constitution check

PASS before/after design: profiler alone joins raw data and artifact; renderers
consume only artifact. Typed attributed evidence, retained semantic inference,
bounded question-selected pairs, context-first comparison, deterministic output,
missing optional extras degrade, public/synthetic inputs. No protected-doc edits.
Extension hooks optional: purpose-link, structural check and impact are executed.

## Design / project structure

Extend src/fathom/profiler.py select_pairs/rank_pairs, preserving legacy methods
pearson/grouped_numeric and quality contrasts. New src/fathom/target.py provides
core measures, selected-pair group summaries, contrasts, artifact display tables and
bounded chart specs. New target_marks.py provides simple shared static geometry
for scatter/group-box/rate plots in SVG, PDF and editable PowerPoint vector shapes.
This is a helper in the existing artifact→renderer path, not a new analysis service.

config.py adds per-column exclude_from_target:boolean and top-level group_by name;
validate references/types. models.py validates additive target_analysis and log ECDF
metadata with legacy support. presentation.py exposes original-unit log ticks;
charts.py / exports.py use these across formats. univariate.py emits positive-only
log ECDFs. renderers.py displays ranking/groups/charts under Relations and keeps
statistics sticky on desktop (normal stacking on phone); no HTML script.

## Algorithms / budget (provisional readings)

Numeric: core Pearson r, signed value, abs(r) ranking. Category/numeric: eta =sqrt
between/total variance using scaled values; category/category: unadjusted Cramer's V.
Complete-case counts and effective semantics retained. No p-values for new measures;
existing optional Pearson p-values retained after selection, never used for ranking.
Categorical/boolean pairs<=20levels; numeric/latitude/longitude are quantities;
dates/special/free-text pairs excluded unless humans declare supported types.

Exclude configured columns, identifier roles, near-unique text/category (>=90%
distinct with>=5values), existing quality constant/near-duplicate exclusions and
row-near-copy of target. Continuous unique numbers remain eligible. Preserve known
legacy<=small-sample routes. An unmarked rank/affine leak may remain ranked; never
exclude all perfect correlations as though they proved leakage.

Compute one light candidate per eligible target column O(rows*columns); selected
value/quality pairs remain<=pair_budget. Existing focus/strength/n/lexical ranking
extended with eta/V strength. For numeric target and budget>=2, reserve one of the
selected slots for the best eligible category (declared group_by preferred) if not
already chosen. At budget1, only explicit group_by reserves the slot. Ranking stays
visible with selected status/reservation notice; quality contrasts use remaining
slots. Categorical target groups every selected pair by the target. No unbudgeted
group×other-columns sweep; numeric group summaries describe target within selected
category, categorical-target summaries describe the selected predictor within target.

Group share uses all rows (missing grouping rows separately counted). Each summary
includes observed count, valid/missing, missing share, mean/median/min/max or level
counts/rates. n<5 marks too small to read reliably; observed contrasts still visible.
Compare group versus rest: numeric mean difference>=overall population SD (both
nonempty), missing/rate gap>=0.30. Group count>=1, rest>=1; explicit n cautions.
No multiplicity-controlled significance or automatic defect verdict. At most20groups
and20category levels, rates include each valid denominator.

Charts: one per selected target pair. Scatter<=200deterministically spaced sorted
complete points, disclosed omissions; use log scale on eligible positive dimensions
and disclose removed nonpositive/invalid/missing cases. Category/numeric boxes use
complete-case five-number summaries; categorical target plots target-category rates
within predictor category or deterministic<=4equal-width numeric bins (empty bins
shown). One pair can carry summaries and plot without another budget charge.

FT-R19: original-value log ticks (no inferred currency); slim box strips without Y
caption; desktop sticky statistics while plot stack scrolls; positive-only log ECDF
conditional on positives with all zero/negative/invalid exclusions recorded. Linear
ECDF retained. Native Office log ECDF uses raw positive coordinates and logarithmic
axis; category histogram bin labels use original bounds.

## Validation strategy

Tests first for exact measures/decoys, rank/budget/reservation, explicit exclusions,
small shifted groups, rates/missingness denominators, log ECDF coverage/ticks,
artifact validation/legacy and selected plot/export bytes. Update older exact
expectations only when FT-R7 changes their accepted semantics. Authored planted
relationship, known rank leak/configured exclusion, shifted small group; clean decoy
and late independent-pattern fixture for builder acceptance. Public pinned films
Worldwide Gross and college Median for before/after FT-R17 desktop/phone allformats.
Capture actual exports and inspect. Run full/core suites, fresh-process repeatability,
AEC edges/check/impact; verify branch-base record prefix and protected bytes; rebase
only after#14merges. Open one PR then stop.
