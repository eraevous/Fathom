# Research / resolved readings
- Reuse GuideDataFrame, ProfilingResult and existing profile target analysis. Add a
  panel discriminator rather than a parallel renderer interface. Panel is a declared
  long-data route; existing wide profile behavior stays unchanged.
- Preserve absent/missing/closed separately. Unequal exposure is orthogonal; it is
  not a zero/missing state. Raw moments describe usable measured quantities; comparable
  exposure SBC/seasonal/noise estimates are withheld if exposures differ.
- ADI = usable periods / positive periods for SBC. Also report contiguous positive-gap
  mean from spec011; unavailable periods break those gaps. Do not silently conflate them.
- Seasonal strength is adjusted phase explained variance, clamped to0..1; it is a
  descriptive in-sample measure, not a significance test. Require three fully eligible
  calendar cycles and repeated phases. Daily supports all cycles; monthly supports year;
  weekly supports year only when complete ISO years exist. No fixed-length month/year.
- Regime age is not estimable: no accepted changepoint rule. No forecast models.
- Count floors: Poisson training mean; NB2 sample-moment k only with excess variance.
  Poisson MAE uses mode-centered recurrence; cap mean at100000, relative mass
  cutoff1e-16 (no asserted numerical error bound); label numerical tail approximation. No normal approximation.
- Slice source into training/evaluation before view construction, and mark edge
  buckets incomplete. Sum/mean are explicit rules; source observed exposure sums are retained; mean views apply the same mean operator to value and exposure, changing their units.
- Metrics are generic declared names; no definitions/directions inferred. Missing
  keys stay visible; delimiter-free tuples preserve leading zeros.
- No volume defaults or user-specific constants. SBC cutoffs are methodological
  classification rules, not declared volume boundaries. All readings provisional.


Reviewed refinements: calendar cycles covered and complete eligible cycles are distinct;
missing, absent and their combined unavailable runs are separate. Source known exposure
is retained independently of usable exposure. Volume retains partial-bucket known
quantities even when the bucket is ineligible for signals. Cross-series windows must
align to preserve unambiguous keys. Metric correlations need at least three distinct
series, alongside their repeated-row counts.

Mean-generated views withhold count-distribution floors even when their averages
happen to be integers. Both training and evaluation boundary-side changes are listed
in view comparisons. Restored panel artifacts reproduce all report/CSV bytes.

Final review removed repeated technical estimator notes from analytical CSV columns;
values/statuses remain, with full context in the artifact. The target-analysis table
is the exported joined table, with identical CSV blank handling and verified target
payload equality. This avoids treating empty explanatory notes as data-quality gaps.
