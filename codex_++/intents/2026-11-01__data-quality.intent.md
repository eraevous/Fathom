# Intent: slice 2 — data quality and readable reports

Author codex:aec; HO-20261101-006; 2026-11-01. Implementation readings, not new owner decisions.

1. FT-R5 and FT-R6 both describe the opening: use one leading block with dataset
   summary first and usefulness/unknowns immediately beside/below it, before findings.
2. The absent reference report is not consulted. Implement only FT-R6's wording:
   typed findings, relations, dictionary, provenance, summarized default/full toggle.
3. Preserve accepted FT-R2..R6 records verbatim. Thresholds below are transparent
   deterministic heuristics, not new domain requirements or acceptance claims.
4. Numeric sentinels: at least five finite values; -1 is a rare minimum among
   otherwise nonnegative values; 999/9999/99999 are rare maxima at least five times
   the other values' median absolute magnitude (floor 1); candidate share <=20%.
   Literal NA/null/none/unknown/n-a/tbd/? are placeholder hypotheses, not null conversions.
   Test/dummy/sample labels with optional numeric suffixes are dummy hypotheses.
5. Dominance: >=5 nonmissing cells, top share >=95%; constants have one distinct
   nonmissing value and >=2 cells. Empty columns are not constants.
6. Redundancy: exact lexical vectors including missing cells, affine numeric
   fingerprints (>=5 finite, >=3 distinct, matching missing/invalid mask, rounded
   normalized tolerance 1e-8), or repeated-category recoding partitions (>=5 cells,
   2..20 levels, at least two observations per level). Unique categorical IDs are
   not declared lockstep. Near duplicates use >=95% row agreement AND >=95% agreement among at least five
   jointly present cells (exact vectors are excluded even on smaller tables); screen at most 2000 candidate vector comparisons.
   Fingerprint groups avoid producing an all-pairs matrix. Group findings do not
   consume the pair budget; they describe structural redundancy, not associations.
7. Co-missingness: nonempty identical missing-row masks, with counts/shares and
   bounded row examples. This detects exact co-missing patterns, not every partial
   overlap. Conditional missingness compares missing rates across 2..20 groups
   with >=3 rows/group and >=30 percentage-point spread. Numeric grouping uses
   below/above median; test at most 20 grouping columns (target first, then names).
   These quality contrasts and existing value routes share one output pair budget.
8. Temporal: >=4 distinct ISO dates; modal positive day spacing must recur at
   least twice and cover >=half the intervals; gaps >1.5 times that inferred
   cadence are flagged. No external calendar/schedule, timezone or causal claim.
9. Skew: >=8 finite values, absolute standardized third moment >=2, and mean/median
   displacement >=half the IQR (or a small relative fallback if IQR zero). This
   narrowly explains why the mean may not be typical; advanced distributions wait.
10. Rank eligible candidates by literal declared focus (target/column mentions),
    then strength: absolute existing Pearson r, group-mean range divided by numeric
    range, or missing-rate spread; then complete-case count and lexical pair/method
    names. These unlike descriptive scores are a priority heuristic, not comparable
    inferential tests. Near-constant/duplicate value candidates are excluded, but
    a variable missingness mask can remain relevant even if observed values constant.
    Do not add FT-R7's general target analysis or FT-R8's axis controls.
11. Additive version-1 artifact fields retain full findings and selection/coverage.
    Slice-1 artifacts remain renderable; complete rows cannot be reconstructed
    without raw data and must be unavailable there. No runtime dates or randomness.
12. Native checkbox/CSS implements the global one-click switch; details/summary
    handles evidence. No new runtime or plotting dependency or narrative layer.
13. Builder tables and a later builder holdout are synthetic and public. The latter
    is not an independent blind trial. List misses and false alarms without tuning
    rules to erase misses; Zach/Kate's unseen tables remain outside this run.

14. docs/acceptance.md and AGENTS retain older “proposed” wording, while the latest
    FT-R4@2 is committed and accepted. The record takes precedence; the criterion
    is applied without editing the protected document or claiming builder acceptance.
    Repetitive quality findings, not only type/meaning questions, are grouped by
    diagnostic family and kind; their original messages/evidence remain one click
    away. The initial diagnostic freeze preceded the holdout; a later shared-absence
    audit decoy required the generic jointly-present agreement guard. Both hashes
    and that timing are recorded; held-out misses were not tuned away.

Drift check: a quality helper stays inside the profiler's responsibility and receives
plain columns/rows; it creates no connector, renderer or orchestration subsystem.
Renderer changes remove primary JSON dumps and derive both views from the same
artifact. No protected guiding document, existing record line or decision is edited.
