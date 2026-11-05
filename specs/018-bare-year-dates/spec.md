# Feature Specification: Explicit bare-year dates
Created2026-11-05; provisional. Branch018-bare-year-dates.
Serves:P0@2,DG-RA@1,DG-RB@1,DG-RE@1,DG-RF@1,FT-YEAR-R1@1.
Input:E4V9 addition4, same authorization. Kate first; Zach accepts/merges.
## User Scenarios & Testing
### US1 — Declare annual precision (P1)
A four-digit year is explicitly parsed via date_format:YEAR into1January of that
year, labelled as an annual calendar anchor. Profile supports declared yearly time
series; panel accepts yearly source periods and raw years with declared keys.
The same numeric values without a temporal declaration stay numeric. No automatic
inference from column name/year-looking numbers.
Acceptance: synthetic1976–2024 entity/year rows; four-digit int/string parser controls;
missing years stay absent in panel, not zero; annual windows use existing ISO bounds.
### US2 — Recover from a wholly failed temporal declaration (P1)
If all nonmissing temporal values fail parsing, report/CLI say which formats were
tried and offer the best supported format by parse count. Ties remain alternatives;
no match stays unknown. No automatic fallback or replacement of invalid raw values.
Acceptance: raw years with temporal override but no YEAR; wrong explicit ISO;
reverse failure (ISO values declared YEAR); non-date text and all-missing decoys.
### Edge cases
0000/10000/bool/float/partial years rejected; 0001 string valid for general parser,
existing narrower panel bounds retained. Coarse YEAR does not create weekday/month
profiles or fine-grained series; Jan1 anchor is not an observed day or placeholder.
## Requirements
FR1:Explicit YEAR parser, no default numeric retyping. FR2:Native year period in
profile series and panel; unchanged existing auto analyses for other formats.
FR3:Annual precision/anchor disclosure and #28 edge coverage integration.
FR4:Actionable100%-failure formats/nearest recommendation in saved evidence,
report and CLI. FR5:Existing target type restrictions remain, with routing guidance.
FR6:Deterministic/offline, no new dependency or threshold/verdict changes.
## Key entities
Parse result:format YEAR, anchor date, annual precision. Parse failure:tried formats,
format match counts, suggested format(s), incompatible examples retained.
Annual period:calendar year; source keys uniquely identify one row per period.
## Success criteria
Synthetic annual profile/panel run end-to-end and survive saved/render validation;
no spurious January/weekday analyses; an ordinary numeric decoy stays numeric.
Failed declarations are explainable from the report and stderr. Full extras suite
passes after final records; screenshots reviewed offline.
## Assumptions / narrower scope
YEAR is explicit only. Strings are four ASCII digits after trimming (0001..9999);
integers must have four digits; booleans/floats rejected. Panel retains0002..9997
bounds and ISO window bounds. No automatic aggregation of candidate/entity rows,
no inference that absent years were observed zeros. No new temporal target association.
Yearly totals cannot resolve within-year seasonality. Existing non-YEAR auto grains
are unchanged. Stack on #28 only for the annual-precision edge coverage interaction.
