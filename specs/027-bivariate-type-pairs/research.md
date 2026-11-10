# Research

R1 Binary rule. Decision: a column is binary in a pair when its non-missing values,
parsed for its effective type, have exactly two distinct values (whole column, not
just complete cases, so the role does not change with the partner). Includes 0/1
and other two-valued numerics, true/false, two-level categories. Disclosed in each
`type_pair.binary_rule`. Alternative (only 0/1 numerics) rejected: two-valued codes
such as 1/2 are the same shape. Risk: a two-valued measurement is read as binary;
the screening measure (Pearson) is kept alongside, so nothing is lost.

R2 Spearman rho: Pearson correlation of average tied ranks (textbook definition with
ties). Disagreement note when |rho| and |r| differ by at least 0.2, or have opposite
signs while both are at least 0.1 in absolute value: wording that points at monotone non-linear shape or influential values.
The 0.2 is a disclosed wording cut, not a test. Open question for Zach.

R3 category×numeric: eta stays (mean-based, sensitive to outliers). Added the
Kruskal-Wallis H (tie-corrected) as a descriptive statistic and rank eta-squared
η²_H = (H − k + 1)/(n − k) (Tomczak & Tomczak 2014), which is roughly zero for
independent columns, unlike eta and H/(n−1) whose null expectation grows with k/n.
No p-value. Alternatives: epsilon-squared H/(n−1) (biased upward), omega-squared
(mean-based, same weakness as eta). Per-group n/median/Q1/Q3/IQR/mean use the
existing percentile rule.

R4 binary×numeric: rank-biserial r = 2(R̄₂ − R̄₁)/n (Glass 1965), equal to
P(Y₂>Y₁) − P(Y₂<Y₁) with average ranks; level 2 is the second level in sort order.
Difference in medians and means (level 2 minus level 1) with group n. Cohen's d
rejected (assumes a common SD and is outlier sensitive).

R5 category×category: Cramér's V stays. Bias-corrected V (Bergsma 2013):
φ²c = max(0, χ²/n − (r−1)(c−1)/(n−1)), r̃ = r − (r−1)²/(n−1), c̃ likewise,
Ṽ = √(φ²c / min(r̃−1, c̃−1)). Justified because plain V is inflated for sparse
tables and many levels, which is exactly what the near-zero wording would misread.
Table display capped at 10 levels per side (by count, then lexical), remainder
summed into one "other levels" row/column; measures use the full table.

R6 binary×binary: 2×2 with rows the left column and columns the right column,
both in sort order. a = (L₂,R₂), b = (L₂,R₁), c = (L₁,R₂), d = (L₁,R₁).
OR = ad/bc; when any cell is 0, 0.5 is added to every cell (Haldane-Anscombe) and
`odds_ratio_correction` says so. Risk difference = a/(a+b) − c/(c+d). Phi =
(ad − bc)/√((a+b)(c+d)(a+c)(b+d)). Phi equals Cramér's V in absolute value for 2×2.

R7 Schema. The repo's schema3 is a proposal pending Zach (docs/schema-flattening.md),
so this slice does not bump the version: `type_pair` is an optional additive key
on each `bivariate` item, like `target_analysis` was in spec 007. Validation accepts
it when present and old artifacts without it. Brief asked for a bump if the stored
shape changes; the repo rule (no schema3 before Zach's decision) wins. Open question.

R8 Ranking. Zach's scope keeps "today's budget and ranking", so new measures do not
enter the ranking key; they describe the pairs the existing rule selected. The
brief's suggestion to extend the strength key is not taken (repo/owner wording wins).

R9 Wording rule: headline magnitude on a 0–1 correlation-like scale: max(|r|,|rho|);
√max(0,η²_H); |rank-biserial|; bias-corrected V; |phi|. Below 0.1 → "near zero (no
notable association)". One cut, wording only, no strong/moderate/weak bands. Random
independent data can exceed 0.1 at small n; the finding says so via the uncertainty.

R10 Charts reuse charts.py/target_marks.py: scatter (existing target chart),
group_box (existing mark code; added for category targets whose existing chart is
the binned rates chart), new `heat_table` for contingency and 2×2 tables (cells
shaded by row share with the existing accent token; counts as text). No scripts.
