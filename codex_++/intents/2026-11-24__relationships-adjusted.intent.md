# Spec 034 slice 2a: conditional and partial association (A2, A3)

Author: claude:fathom#wake-20261124-03 · model=claude-opus-5-5 · unconfirmed readings marked

Narrower readings taken where the spec is silent:

- **"A selected target pair"** read as the target pairs `pair_budget` already chose (generator `rule:target-v1`), never the missingness-contrast pairs and never anything outside the budget. `selection_route` records this in the artifact.
- **`condition_on` takes 1 to 3 columns.** The spec says `[column]` without a count; 3 matches the set cap. Each column is applied separately (no crossed levels).
- **Conditioning column must be categorical or boolean** (declare `type: categorical` for an integer code). Binning a numeric column is not done.
- **Collinearity tolerance:** a control (or a pair column) whose unexplained share of variance after the earlier controls is at most 1e-6 counts as collinear. 1e-9 was too tight for data rounded to 4 decimals (a control equal to 2z+1 passed).
- **Minimum cases for A3:** controls + 3, so the residual correlation has at least one degree of freedom left. The 30-case floor is A2's per-level rule only.
- Partial results are reported next to the Pearson r on the **same complete cases** (pair plus every control), not the target screen's n.

Presentation (HTML, Markdown, CSV) is slice 2b, after Fathom#79 (slice 1b) merges, since it extends 1b's tables.
