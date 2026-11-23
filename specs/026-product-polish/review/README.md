# Product review

Open `docs/index.html` from the checkout for the branded landing page and linked synthetic report. Regenerate the latter with `python scripts/build_showcase.py`.

Rendered review (builder pass, 2026-11-22): see [Rendered pass](#rendered-pass-2026-11-22) below. The original slice could not launch a browser; see [validation](../validation.md). Visual polish and brand acceptance remain Zach's.

Independent internal source review found no blockers. It reran 5 product UI tests, reproduced the synthetic demo exactly, verified unique IDs/local fragments/no external resources and checked diff whitespace. This is a source review only, not a rendered-browser or cross-family review.

The same-version structural [code impact report](code-impact.txt) identifies affected claims for review; owner decisions remain untouched.

## Rendered pass (2026-11-22)

Builder pass only, same family (Claude); the independent pass is still pending. Pages as committed on main: `docs/index.html` and `docs/demo-report.html` (`PYTHONPATH=src python3 scripts/build_showcase.py` reproduces the report byte for byte). Captured with `node capture.js shots > checks.json` from the repo root (offline Chromium via Playwright, `colorScheme` emulated, device scale 1): the landing page full length, the report's first screen, at 1280 and 390, light and dark. Eight screenshots in `shots/`.

`checks.json`: no network requests, no console errors, no page-level horizontal overflow in any of the 8 states. Also checked by hand: the Appearance/theme selector switches light and dark over a light system setting; with scripts disabled both pages render at 390 with no overflow and hide the selector and the Copy button (they need scripts).

Observed, not changed (none blocks; each is small or pre-existing):
1. Decorative labels on the landing page are 10–11 px: eyebrows, the preview's tags, numbers and caption, the code note and the Copy button (`small` in `checks.json`: 19 elements at 1280, 23 at 390). Readable on screen; a reader who needs larger text gets it from browser zoom.
2. Footer links (Repository, MIT license, README) are 15 px tall and "Read the full user guide" 17 px, under the 24 px WCAG 2.2 target size; they sit well apart, so they probably meet the spacing exception (not measured).
3. At 390 the install commands scroll sideways inside their frame (452 px of content in 314 px); intended, the frame is `overflow-x: auto`.
4. The theme choice is not remembered across a reload; the pages never stored it, and storing it isn't in the spec.
5. Report wording, pre-existing and outside this slice: "1 rows repeat an earlier raw identifier" and "1 nonmissing value(s)". Worth a pluralisation pass; not changed here, because the strings are in profile output that tests compare byte for byte.

No layout fault found that needed a fix, so this pass changes no page code.
