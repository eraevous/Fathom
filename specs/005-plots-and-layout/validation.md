# Builder acceptance and validation: 005 plots and layout

Checked against docs/acceptance.md; authored synthetic tables only. Builder checks
are not Zach/Kate's independent acceptance. [Visual review](review/README.md) holds
screenshots, sources, fixes and remaining issues; claude:aec independent pass pending.

| Table | What the report found/shows | Missed / review noise |
| --- | --- | --- |
| layout/planted.csv,36x11 | Repeated title, unusual zero gross, two-digit/future date and gap, strong positive skew with additional log view; eight joint missing rows versus28complete;14category levels with top10covering77.8% and8other values; long-text length distribution; time-named numeric columns no longer called dates | No supported planted diagnostic family missed; benign notes dominance and deterministic lockstep columns also prompt review |
| layout/clean.csv,36x11 | Valid non-skew numeric/date distributions, one complete-row mask, no log view, unique titles | Two existing-rule actions for benign notes dominance/lockstep structure; no new plot-generated defect claims. Clean does not mean action-free |
| layout/late.csv,65x10, authored after implementation commit | Negative/zero/large amounts, skew review but no invalid positive-only log view; long text/unicode; exact category remainder;20of64missingness masks,44masks/44rows explicitly omitted;192missing cells | Mixed dates in a time-only-named column stay categorical, so date analyses require a human declaration; omitted masks cannot be inspected individually in this bounded summary; existing sentinel/dominance rules add review noise. Literal remainder-like category stays distinct from aggregate remainder |

The distributions and aligned tables make skew, coverage, missingness combinations
and date/type uncertainty reviewable. Existing typed actions provide consequences,
not just extra statistics. Reports preserve unknown meaning and basis; no cleaning,
score, target/group methods or automatic domain claims added.

Tests: **147 passed** with all extras; core **141 passed,6skipped** (one SciPy,
five export tests). New tests cover exact ECDF/counts/coverage, positive-skew log
eligibility and zero/negative/constant decoys, category collision, raw text lengths,
day/month/year periods with empty bins, exact/bounded masks and complete decoy,
time names, readable/escaped tables, artifact validation/legacy roundtrip and native
numeric XY/PDF exports. Existing fresh-process output/dependency tests still pass.
Native ECDF spacing is numeric, not category-based. HTML/PDF/PowerPoint remain
artifact-only and self-contained/offline; optional serializers remain independent.

## Proposed FT-R15 detail changes

Define log eligibility, histogram binning, ECDF rank-knot approximation and missingness
bounds explicitly rather than leaving them implicit implementation choices. Define
whether raw blank strings belong in category/length denominators. Consider an
explicit static distribution-detail policy to reduce report length, with human
selection/units rather than type-name guesses. Specify calendar bin policy and how
outlier dates affect it. Plan phone chart/export legibility with DG-D7; don't silently
claim current fixed views solve mobile review. None of these proposals is accepted.

Original records prefix and protected documents preserved. PR#10 merged during work;
branch rebased onto main d195f1b. AEC check and impact reported in PR; structural
review flags do not certify usefulness or accept provisional requirements.
