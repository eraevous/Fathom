# Artifact additions (version1)

purpose/config persist group_by and columns.exclude_from_target. target_analysis:
status active/skipped, reason, target, ranked rows (column, method, value, strength,
n, selected), exclusions/reasons, grouping policy, selected relationship charts and
within-group summaries. Empty/no-target carries explicit skip reason. Older artifacts
without the field report unavailable legacy target detail, not silently recompute.

Each budgeted bivariate pair may add measure/association and group_summary; shared
selection still owns actual chosen count. Each group: value,n,share,valid,missing,
missing_share,small, numeric statistics or category rates,rest contrasts. Evidence
links target_analysis summaries/ranked rows, generator rule:target-v1. All finite
metrics ornull. New chart kinds scatter/group_box/rates carry raw coordinates,
scale descriptors and coverage; univariate log ECDF retains transformed x positions
and explicit positive-only coverage. Validators bound<=200scatter points,20groups,
20levels; selected pair count stays<=budget, plot count<=selected pairs.
