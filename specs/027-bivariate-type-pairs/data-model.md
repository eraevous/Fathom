# Data model (additive, schema 2)

`bivariate[i].type_pair` (absent on missingness-by-group pairs and on old artifacts):

| Field | Type | Notes |
| --- | --- | --- |
| pair_type | str | numeric×numeric, category×numeric, binary×numeric, category×category, binary×binary; must equal what the two roles classify to |
| roles | list[{column, role, levels?}] | role numeric/category/binary; binary carries its two levels in sort order |
| binary_rule | str | R1 wording |
| n | int | complete cases |
| measures | dict | per pair type, see below (all required for that type); a null numeric measure always carries `<name>_status`, a reason string ("not estimable: …" / "undefined: …") that the measure table shows in place of the value |
| groups | list | required for grouped pairs only: {value, n, median, q1, q3, iqr, mean}; 1–20 entries, distinct values; binary×numeric has exactly the binary role's two levels |
| table | dict | required for category×category and binary×binary only: {row_column, column_column, row_levels, column_levels, counts, other_row_levels, other_column_levels, shown_cap, basis}; counts shape matches the shown levels plus an "other" row/column |
| wording | dict | {magnitude (number or null), near_zero, rule} |
| chart | dict or null | kind target_chart {title, note} (numeric×numeric and grouped pairs whose numeric side is the target), group_box {title, note, x_label, y_label, x_scale, n, total_rows, data[{label, n, excluded_nonpositive?, box{min,q1,median,q3,max} ordered or null}]} (grouped pairs), heat_table {title, note, x_label, y_label, n, total_rows, row_labels, column_labels, counts} (category and binary pairs) |
| basis | str | descriptive-only disclosure |

measures by pair type:
- numeric×numeric: pearson_r, spearman_rho, rank_linear_gap, disagreement (bool), disagreement_rule
- category×numeric: eta, kruskal_wallis_h, eta_squared_h, groups_k
- binary×numeric: rank_biserial, index_level, reference_level, median_difference, mean_difference
- category×category: cramers_v, cramers_v_bias_corrected, rows_k, columns_k
- binary×binary: odds_ratio, odds_ratio_correction, risk_difference, phi, index_levels, reference_levels

Nullable measures and their status reasons: pearson_r, spearman_rho, rank_linear_gap, eta, kruskal_wallis_h,
eta_squared_h, rank_biserial, median/mean_difference, cramers_v, cramers_v_bias_corrected, odds_ratio, risk_difference, phi.
An empty row or column of the 2×2 table makes odds_ratio, risk_difference and phi all null with the same status.

Validation (`type_pairs.validate_type_pair`, run by ProfilingResult) rejects any block that breaks this table,
so a saved artifact that loads also renders (PR #41 review).

New finding: `pair-{i}-type`, kind observation, generator rule:type-pairs-v1,
rule type_pair_association, columns [left,right], evidence path
`bivariate.{i}.type_pair` (value = the block without chart), gate = wording rule.
