# Feature Specification: Offline panel signals
**Branch**: 014-offline-panel-stack | **Created**: 2026-11-05 | **Status**: provisional for Zach.
Serves: P0@2, DG-RA@1, DG-RB@1, DG-RC@1, DG-RD@1, DG-RE@1, DG-RF@1, FT-R17@2.
Proposed: FT-PANEL-R1@1, FT-PANEL-R2@1.

## User Scenarios & Testing
### US1 — Keep data local (P1)
Every command completes with socket creation blocked, producing identical files/stdout.
Offline installation uses prebuilt wheels with no index. Generated reports/configuration
pages request no external resources. An intentionally networking probe fails the harness.
### US2 — Understand a declared panel (P1)
An analyst declares series keys, time, value and calendar period. Outputs distinguish
observed zero, missing measurement, absent calendar period, closure and unequal exposure.
A windows file produces one series/model/window row; signals use training only.
Changing evaluation data cannot change any training signal, even in aggregate views.
### US3 — Compare declared views and metrics (P2)
Declared volume thresholds show observed training/evaluation volume, normalized volume,
side, signed distance and disagreement with missing-coverage reservations. Separate
week/month and optional cross-series views retain lineage/state counts. Metric joins
use complete composite keys; unmatched keys are listed; metric pairs have Spearman,
row and unique-series counts overall/by declared volume bands/by SBC, never failure labels.
### Edge cases
Empty data, malformed dates/counts/exposure/states, duplicate periods/window/metric keys,
leading-zero and hostile names, absent/closed-only/all-zero/constant series, non-count
values, unequal exposure, boundary buckets, missing metrics, tied ranks, short histories,
leap years, invalid config, unsupported seasonal grains and optional extras absence.

## Requirements
- FR-001: Block every socket constructor during fresh-process command tests; compare all
  bytes. No data may leave the machine. Fathom code imports no network clients;
  unused imports inside existing optional serializers may remain. All eight commands
  are covered on the authorized liftoff stack. No connector/network feature.
- FR-002: panel command writes series-signals.csv, panel.json, panel.html and panel.md;
  artifact is the authority. Strict declared local CSV roles, ISO dates, nonnegative
  finite values; at most one source row per series/calendar period. No inferred roles.
- FR-003: Preserve calendar/state/exposure counts and signal-specific eligibility.
  Missing/absent/closed/ineligible periods break runs and positive-gap chains.
- FR-004: Duration reports span, usable observations, observed exposure and regime age
  (not estimable in this slice, no inferred changepoint). Amplitude reports mean/zero
  share/positive mean/positive population CV²/sample dispersion-to-mean/mean per summed
  exposure/IQR, with explicit undefined denominator states.
- FR-005: Wavelength reports complete calendar cycles and descriptive adjusted phase
  strength for week/month/year where supported and at least three complete cycles;
  no significance or causal claim. Frequency reports coverage, classic SBC ADI,
  positive probability, zero/missing runs, positive-gap variability and spec011-style
  gap mean without crossing unavailable periods.
- FR-006: SBC uses disclosed classic ADI and positive CV² rules. Unequal exposure
  prevents comparable-exposure SBC/seasonal/noise estimates. Poisson/NB2 floors are
  model-conditional training estimates for integer counts, never fitted forecasts.
  Poisson median absolute error uses deterministic bounded probability summation.
- FR-007: Windows are inclusive, nonoverlapping training then evaluation ranges.
  All signal estimators see training only; evaluation is used only for volume/threshold
  context. Volume thresholds have no defaults; values occur only in synthetic fixtures.
- FR-008: Requested aggregate artifacts are generated independently after splitting
  windows; source/rule/state/exposure lineage retained. Incomplete buckets remain
  unavailable for signal estimation, retaining their known subtotal. Compare SBC and
  threshold sides with corresponding native rows. No general transformation engine.
- FR-009: Metrics have declared columns and unique series/model/window/horizon keys.
  Count/list unmatched keys on both sides. Preserve left rows. A metrics-only horizon
  explicitly expands a base signal row by observed horizons; never many-to-many.
  Run joined data through existing profile for each declared target metric.
- FR-010: Disagreement pairs are only declared metrics (at most twelve); average tied
  ranks, pairwise finite values, overall/declared volume bands/SBC, with row and distinct
  series counts. Repeated rows are not independent; metric direction is not inferred.
- FR-011: Fixed seeds; synthetic violating/clean cases; script-free escaped new HTML
  reviewed at1280/390 light/dark. No dependency beyond existing stdlib/pandas.
## Key Entities
GuideDataFrame; panel declaration; calendar period with orthogonal state/exposure flags;
window; signal row with typed values/status/denominator; aggregation lineage; metric key;
disagreement row; versioned ProfilingResult kind panel.
## Success Criteria
All eight commands are byte-identical under socket denial; evaluation perturbation
leaves training signals unchanged; exact planted counts/joins and decoys pass;
every unavailable estimate has a reason; every aggregate preserves constituent
state counts; HTML is readable without external resources.
## Assumptions / Clarifications
Panel values are nonnegative quantities; noise distributions require integers.
The calendar is declared and dates are timezone-free. No imputation. Windows outside
available data remain absent, not zero. Native period rows are unique; reject duplicates.
Optional regime estimation is omitted explicitly. See contracts and research for
provisional algorithm/cap readings. No forecasting, data-specific interpretation or
accepted thresholds. The user authorized stacking on PR23; its reconciled97648e0 includes main498a50b.

### Offline clarification (2026-11-05)
Loopback may be used only if a future authorized feature needs it, with safeguards
against web access and binding only to 127.0.0.1/::1/localhost, never 0.0.0.0. This slice
adds no server or network feature and needs no loopback: the test denies all socket
creation and proves no attempt, which is stronger than blocking non-loopback alone.
Unused network-client imports inside existing optional serializers are allowed;
Fathom's own code imports none. Every command, including exports, runs under the
same socket/Request audit and produces identical bytes. HTML requests no resources.
