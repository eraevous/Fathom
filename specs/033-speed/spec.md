# Spec 033: faster profiling, same bytes

**Serves:** P0@2, DG-RF (CHARTER rule 7: output is byte-identical across runs).
**Requested by Zach, 2026-11-21:** "Fathom should be faster" (first item of a wider request; the analyses follow in later specs). He chose "speed first" so that new analyses don't pile onto a slow base.
**Records:** `FT-SPD33-R1` (requirement, provisional, written by the implementer), `FT-SPD33-C1`, `FT-SPD33-E1`.

## The rule

A speedup may change how long a profile takes and nothing else. For the same input and configuration, `guide-profile.json`, `report.html` and `report.md` stay byte-identical to the previous release.

## Baseline (main at 14ef42e on 2026-11-21, one cloud machine)

`scripts/bench_speed.py --rows 200000` (20 columns: 12 numeric, 6 categorical, 1 timestamp, 1 numeric target-shaped column): **127 s**. Most of it was per-cell Python:
- type inference tried every cell of every column as a date, even after the first failure made a temporal reading impossible (5 million `parse_temporal` calls);
- the special-type check (email, URL, phone) scored every cell even when 80% was already out of reach;
- temporal columns parsed each value up to three more times for examples and fault counts;
- the intraday view made 24 + 60 + 60 + 168 passes over the parsed values;
- copy evidence between column pairs made four passes per pair.

## Slice 1 (this PR)

Same answers, fewer passes:
- `parsing.reaches(predicate, values, test)`: counts hits and stops when the rest of the column can't change `test(hits, total)`. Used by temporal inference and the special-type check. The tests stay exactly as written (`hits >= total*share`, `score/total >= .8`), so no float boundary moves.
- `temporal_profile` parses each value once; invalid examples and fault codes come from the values that failed (a value that parses has no fault).
- `intraday_profile` counts with one `Counter` per measure.
- `copy_evidence` makes one pass.
- `quality.finite` imports once instead of per call.

Result: **127 s → 81 s** (−36%) on the benchmark. JSON, HTML and Markdown are byte-identical apart from the input path (checked on the benchmark, the repository's CSV fixtures and a 30,000-row mixed table with timestamps, 12-hour clocks, timecodes, phones, emails, URLs, currency and a target).

## Next slices (not in this PR)

1. **Parse each column once.** `finite_number` still runs about 18 million times on the benchmark: inference, summary, univariate, quality and target analysis each re-parse the same cells. One parsed column per run, shared by every stage.
2. **Vectorized counting** where the arithmetic is exact (counts, min, max, ranks). Means and standard deviations stay on `statistics`, because a numpy sum can differ in the last digit and the stored values would change. A change there would need Zach's say-so.
3. A size gate in CI: the benchmark at 20,000 rows, warning (not failing) on a slowdown over 25%.
