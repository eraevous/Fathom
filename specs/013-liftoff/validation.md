# Liftoff validation (HO-DG-20261104-36XP)

PartA was already completed upstream: main7e5fa43 includes #16 and #19–#21;
#22head21b9896 is an ordinary reconciliation merge. Spec013 branched from21b9896;
no new integration branch/merge/rebase/squash/force was performed. The original
records-link stack was not reopened or DEC-021 replayed. Kate reviews this PR first.

## Tests and artifact contract

Baseline286pass on pandas2.2.3/Python3.12. Initial13new cases failed before code;
expanded22liftoff cases pass, including clean/constant/short/rate/size decoys.
**Full308passed; core297passed/11optional skips.** Existing tests retained.
Optional spectral absence explicitly says not computed; report/Brief remains usable.
No new dependency. The only warning in the extras run was an external pytest plugin
deprecation, not an AEC finding.

Default profile equality is asserted after removing only the additive liftoff block.
No ordinary declaration/target/selected pair changes; standaloneconfigure remains
compatible. The schema2 saved artifact re-renders to identical liftoff HTML.
Canonical rendering fixes in-memory versus JSON-loaded dictionary ordering.
Hostile markup/prototype names, Python/JS YAML parity, invalid boundary rejection,
CLI validation, no partial failure output and candidate caps have regressions.

Fresh processes with hash seeds1/99 produce identical liftoff JSON/HTML, and identical
**declared** taxis JSON/HTML/Markdown/PDF/PPTX/status. [Hashes](determinism.json).
Existing Office exports are deterministic; new Brief/temporal Office content not added.

## Taxis: report-only found/missed check

Pinned public seaborn-data6433×14, source/hash under tests/fixtures/liftoff/sources.json.
No private/held-out table used. The Brief, not just raw statistics, states:

| Fact | Brief excerpt / rule | Declared check |
| --- | --- | --- |
|6equal pickup/dropoff pairs | **If you declare pickup→dropoff:**6433/6433pairs parsed;0endbefore;6endequal; median654s. `interval` /rule:rows-v1 | Result dictionary exactly equals unchanged row_structure.intervals[0] |
|24hour cycle | **If you declare event counts by pickup(auto):** hour ACF peaks atlag24,r0.552; schedule question. `dominant_cycle` /rule:timeseries-v1 | Entire series result exactly equals declared series; r0.5515768335 |
|Cash-tip zeros | tip0in1812/1812finite cash rows;455/4577elsewhere;44missing payment labels excluded. Is zero structural/unrecorded/literal? `all_zero_group` /rule:liftoff-v1 | Existing selected paymentgroup has1812valid,min=max0; no new stage-two zero sentence |
|19repeat pickups |19rows repeat earlier exactpickup timestamps, with positions. `duplicate_timestamps` /rule:rows-v1 | Same automatic finding in declared report |
|1out-of-month pickup |6432/6433pickups inMarch2019;1outside,row6204,2019-02-28 23:29:03. `temporal_period` /rule:rows-v1 | Same automatic finding in declared report |

The opposite interval direction is also offered/measured conditionally; it has6427
negative durations, not a claim of an input defect. Dropoff independently has2values
outsideMarch and8repeat timestamps. No direction, target, row unit or mechanism inferred.

The actual browser starts with{}, no target/interval/series/type suggestion selected.
Changing granularity alone emits nothing. Selecting pickup→dropoff, pickup events/auto
and targettip, then clicking Download, produces accepted liftoff.yaml and an advisory
manifest whose digest equals its exact bytes. Stage-two interval/series results match
previews exactly; target comparison retains the existing payment-group reservation.
[Browser assertions](review/checks.json), [gallery](review/README.md).

## Authored synthetic truth

- planted.csv: one equal interval, one repeating start,31/31cash zeros versus30/30
  nonzero card values, >30period candidates. All surfaced under correct labels.
- clean.csv: no temporal candidates or zero contrasts; no invented previews.
- periodic.csv:240hours with a24hour event pattern; dominant24lag found; no equal
  interval. constant.csv:120hourly events, undefined ACF (not a positive signal).
- Inline balanced-zero/small-group/small-gap decoys stay quiet; missing labels and
  invalid/missing numeric cells have separate exact denominators. Hostile names
  stay text and series/value declarations survive reserved prototype-like names.

## Limits and questions for Zach

- Provisional computations are the coordinator reading of DEC-079, still proposed
  (FT-LIFT-Q1@1). A suggest-only mode could omit those rows without applying meaning.
- Stage two is unchanged: no new standalone zero-contrast sentence. Existing group
  counts/extrema corroborate the zeros; a new configured zero rule is a separate
  scope question (FT-LIFT-Q2@1). This is an explicit acceptance wording limitation.
- No target ranking/association previews, value/by-series previews, extra lag/group
  controls, timezones, server/dashboard, C-22, AI narrative, Brief/temporal PDF/PPTX
  export or accepted thresholds. Selecting a different value/grain changes the question.
- Interval pairs capped at10(both directions); event previews at20, zero scan10×10
  with20results; all counts/omissions disclosed. Existing time-series caps apply.
- Long forms/complete reports still need scrolling; exact wide tables scroll locally;
  fixed exports need phone zoom. User meaning and independent usefulness remain open.

AEC check:0errors/0warnings,4261edges/56files,0skipped. Purpose-link references all
resolve. Post-implementation impact against regenerated21b9896snapshot:22affected,
84unaffected(structural prompts, not acceptance). Existing records/decision files and
protected documents verified unchanged; only appended FT-LIFT records.
