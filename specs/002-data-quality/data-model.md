# Additions to the saved profile

Existing fields/findings remain. No raw rows are added to the artifact.

- `dataset_summary`: measured counts/shares, inferred-type counts, duplicate and
  lockstep groups, constant/near-constant names, and per-figure finding links.
  Shares are null for a zero denominator. Duplicated-column count is redundant
  members beyond the first; lockstep count is separately reported with named groups.
- `quality`: rule descriptions, screening counts/limits, bounded pattern evidence,
  redundant/near-constant exclusions and candidate missingness contrasts.
- Findings retain id/kind/message/generator/evidence/uncertainty/provenance. Optional
  `rule`/`columns` fields support deterministic view grouping and traceability.
- `selection`: retains target/budget/selected/excluded; adds ranking_rule and ranked
  candidates with focus/strength/count/method and selected or omission reason.
- Existing `bivariate` list also holds selected `missingness_by_group` results with
  group sizes/missing counts/rates and observed spread. This is FT-R2 evidence,
  not a new general target measure. Total entries <=pair_budget.
- Summary view groups are derived from original findings only; artifact findings
  are never discarded to make the HTML readable. Repeated type and meaning groups
  list affected columns and link to their complete original items.

When additive fields are present, validate required types/nonnegative counts,
shares in [0,1] or null, and summary finding links resolving to unique finding IDs.
Without them, legacy rendering labels unavailable measurements explicitly.
