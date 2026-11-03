# Builder acceptance: target analysis and FT-R19

Checked against docs/acceptance.md on authored planted/clean/late and pinned public
tables. This is builder evidence, not Zach/Kate's deliberately unseen acceptance.
Core implementation preceded the late fixture; no domain defect verdict is inferred.

## Measures and selection

Pearson r retains signed linear correlation; ranking uses absolute r. Correlation
ratio eta measures numeric variation between categories. Unadjusted Cramer's V
measures category/category association. These simple core measures require no fitted
model/new runtime dependency. Cramer's V can be inflated by sparse/high-cardinality
tables. Unlike measures share a priority heuristic, not a calibrated effect scale.
Existing optional Pearson p-values remain after selection, never choose candidates.

Existing target routes were extended, quality contrasts retained under the same
pair_budget. All eligible target columns get light candidate scores; only selected
pairs get detailed group summaries/plots. Numeric-target group reservation is explicit;
no unbudgeted group×every-column or target-versus-two-predictor work. Continuous unique
numbers remain eligible; known leaks can be configured out. Arbitrary leaks and valid
predictors cannot be distinguished from observed correlation alone.

## Found and missed

| Table | Report alone finds / consequence | Missed / noise / limits |
| --- | --- | --- |
| target/planted.csv40x7 /planted.yaml, budget3 | group eta0.918643(n40), signal r0.689275(n40), other r0.074596(n38). Known target-rank leak excluded by config, raw copy excluded, unique record_id excluded. Small group3/40rows(7.5%) has target mean/median2903 versus regular mean524.5 across37rows; explicit n<5caution, rest counts and review actions. Three selected pairs/plots. | The missing values of other inside the small group are not summarized under group: this slice's group summaries are pair-local, not every selected column under group. Overall other missingness is visible. The known leak requires supplied exclusion metadata; no automatic arbitrary leakage detection. Mean contrasts flag both sides of the same two-group difference. |
| target/clean.csv40x7 /clean.yaml | Balanced numeric/category decoys: signal r0, group eta0.018983, other r0.042448. No marked target-group contrast. Copy/ID/configured-rank screening remains. | Generic selected-relationship review actions remain even for weak relationships; no claim of significance/usefulness merely because a pair is selected. |
| target/late.csv24x5 /late.yaml | Categorical-target ranking: hidden_signal eta1(n24), sometimes_missing V1(n22), predictor V0.957427(n24); decoy eta0 beyond budget. Category rates show complete separation of hidden_signal bins; empty bins explicit. Summaries show category-specific rates and missing counts; review actions name observed differences. | hidden_signal is an authored0/1target encoding and remains eligible: unmarked leakage is deliberately missed. sometimes_missing is an incomplete copy and also remains ranked (row agreement22/24 below95%near-copy threshold). The rare predictor level2rows is visible in group-rate plotting, but grouping is the categorical target, so no separate rare-level-rest finding. Sparse group/rate effects are descriptive. |
| polish/movies.csv3201x16 /target/movies.yaml | Five selected relationships: US Gross r0.939742(n3194), US DVD Sales r0.702271(n564), Production Budget r0.665780(n3193), IMDB Votes r0.551564(n2983), Major Genre eta0.369321(n2925). Genre summaries flag Adventure mean241,171,386 vs rest76,434,662 with counts274/2652 and review action. Eleven eligible ranking rows, explicit exclusions/remaining budget limits. Positive log ECDF3147values/47zeros with original-unit ticks. | No domain ground truth or causal claims. Dates/text/special types are unsupported for association unless re-declared. Some scatter cases excluded for positive-log plotting and samples bounded200; counts disclosed. Rank-spaced sample may miss individual outliers. Domain overlap/leakage cannot be resolved from the table. |
| polish/college.csv173x21 /target/college.yaml | Five selected: P75th r0.901923, P25th r0.891683, Rank r-0.873308, Major_category eta0.756430, ShareWomen r-0.618690(n172; others173). Engineering mean57,383 vs rest36,681, counts29/144 with review action. Eighteen ranked candidates and exclusions. | Rank remains a numeric candidate; a derived/undesired rank needs human exclusion. No assertion it is safe for prediction. Correlation ignores nonlinear relationships. Independent source meanings, target timing and sampling assumptions remain unknown. |

Report-alone consequence: the analyst can identify which relationships merit context/
leakage review, see sample loss and small-group caveats, and investigate a shifted
small group before treating its pattern as stable. Standalone documentation retains
inferred semantics, dictionary/provenance and unknowns; no automated causal story.

## Verification / authority

164tests pass with extras; core157pass/7optional skips. Hand calculations cover
signed Pearson, eta0/1 and V0/1; tests cover exclusions, reservation/order/budget,
small groups/missingness, category rates/empty bins, skip/legacy/config rejection,
artifact tampering, log ECDF and200-point scatter coverage, native log-axis markup
and independent optional exports. Existing tests remain valid; no old tests removed.
Fresh processes verify identical HTML/Markdown/PDF/PPTX/status bytes in summary and
full modes. See [visual pass](review/README.md) for all4FT-R19 dispositions and actual
HTML/PDF/PowerPoint1280/390 images, limits, practice comparison and reproduction.

Spec/plan/intent and FT-TA-R1@1 preceded code. All implementation choices remain
provisional; a merge/test does not accept them. PR#14's authorized duplicate FT-R18
removal is inherited unchanged, not repeated by Codex. Existing record bytes and
protected docs/decisions are verified against3b89d7c. PR#14 rebase waits for merge;
no main push, force push or PR merge is performed.

AEC final: **0errors/0warnings**,2117edges from33files. Impact reports23affected
conclusions (7stale requirement links/16review flags),45unaffected. New FT-TA evidence
covers current behavior; old records remain historical. Structural flags do not
accept or reject requirements. Authored7records:FT-TA-R1@1/@2 (provisional),
FT-TA-C1@1,FT-TA-V1@1,FT-TA-E1@1–E3@1. Review has63screenshots with hashes.

Field-naming limit: within-group numeric/boolean "missing" counts unavailable after
effective-type parsing, including incompatible values as well as raw blanks. A
separate per-group invalid count is not supplied; raw column invalid totals/evidence
remain in the dictionary/artifact. The committed planted tables do not exercise
mixed-invalid group cells; this is a disclosed narrower reading, not a tested claim
that all unavailable cells were literally empty.
