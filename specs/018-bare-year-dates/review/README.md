# Bare-year acceptance and visual review

Synthetic input only:52 rows =13 years (1976–2024 at four-year intervals) ×2 entities
×2 candidate keys. Values/codes are authored formulas, not a real metric or election
return. The relayed public table was not accessed.

## Validation

Full extras suite after all records and final code: **411 passed / 2 frozen legacy-AEC
snapshot skips**, pinned Telosmith0.5.24 focused cases pass. Initial21-case run had
13 failures and8passing invalid/numeric decoys; three later controls cover strict
panel formats/keys, configurator parity and ambiguous-format ties. Format-evidence,
caption and malformed-format regressions were additionally demonstrated red before
correction within those cases. No claim every assertion was individually shown red.

The complete existing offline suite passes. Annual profile/panel commands produce
identical files/stdout/stderr with every socket denied. Actual PDF/PPTX annual exports
also match normal versus socket-denied bytes, including their report/status files.
No new runtime dependency or network client. No threshold/verdict change.

AEC: **0 errors / 100 inherited warnings**,5,536edges/72files/0skipped. Structural
impact vs parent80ee25d:50affected/74no-status-change/77pointers; these are review
prompts, not acceptance. Requirements hold implemented_by, claims depends_on and
evidence supports the exact claim. followup(raw) is empty; parent ledger exact
prefix retained; protected docs/decisions unchanged.

## Found and preserved

- Before:explicit temporal without a format gives52invalid years and no useful parse
  advice. After:invalid count stays52, but report/CLI name tried formats and YEAR's
  52/52syntax matches. Suggested action is separate from observation, with structured
  format counts as evidence. Nothing is coerced or silently retried.
- With explicit YEAR:52valid/0invalid,1January anchors labelled as annual precision.
  Year charts remain annual; no weekday/month/quarter patterns or Jan1placeholder
  findings are invented from anchors. Existing day-tick caption is no longer shown
  on year charts. Year-looking numeric/code columns remain numeric when undeclared.
- Profile sample explicitly sums both synthetic candidates within each entity/year.
  It has49annual calendar periods,13observed/36missing. The panel keeps all4 entity×
  candidate series separately:13observed/36absent,0observed zeros in each. First/last
  annual periods are complete at YEAR precision, not one-day Jan1stubs.
- General YEAR parser accepts four ASCII digit strings and four-digit integers;
  bool/float/0000/10000/partial years reject. Common/leap calendar arithmetic reused.
  Default ISO auto analysis remains hour/day/week/month; YEAR auto is year only.
- Reverse-format, no-match, partial-failure and ambiguous-format decoys retain raw
  invalids/unknowns. Tied recommendations are not resolved as domain knowledge.
  Duplicate entity/year keys fail; candidate rows are never silently aggregated.

## Actual screenshots

14actual offline Chromium screenshots. [Checks](checks.json):zero resource requests
and document overflow on monitored desktop/phone views; dark-phone failure smoke.
Configurations used for screenshots are [failure.yaml](failure.yaml) and
[profile.yaml](profile.yaml); metadata declares the known synthetic purpose explicitly.

[Before failure head1280](before-failure-head-1280.png) / [after1280](after-failure-head-1280.png)
/ [after390](after-failure-head-390.png) / [dark390](after-failure-dark-390.png).
[Annual head1280](annual-head-1280.png) / [390](annual-head-390.png).
[Annual dictionary1280](annual-column-1280.png) / [390](annual-column-390.png).
[Annual structure1280](annual-structure-1280.png) / [390](annual-structure-390.png).
[Panel head1280](panel-head-1280.png) / [390](panel-head-390.png).
[Panel details1280](panel-details-1280.png) / [390](panel-details-390.png).

Visually inspected failure advice, annual chart/anchor precision, and phone panel.
Fixed the inherited day-tick caption on year charts. Existing wide temporal tables
still need local phone panning; no new Office layout/native chart feature.

## Narrower readings and open limits

Stack on #28 is necessary for annual precision in its partial-edge calculations.
YEAR is explicit; it does not choose series keys, invoke panel, or infer absence as
an observed zero. Years between four-year observations remain absent/missing.
Native annual totals cannot resolve within-year seasonality. Panel windows remain
ISO inclusive dates; existing panel0002..9997bounds remain. General parser0001..9999;
series year9999 end boundary is skipped with a reason rather than overflowing.

Temporal target association remains unsupported; the exclusion now points to declared
time_series or guide panel. No new predictor/model is added. Syntax matches are not
semantic acceptance. Inferred descriptions retain existing name heuristics; declare
metadata for known purpose (as these synthetic screenshot configs do). Strict ISO
interval semantics are unchanged. No private/held-out usefulness claim.
