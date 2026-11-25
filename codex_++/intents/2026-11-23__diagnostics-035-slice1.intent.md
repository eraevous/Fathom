# Intent: spec 035 slice 1 (context gate, registry, statuses, W1, W5, T1, T3)

Author: claude:fathom#wake-20261123-17 · Reviewer: none yet · model=claude-opus-5-5

Where the spec is silent, I took the narrower reading. Each item is the implementer's reading, for Zach to adjust:

1. **Missing task is a question, not an error.** A `diagnostics` block without `task` validates; task-specific checks are `not_applicable` and a question asks for `diagnostics.task`. An unknown task value is refused.
2. **W5 equality rule needs two distinct target values** among complete rows. Without that, a constant target makes every constant feature "equal to the target".
3. **W5 under `forecast`** applies only the equality rule. The spec names the categorical rules for classification and the rank rule for regression and count; forecast is neither.
4. **T3's condition looked for** is a value a count can't hold (negative, not whole) or unusable exposure (missing, at or below 0). The dispersion figures are reported either way and are never classified, so nothing in T3 picks a count family (R5).
5. **T1 lists at most 50 classes** in the artifact (all are counted). The spec bounds pairwise work, not this list.
6. **No HTML section yet.** Results reach the report through findings (one observation per signal, one status line for the rest, questions for missing roles and W5 timing). The statuses render with different wording; a dedicated table is a later slice.
7. **`exposure` only with `task: count`, `horizon` only with `task: forecast`**; otherwise the block is refused rather than silently ignored.
