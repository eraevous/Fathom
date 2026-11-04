# Intent: HO-DG-20261104-9B3S, three salvage decisions (DEC-043)

Serves P0@2, DG-RA@1, DG-RB@1, DG-RE@1, DG-RF@1, FT-R16@1, FT-R17@1, FT-R14@1 through
spec 008; proposes FT-SD-R1@1 (provisional). Builder: claude:dg (Claude subagent in the
coordinator's cloud session), authorized by Zach's DEC-048 delegation. Branch
salvage/dec-043 from origin/main 68890bf. One PR; no merge; CLA box left unticked.
Data-Guide code was not opened; only the salvage memo's extracted choices were used.

Trade-offs and readings (narrower reading where documents are silent):

1. **Significant figures with a 10-decimal floor.** "6 significant figures instead of
   10 decimals" read literally collapses large-offset values: on the offset fixture,
   percentiles 1730000133.67 / 1730000656.5 / 1730001179.33 all become 1730000000.
   The implemented rule keeps max(10 decimals, 6 significant figures). It changes
   only |x| < 1e-4, which is where the reported bug lives, and leaves every
   normal-scale artifact byte-identical. **Open for Zach:** accept, or ask for the
   literal rule (one line in `univariate.stored`).
2. **Geometry** uses the same rule at 12 figures, not raw floats, so normal-scale
   SVG/PDF/PPTX bytes do not move and tiny charts keep their shape.
3. **Schema 2** marks the precision change; nothing else in the shape changed except
   the additive `quality.missingness_tests`. Version-1 artifacts still load and
   render; their rounded zeros cannot be recovered without re-profiling.
4. **`guide validate`** validates a CSV and config, not an artifact. The handoff's
   "make guide validate accept both" is met by the artifact validator used by
   `render`/`compare`/`export`. Adding artifact input to `guide validate` would be a
   CLI change; recorded as a challenge, not built.
5. **Missingness test thresholds.** alpha 0.01 family, Bonferroni, V ≥ 0.15 from
   DEC-043. Minimum group size 10 and Cochran's rule (no expected cell < 1, at most
   20% below 5) are Fathom's readings; the memo only says "minimum group size".
   m counts tests actually run, so screening more columns raises the bar.
6. **Reconciliation with "p-values never select actions"** (research.md:15): the
   test writes observations only, never actions, never enters pair ranking/budget,
   charts or target analysis. Stated in spec 008. The existing descriptive
   spread ≥ 0.30 rule (which does suggest a review action) is untouched; both can
   report the same pair, from different evidence. Merging them is a design question
   for Zach, not done here.
7. **Stdlib chi-square tail** instead of optional SciPy, so the observation does not
   depend on an extra. Cross-checked against SciPy in tests when installed.
8. **Palette.** Kept Fathom's teal light palette (the Data-Guide hexes were
   assistant-authored); kind hues follow the memo's roles, adjusted to pass WCAG AA
   on the panel in both themes. `fathom/palette.py` is a separate module only to
   avoid a renderers↔charts import cycle; `renderers.PALETTE` points at it.
9. **Dark mode without script.** System preference plus `data-theme` on `<html>`;
   no toggle control (it would need script). SVG marks keep light colour attributes
   so the Markdown report is unchanged; HTML CSS maps those attributes to tokens.
   Kind colours only in HTML; PDF/PowerPoint unchanged (open).

Parked: Zach's exponent-first display "(e-12)1" (C-22) is recorded in spec 008 and
not implemented.

Challenges noticed, not fixed: (a) `scalar()` in renderers prints stored floats with
`.10g`, so raw-evidence tables can show more digits than the 6 stored significant
figures imply for small values; harmless but inconsistent. (b) Two missingness rules
now coexist (spread rule with action, test rule observation-only); a reader may see
both for one pair.
