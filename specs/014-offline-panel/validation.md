# Validation: offline panel signals
HO-DG-20261105-AW0D. Spec/plan/tasks and provisional requirements precede code.
Final branch is stacked on PR #23 at 97648e0, which includes main 498a50b/Telosmith.
Kate reviews first; Zach merges. No requirement accepted.

## Tests and offline contract
**373 passed** with existing extras; **362 passed/11 optional skips** with core.
40 panel cases and15offline cases; affected panel/offline family55passed after the
final presentation adjustment. Initial panel tests failed at import before the
module existed; malformed/alignment/evaluation-side/mean-floor/saved-render and
swallowed-network regressions separately failed before their corrections. Do not
read this as all 40 individually demonstrated red.

Every command: profile,render,compare,validate,export,configure,liftoff,panel.
Fresh-process audit is installed before Fathom imports and rejects every socket
constructor/operation and urllib Request; caught attempts still fail at process exit.
All output bytes/stdout/stderr match the normal run, including available PDF/PPTX.
Fathom code imports no network clients. Per the user's clarification, unused imports
inside existing optional serializers are allowed, scoped by importer stack; the
independent socket audit is never relaxed. Direct-import and socket positive controls
demonstrate the guards. No loopback is needed or server added; blocking all sockets
is stronger than the allowed safeguarded-loopback rule.

The deep panel command includes week/month views, windows, metrics/horizons and
existing target reports; hash seeds 1/99 match all files. Saved panel artifacts render
to identical HTML/Markdown/CSVs. Static resource checks and actual offline Chromium
requests are empty for panel/views/targets/configure/liftoff. No CDN/font/image requests.

Connected wheel build prepared 7 core wheels. In a fresh venv, no-index installation
under socket denial succeeded; its installed guide panel produced 10 series. README
documents matching-platform wheelhouse preparation and target installation. Optional
extras retain existing clean degradation. No new runtime dependency.

## Synthetic truth and found/missed
Committed generator seed 20261105 and truth.json; no real or held-out data used.
These are descriptors/conditional estimates, not causal diagnoses or model selection.

| Fixture series | Found in report | Miss / reservation |
| --- | --- | --- |
| low_poisson |155 observed zeros/240; training Poisson mean/floor 0.38333; intermittent SBC | Does not establish the generating distribution |
| overdispersed |87 zeros/240; NB2 moment k 0.7286; conditional squared floor 9.4693; lumpy SBC | Excess variance is not proof of NB2 |
| bursts |232 zeros and8positive periods/240; positive size 20; ADI 30 | No burst cause inferred |
| closures |12 closed/84calendar periods,72 usable;0 observed zeros | Known closures excluded, not converted to zeros |
| missing |10 missing measurements and5absent periods;69 usable/84; known exposure 79 versus usable69 | Missingness mechanism unknown |
| regime | Training descriptors and24observed zeros/120 | **Regime boundary/age intentionally not estimated**; explicit not-estimable state |
| weekly |12complete weekly cycles; adjusted phase strength 1 | Descriptive in-sample strength, not significance |
| annual_short |1complete year; strength not estimable | Not called absent |
| annual_long |3complete years/1,096 days; adjusted annual strength 0.99952 | Leap-only singleton phase omitted/disclosed |
| exposure |84 usable; exposure 126; rate 3; unequal exposure flagged | SBC/seasonal/count floors withheld |

Clean/constant/zero/non-count/short/balanced and missing-gap decoys are in tests.
Exact Poisson MAE at mean 1 matches2/e; mean 1000 remains finite; beyond-cap values
are explicitly not estimable. NB2 sample-moment hand calculation and all four SBC
classes pass. No score or forecast model.

## Windows, views and metrics
Evaluation-only perturbation changes no training dimension, SBC class or noise
estimate, including midweek/month boundaries. Slice first, aggregate second.
Partial/unknown buckets retain state counts and known subtotal but do not enter
signal estimates. Sum views retain observed quantity; mean views change units and
withhold count-model floors even if means are integers. Source exposure totals are
retained independently. Cross-series windows must align; duplicate keys fail.
View comparison covers native/each requested view and week/month, including both
training and evaluation boundary sides.

Synthetic joined fixture:40 signal window rows; horizon expansion gives79left rows
(78 matched plus 1 unmatched signal).1 unmatched metric key is listed.51 disagreement
rows; overall metric_a/metric_b uses78pairs across 10 distinct series, rho-0.9719.
Constant metric_c comparisons are not estimable. Overall pooling and per-model/
window/horizon slices are explicit; repeated rows are not independent. At least
three distinct series required. Leading-zero keys, tied ranks, exact duplicates,
missing metrics and output escaping tested. Chosen metrics reuse existing profile
target analysis; no metric direction/definition/failure threshold inferred.

## Visual review and limits
[28 actual screenshots and issue ledger](review/README.md),1280/390 light/dark.
Fixed split numbers/headers, compact default row summaries, full-width volume tables,
explicit coverage and technical disclosures. Shared palette; no page overflow.
Wide tables still need local phone scrolling; open evidence/target reports can be long.
No new panel PDF/PPTX exporter, panel GUI/server, timezone parsing, generic aggregation
engine or changepoint estimator. ISO dates, unique native periods and nonnegative
values are narrower readings. Generated week/month views require daily source.
Caps/errors/methods are in plan/contracts and artifact rules. Volume bounds have no
defaults and occur only in authored synthetic fixtures.

Protected documents/docs/decisions and the parent ledger prefix are unchanged.
FT-PANEL records remain provisional. Telosmith output is structural, not acceptance.
