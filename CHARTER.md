# Fathom engineering charter

**Status: accepted by Zach, 2026-11-01 12:41 CT ("Charter looks good, too"),** as the Data Guide charter; carried into Fathom unchanged in substance (`DG-D2`). It derives from the April 2026 design, distilled in `docs/design.md`, and the requirements `DG-RA` to `DG-RF` in `.aec/records.jsonl`. Changes need Zach's approval.

*Carried over on 2026-11-01. Only pointers changed: rule 1 now cites `docs/design.md` instead of the April design file. Files and commands named under "Enforced by" are the targets to build; none exist yet.*

Each rule gives: Rule → Why → Enforced by.

1. **One data flow.**
   Rule: every connector produces a `GuideDataFrame`; every renderer consumes a `ProfilingResult`; only the profiler touches both.
   Why: one path means one place to test.
   Enforced by: `docs/design.md` (Architecture); review.

2. **Findings are typed and attributed** (`DG-RA`).
   Rule: observation, interpretation, hypothesis, action or question, each with evidence and a generator.
   Why: a reader must be able to tell what was measured from what was guessed.
   Enforced by: `tests/test_understanding.py`.

3. **Inference is never presented as fact** (`DG-RB`).
   Rule: inferred semantics keep their confidence, reasons and alternatives; human annotations override them and the inference is kept. Useful results resting on an inference are still shown, labelled.
   Why: a type guess is not domain knowledge, and hiding it would lose what it is good for.
   Enforced by: tests; report wording.

4. **The question selects the analysis** (`DG-RC`).
   Rule: a declared question, decision or target governs which pairs and metrics are shown, within a budget. Excluded columns are listed with reasons. No all-pairs (Cartesian-cross) explosions.
   Why: combinatorial output buries what matters.
   Enforced by: pair-screening tests.

5. **Re-profile and compare** (`DG-RD`).
   Rule: a transformed table can be profiled again and compared. Each profile carries its context (snapshot date, source, transformations and their types), the comparison states those differences first, and it says what it can't know (row-level lineage).
   Enforced by: `guide compare` tests.

6. **The artifact is the interface** (`DG-RE`).
   Rule: `guide-profile.json` is versioned; Markdown and HTML derive from it.
   Enforced by: renderer tests.

7. **Tested for accuracy, routing, degradation, reproducibility and purpose** (`DG-RF`).
   Rule: every check has a violating fixture and a decoy; output is byte-identical across runs; missing optional dependencies degrade.
   Enforced by: `python3 -m pytest`.

8. **Safe to publish.**
   Rule: no real data, credentials or org-specific code in the repository.
   Why: the April design targets public release.
   Enforced by: review.
