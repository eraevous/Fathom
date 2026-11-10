# Data model (additive, schema 2)

`bivariate[i].type_pair` (absent on missingness-by-group pairs and on old artifacts):

| Field | Type | Notes |
| --- | --- | --- |
| pair_type | str | numeric×numeric, category×numeric, binary×numeric, category×category, binary×binary |
| roles | list[{column, role, levels?}] | role numeric/category/binary; binary carries its two levels in sort order |
| binary_rule | str | R1 wording |
| n | int | complete cases |
| measures | dict | per pair type, see below; every numeric measure that is null has a `<name>_status` reason (validated) |
| groups | list | grouped pairs: {value, n, median, q1, q3, iqr, mean} |
| table | dict | category/binary pairs: {row_column, column_column, row_levels, column_levels, counts, other_row_levels, other_column_levels, shown_cap} |
| wording | dict | {measure, magnitude, near_zero, rule} |
| chart | dict | target_chart (title, note) / group_box (title, labels, scale, data rows with five-number box) / heat_table (labels, counts matching labels); kind must suit the pair type (validated) |
| basis | str | descriptive-only disclosure |

measures by pair type:
- numeric×numeric: pearson_r, spearman_rho, rank_linear_gap, disagreement (bool), disagreement_rule
- category×numeric: eta, kruskal_wallis_h, eta_squared_h, groups_k
- binary×numeric: rank_biserial, index_level, reference_level, median_difference, mean_difference
- category×category: cramers_v, cramers_v_bias_corrected, rows_k, columns_k
- binary×binary: odds_ratio, odds_ratio_correction, risk_difference, phi

New finding: `pair-{i}-type`, kind observation, generator rule:type-pairs-v1,
rule type_pair_association, columns [left,right], evidence path
`bivariate.{i}.type_pair` (value = the block without chart), gate = wording rule.

## Closed shape (validator contract)
Every object inside `type_pair` (and the evidence copy in `type_pair_association` findings) is
validated against a closed field set: unknown keys are rejected on load. Every nullable value
(measures, `wording.magnitude`, group statistics) must be present; null is accepted only with a
`<name>_status` reason. Adding a nested field therefore means updating the producer
(`type_pairs.describe`), the allowlist, the validator and the tests together. This is a validation
rule within the additive schema 2 block; it does not decide schema 2 versus schema 3 (Zach's
decision, research R7).
