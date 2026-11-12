# Bivariate type-pair layer intent

Zach (2026-11-10, relayed DEC-189): "I would also like to begin rebuilding bivariate analyses"; scope "Full type-pair layer ... Keeps today's budget and ranking"; depth "Spec, then draft PR". Spec: specs/027-bivariate-type-pairs. Starts from f600888.

Narrower readings taken where the documents are silent or conflict:
- Ranking and budget are untouched. The relay brief suggested extending the ranking strength key to the new measures; Zach's wording ("keeps today's budget and ranking") wins, so the new measures only describe pairs the existing screening already selected. Selection order, screening values (Pearson r, eta, Cramér's V) and all pre-existing fields are byte-identical on 77 fixture profiles once the additive keys are removed.
- No schema bump. The brief asked for one if the stored shape changes; docs/schema-flattening.md keeps schema3 as a proposal for Zach, so `type_pair` is an optional additive key on bivariate items within schema 2 (as `target_analysis` was in spec007). Old artifacts validate unchanged.
- Pairs exist only for a declared target (plus missingness contrasts), as before. Without a target there is still no bivariate output (DG-RC, vision Q4); the layer does not open all-pairs screening.
- One new observation per selected pair, no new action, no p-value. "Near zero" is a single disclosed wording cut (0.1 on a correlation-like headline) rather than strong/moderate/weak bands; flagged for Zach. The Spearman/Pearson disagreement cut (0.2) is also wording only.
- Binary = exactly two distinct non-missing parsed values in the whole column (includes 0/1 and other two-valued numbers). Level order is sort order; the second level is the index level. This makes odds-ratio direction lexical ("miss" over "hit"), disclosed but possibly surprising.
- Rank eta-squared (η²H, Tomczak & Tomczak 2014) and bias-corrected V (Bergsma 2013) were chosen because their null expectation is near zero, so the near-zero wording does not misread small groups as association.
- Charts reuse the existing scatter and grouped-box marks; a new heat table (counts as text, an opaque row-share bar) covers category×category and 2×2. PDF/PowerPoint exports are not extended; browser visual review at 1280/390 was not run.

Drift check: a new module (type_pairs.py) extends the existing bivariate responsibility; no component changes role, no subsystem is added, effort went into measures and wording an analyst reads.
