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
  Poisson MAE uses mode-centered recurrence; cap mean at100000, relative tail
  tolerance1e-14; label numerical tail approximation. No normal approximation.
- Slice source into training/evaluation before view construction, and mark edge
  buckets incomplete. Sum/mean are explicit rules; observed exposure sums, never averages.
- Metrics are generic declared names; no definitions/directions inferred. Missing
  keys stay visible; delimiter-free tuples preserve leading zeros.
- No volume defaults or user-specific constants. SBC cutoffs are methodological
  classification rules, not declared volume boundaries. All readings provisional.

