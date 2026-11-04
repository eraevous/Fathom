# Spec 008 visual review (FT-R17)

Actual offline HTML in headless Chrome (Playwright), 1280 and 390 wide, four modes:
system light, system dark, `data-theme="light"` on a dark system and
`data-theme="dark"` on a light system (the attribute is set by `capture.py`; the
report has no script). Reports: `tests/fixtures/salvage/planted-missingness.csv`
with `planted.yaml` (target income, group_by region) and `tiny.csv`.
36 screenshots; `manifest.json` records view, mode, width, document width and
computed body background; `image-hashes.json` their hashes.

Inspected and found as intended:
- Findings: kind tags (OBSERVATION, ACTION, ...) and kind-coloured headings and
  borders in all modes; the "Missingness in income varies with region" observation
  reads in full at 390.
- Tiny column: Q1 -6.936e-13, median -9.741e-14, SD 1.028e-12 (main showed 0);
  histogram and box keep their shape with e-12 ticks.
- Target charts: box, scatter and rate marks map to dark tokens; text readable.
- Quality block: thresholds, test count and results listed.
- Overrides win over the system setting both ways; print uses light tokens (CSS).
- No horizontal overflow (document width equals viewport in every capture).

Open: the 20-colour categorical series (rate bars, legends) keeps its light hues in
dark mode, 2.6–4.2:1 against the dark panel, some under the 3:1 graphics guideline.
Kind colours are HTML-only; PDF and PowerPoint are unchanged. Phone zoom for fixed
exports and long reports remain as in spec 007.
