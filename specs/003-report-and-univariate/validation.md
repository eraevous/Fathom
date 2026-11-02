# Builder validation: 003 report and univariate

HO-20261102-001, codex:aec. Scope accepted; FT-R14 detail and algorithm choices
remain provisional. Builder conformance is not Zach/Kate's unseen-table acceptance.

| Authored synthetic table | Found in report | Missed / review noise |
| --- | --- | --- |
| film.csv, 30x6 | English month dates (29 valid, 1 invalid calendar date), fixed-pivot 2044 year and after-snapshot warning, 1900 placeholder, two large date gaps, one repeated title with unique row IDs, $0 gross against median positive 1.6 million, raw blank/case/punctuation/rarity profiles | No planted supported family missed; dates remain inferred, not corrected |
| clean.csv, 30x6 | Valid distinct dates, positive grosses, unique titles; no review actions | No planted problems or diagnostic false alarms |
| late.csv, 6x4 (after implementation commit) | Repeated title, ambiguous numeric MDY/DMY reading, two-digit century warning, after-snapshot dates, partial date surfaced as incompatible | Partial month/year 'Dec 1999' is not understood at its original precision; zero among $10–$50 misses the >=100 scale heuristic; a legitimate planned 2027 date draws an unnecessary domain review |

Each change was checked against acceptance: dictionary/examples/samples provide
standalone documentation; identity/inference labels and collapsed provenance
explain authority; univariate findings reveal consequences (century ambiguity,
zero meanings, repeated titles) rather than only a statistics dump. Late-table
misses were not tuned away. No independent usefulness outcome is claimed.

Verification: **118 passed** with SciPy, **117 passed and 1 skipped** without it.
Exact metrics, entropy, date breakdowns, raw blank variants, format override,
invalid configuration/artifact data and all old regression/bytes tests pass.
Browser confirms dictionary→provenance→summary→findings→relations, collapsed
provenance internals, 20 first-row samples, chart titles and native full-item
switch. Samples use recorded seed17 in the fixture; default seed0, default N20.
HTML/Markdown derive from artifact only. No new runtime dependency.

## Proposed changes to FT-R14 detail

1. Define date precision/locale/timezone explicitly; partial months and timestamps
   need a precision-aware contract rather than inventing days or local time.
2. Replace the fixed two-digit pivot with explicit human century policy when known;
   retain the raw value and ambiguity. After-snapshot dates may be valid forecasts.
3. Make zero/rarity rules depend on declared units and roles; absolute magnitude100
   misses small-unit coded zeros and can overflag legitimate free items.
4. Specify population vs sample/bias-adjusted moment definitions and minimum sample
   sizes; tiny-sample skew/kurtosis is descriptive, not evidence for normality.
5. Define 'substrings': this slice counts case-folded word tokens, not arbitrary
   substrings. Bound high-cardinality/rare-level displays and avoid diagnosing
   every unique identifier as a rare-category problem.
6. Use explicit currency/units metadata for comparable quantities; symbols alone
   do not justify merging currencies. The box alternative avoids unspecified KDE.

These are proposals, not accepted record edits. No quality score/subscore, FT-R7/8,
PII/PHI tagging, network lookup or AI layer. Existing pair methods are unchanged.
AEC snapshot/check/impact are reported in the PR; original record prefix and
protected documents are preserved. The branch starts from 65d2fb6 and rebases onto
f702ad9 after both decision PRs merged. Records/planning precede code.
