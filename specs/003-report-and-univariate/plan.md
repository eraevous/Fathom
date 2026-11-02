# Plan: 003 report and univariate

Python 3.12+, existing pandas/PyYAML; no new runtime dependency. Existing pytest,
setuptools and optional SciPy remain justified by prior plans. Stdlib random,
statistics, date and local SVG cover this feature. Local Playwright is verification
only. Scope is in-memory CSV/wide; no network or new relationship methods.

## Constitution check

PASS before/after design: one flow, typed evidence/inference labels, bounded
relations unchanged, context-first comparison, artifact-only views, deterministic
synthetic/decoy/degradation tests, public-only fixtures. No charter amendment.

## Structure and sequence

1. tests/test_univariate.py and synthetic fixtures define samples/metrics/findings.
2. parsing.py supplies explicit local numeric/date parses; univariate.py supplies
   stats/chart specifications, identity/samples and typed diagnostics.
3. Connector/input wrapper preserves lexical rows for bounded samples and blank
   variants; config validates title/description/sample settings/date formats/units/role.
4. Profiler integrates helpers, models validate additive fields; charts.py renders
   labelled SVG from chart specs. renderers.py enforces FT-R6@3 order and disclosures.
5. Legacy, bytes, browser, core/stats and acceptance ledger; AEC snapshot/evidence.

No research outside repository. Sampling/parse/moment/rarity/period rules and limits
are resolved in the intent note. Tables and chart limits are explicit. Additions
are optional artifact-v1 fields; absence on old artifacts is never synthesized as
measured data. Keep source sample rows bounded and truncated with a visible marker.

## Drift and acceptance

Helper modules stay in profiler/rendering responsibilities. Check planted/clean
and later tables from the report alone; document misses and FT-R14 changes. No
quality score, sensitive-data tagging, AI narrative or FT-R7/8. Publish through PR.
