# Intent: spec010 row-level and temporal checks (claude:dg#rowlevel)

1. Open PR #17 (spec only, unaccepted) already proposes row-level checks under
   `specs/009-row-level-checks`. This slice builds a structure-only subset and reuses #17's
   thresholds where they exist (k 2..20, >=90% coverage, <=10 positions, 1-based rows).
   Where they differ, narrower reading taken and recorded here; Zach reconciles.
2. Repeated keys screen every column by structure, not by name cues (#17 FR-004 uses
   `id`/`individual` cues). Name cues would be domain meaning; structure is measurable.
   To keep balanced small designs quiet, >=10 distinct keys is required (#17: >=3).
3. Blank rows: wholly blank rows, plus rows blank in every numeric column (>=2 numeric
   columns). This is a type-based stand-in for #17's year-heading value scope, which is
   not built. It reproduces #17's 9/18 truth on its `empty-values.csv` and is silent on
   its clean decoy.
4. Temporal outliers: the Tukey 1.5xIQR fence would not flag a pickup a few hours before
   a month of data, and is noisy on long spans. Two disclosed rules instead: >=99%
   concentration in one calendar month/year (stragglers reported), and a far fence at
   quartiles ± 3xIQR on day ordinals. Both are observations with a question.
5. Duplicate timestamps only for columns whose every value carries a time of day and
   >=90% of values are distinct (event-like); date-only columns repeat by nature.
6. Intervals require declaration (`intervals: [{start, end}]`); never inferred from names.
   Full date-times are parsed for this check only (date-only values read as midnight,
   counted in `date_only_pairs`); the FT-R14 date profile keeps calendar dates.
7. Zero-share generalisation not built: no accepted spec allows it; PR #19's proposal
   (docs/decisions/2026-11-04-proposed-contrast-threshold.md §2) is left as is.
8. Existing `duplicates` finding keeps its id; its message gains repeating-row positions.
   Nothing new enters pair selection, ranking or charts.
