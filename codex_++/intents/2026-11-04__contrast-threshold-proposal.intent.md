---
status: proposed
author: claude:dg#colduser
date: 2026-11-04
---

# Proposal for Zach: group-contrast threshold and zero-share findings

This is an agent proposal, not Zach's words or a committed decision. No behaviour
changed. Kept under codex_++/intents/ because docs/decisions/ holds Zach's own
words (AGENTS.md).

## 1. "No marked contrast" for color × tip

Observed on seaborn `taxis` (public, 6,433 rows): mean tip green 0.80 (n 982) versus
rest 2.19; yellow 2.19 (n 5,451) versus rest 0.80. The gap is 1.40.

Which rule produced the verdict: `target.summarize_groups` marks a numeric contrast
only when |group mean − rest mean| ≥ the overall population SD of the target
(both scaled by the largest absolute value). Overall SD of tip is 2.45, so the gap is
0.57 SD and the row reads "No marked contrast".

This is a recorded choice, not a bug: spec007 plan ("numeric mean difference >=
overall population SD") and intent note 2026-11-02__target-analysis §3, under
FT-TA-R1@2 (provisional, implementing FT-R7@2). The threshold is deliberately strict
and is a review-prompt gate, not a significance test.

Why it misleads here: tip is skewed with 2,311 zero values (35.9%),
which inflates the overall SD; and the label "No marked contrast" reads as "no
difference" next to means that differ by a factor of 2.7.

Options:
- A (wording only): replace the label with "below marked-contrast threshold
  (gap 0.57 SD; threshold 1 SD)" so the measured gap is visible. No selection change.
- B (threshold): mark at ≥ 0.5 pooled within-group SD (or ≥ 0.5 overall SD), with a
  balanced clean decoy re-checked. Raises more prompts on large tables.
- C (keep): current rule and label.

Builder recommendation: A now; B only with a decoy study.

## 2. Zero counts are counted but not raised

Observed: passengers = 0 in 96 rows, distance = 0 in 51 rows. Both appear in the
numeric zero count/share statistics but produce no finding.

Which rule: the only zero finding is `implausible_zero` (univariate.enrich_columns):
zeros ≤ 20% of finite values, median positive ≥ 100, and ≥ 80% of nonzero values ≥
100 (spec003 FR-008, FT-R14@1 "zeros where most values are large"). Passengers
(median 1) and distance (median positive value below 100) fail the ≥ 100 scale gate. Spec003
validation.md already lists this miss ("zero among $10–$50 misses the >=100 scale
heuristic") and proposes making zero rules depend on declared units/roles.

A general "notable zero share" finding is not within any existing spec, so it was
not built. Proposal: for numeric columns whose minimum positive value is ≥ 1 (or
with a declared count/quantity role), raise an observation when 0 < zero share ≤ 5%
("zero may be a code, a cancelled record or a genuine quantity"), with a clean decoy
for columns where zero is common. Needs Zach's acceptance as an FT-R14 refinement.
