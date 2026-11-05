# Feature Specification: Partial-period and type disclosure
Created2026-11-05; provisional. Serves:P0@2,DG-RA@1,DG-RB@1,DG-RE@1,FT-DEMO3-R1@1.
Input:HO-DG-20261105-E4V9 item3. Independent main ad16fe6; PR26/27 listed first.
## User Scenarios & Testing
### US1 — Recognize partial edge totals (P1)
First/last period rows flag timestamp-span coverage below the calendar period length.
Amplitude summaries that include these totals say so inline, including a monthly
stub of roughly31minutes. Existing values, signals and thresholds remain unchanged.
Acceptance: synthetic cross-month timestamp stub and full date-only calendar decoy;
first/last in one bucket, leap month and zero-event state preservation.
### US2 — Read time and type scope correctly (P1)
When hourly analysis is declared, the dictionary/unknowns never claim the report
excludes time of day. Date-only univariate summaries are distinguished from the
hourly analysis. High-cardinality strings get a one-line option to declare categorical,
without automatic recoding or a promise to bypass grouping caps.
Acceptance: declared-hour fixture and no-declaration decoy; high-card string and
ordinary category decoy, HTML/Markdown/configuration page.
## Requirements
FR1:Explicit first/last timestamp-span coverage and partial flags, with calendar
period duration. FR2:Inline partial-edge amplitude caveat, not changed calculations.
FR3:Qualified date-only scope for hourly declarations. FR4:Categorical hint for
string columns beyond the existing20-level categorical-inference cap.
FR5:Offline self-contained, deterministic, no new dependency/rule/threshold.
## Key entities
Edge coverage:period, first/last/both, covered interval/seconds, period seconds,
share and partial flag. A timestamp span is not an observation/exposure declaration.
## Success criteria
A reader sees a stub next to affected amplitude stats; hourly wording is consistent;
all old numerical and signal tests still pass. Actual1280px before/after and phone
screenshots; synthetic and pinned public tables reviewed.
## Assumptions
Use [first timestamp,last timestamp plus its lexical resolution) as the measurable
span:date=day, minute timestamp=minute, second timestamp=second. It is not proof of
continuous observation. No extrapolation/rescaling or exclusion changes. A single
bucket has one edge marked both. Calendar month/week lengths use existing rules.

Main #26 merged during finalization; the related small-group caution now spells out valid n<5 inline (item1 presentation only).
