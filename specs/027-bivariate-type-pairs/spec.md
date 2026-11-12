# Feature Specification: Bivariate type-pair layer

**Branch**: 027-bivariate-type-pairs | **Created**: 2026-11-10 (CT)
**Status**: provisional. Authorized by Zach on 2026-11-10 (relayed as DEC-189 in the
coordination ledger): "I would also like to begin rebuilding bivariate analyses";
chosen scope "Full type-pair layer ... Keeps today's budget and ranking"; depth
"Spec, then draft PR". Kate reviews first (DEC-038); Zach merges.
Serves: P0@2, DG-RA@1, DG-RB@1, DG-RC@1, DG-RE@1, DG-RF@1, FT-R7@3.

docs/vision.md §2 asks for bivariate analysis "across meaningful type pairs
(numeric×numeric, category×numeric, binary×numeric, category×category,
binary×binary), with association and effect summaries suited to the types".
Today every selected pair gets one screening measure (Pearson r, correlation ratio
eta or Cramér's V). This slice adds, for each selected relationship only, the
measures suited to its type pair, one chart per type pair and a plain-language
observation. Selection, budget and ranking are unchanged (DG-RC; vision Q4).

## User Scenarios & Testing

### US1 — Read each selected relationship with measures suited to its types (P1)
An analyst declares a target. For each selected pair the artifact records a
`type_pair` block: the pair type, how each column was classified (numeric,
category, binary) and the measures for that type pair:

| Pair type | Association / effect measures | Summary |
| --- | --- | --- |
| numeric×numeric | Pearson r (unchanged) and Spearman rho (average tied ranks); disagreement note | scatter (existing) |
| category×numeric | eta (unchanged), Kruskal-Wallis H and rank eta-squared (η²_H, bias-adjusted) | per-group n, median, Q1, Q3, IQR, mean; grouped box |
| binary×numeric | rank-biserial correlation; difference in medians and in means | per-group n, median, Q1, Q3, IQR, mean; grouped box |
| category×category | Cramér's V (unchanged) and bias-corrected V (Bergsma 2013) | contingency table, at most 10×10 shown levels; heat table |
| binary×binary | odds ratio (Haldane-Anscombe +0.5 when a cell is 0), risk difference, phi | 2×2 table; heat table |

Acceptance: planted relationships for each type pair produce the right pair type
and hand-verifiable values; Pearson values and ranking are byte-identical to
before; a monotone non-linear pair shows Spearman well above Pearson with a
disagreement note; a 2×2 with a zero cell reports the correction.

### US2 — Plain-language observation that never overstates (P1)
Each selected relationship gets one `observation` (rule `type_pair_association`,
generator `rule:type-pairs-v1`) worded from the stored measures: direction for
rank and binary measures, group medians for grouped numeric pairs, the 2×2 shares.
A disclosed wording rule calls a magnitude below 0.1 on the pair's headline
measure "near zero (no notable association)". This is wording, not a test or a
strength band; no p-value or threshold selects an action (001 research). No new
`action` finding is created: the existing per-pair review action stays the only one.
Acceptance: independent null decoys are worded "near zero" and carry no direction;
the gate text is disclosed on the finding.

### US3 — See it in every view (P2)
HTML and Markdown show the type-pair measures and the chart next to the existing
pair statistics; `relations.csv` carries the new fields as flattened columns;
findings.csv carries the new observation. Old artifacts without `type_pair` still
validate and render.

### Edge cases
Two-valued numeric columns (0/1 or any two numbers, in the pair's complete cases) count as binary; true/false
booleans and two-level categories too. A binary column paired with a category of
three or more levels is read as category×category. Groups of one value (IQR 0),
ties, all-equal ranks or fewer than three cases (Spearman null with reason), empty 2×2
margins (odds ratio, risk difference, phi not estimable → null), negative rank
eta-squared (stored clipped at 0), high-cardinality categories (more than 20
levels stay excluded by the existing rule; 11–20 levels are capped to 10 shown
levels plus an "other levels" total), missingness-by-group pairs (not type pairs;
unchanged), budget 0, no target (no pairs, unchanged).

## Requirements
- **FR-001**: Classify each selected non-missingness pair into one of the five type
  pairs with a disclosed binary rule; store roles and the two binary levels.
- **FR-002**: Compute the measures in the table above with stdlib arithmetic only;
  hand-verifiable formulas; null with a reason when undefined.
- **FR-003**: Keep candidate generation, screening measures, ranking key, budget,
  grouping reservation and existing fields unchanged; enrich only selected pairs.
- **FR-004**: One chart per pair type using the existing self-contained SVG code
  and palette: scatter, grouped box, heat table. No external assets or scripts.
- **FR-005**: One observation per selected pair with nested quantities, at most one
  comparison per rendered line, and the disclosed near-zero wording gate.
- **FR-006**: Additive within schema 2 (see research R7); old artifacts validate;
  output stays byte-identical across runs.
- **FR-007**: relations.csv, findings.csv, HTML and Markdown carry the new fields.

## Success Criteria
Hand-computed values match textbook formulas in tests; planted pairs found, null
decoys worded near zero; all pre-existing tests pass unchanged; Pearson values,
rank order and selection identical on the existing fixtures; AEC 0 errors.

## Assumptions
Measures are descriptive summaries of complete cases in one snapshot. Binary level
order is lexical (numeric order for numbers) and carries no domain meaning such as
"positive outcome". Unlike measures remain priority heuristics, not interchangeable
effect sizes. No new runtime dependency; scipy stays optional and unused here.
