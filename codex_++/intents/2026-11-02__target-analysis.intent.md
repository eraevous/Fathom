# Intent:HO-20261103-001 target analysis

1. Extend existing target routes/ranking and retain quality contrasts under the same
   pair_budget; candidate scoring is a light target×column screen, detailed groups
   and plots only selected pairs. Pearson abs(r), eta, unadjusted Cramer's V share
   a priority heuristic, not interchangeable effect sizes. No new runtime dependency.
2. Within-group is pair-local: categorical target groups the selected predictor;
   numeric target is summarized within selected declared/detected categories. For
   numeric targets reserve one slot for best category at budget>=2 (explicit group_by
   may reserve at1); disclose reservation separately from numerical ranking. No
   unbudgeted group×all predictors or target-versus-two-predictor methods.
3. Up to20groups/levels, n<5too-small warning; shares/allrows, valid-case means/rates,
   missing grouping rows separate. Observed mean contrast>=one overall SD or rate/
   missingness gap>=.30 gives a review prompt with rest counts, not significance.
4. exclude_from_target explicitly marks known leaked or unwanted predictors;
   identifier/nearunique text/category and existing constant/copy blocks apply.
   Ordinary unique numeric quantities stay eligible. Arbitrary rank/affine leakage
   cannot be proven from values; unmarked leaks may remain ranked. Do not exclude
   every perfect correlation, invent semantics or accept requirements.
5. Scatter display max200deterministic sorted rank-spaced points; numeric bins<=4
   equal-width with explicit empty/small bins. Log eligible dimensions keep positive
   cases only, record coverage/exclusions, ticks original units; no invented currency.
6. Slim box strip/noY; sticky desktop statistics follows normal document scrolling,
   phone stacks. This is static CSS explicitly solving FT-R19, no layout controls,
   HTML script, switchable axes or dynamic layout builder. Positive-only log ECDF
   conditions on positives, records counts, retains linear ECDF.
7. Inherit PR#14 authorized duplicate FT-R18 removal untouched; never edit existing
   records/decisions ourselves. Spec/records precede code. Main rebase after#14merge,
   no main push/force/PR merge. Builder checks are not independent acceptance.
