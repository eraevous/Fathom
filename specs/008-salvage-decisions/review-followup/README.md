# PR16 independent review follow-up (2026-11-04 CT)

Reviewed a52ce37 against spec008, pinned pandas2.2.3.

| Finding | Disposition |
| --- | --- |
| FR-006:19categorical series colours have no theme mapping; dark contrast2.6–4.2:1 | Fixed:all20 mapped to recorded light/dark tokens; dark marks >=3:1 against panel. SVG attributes/Markdown and Office colours unchanged. |
| FR-008:print :root selector loses to explicit-dark and system-dark selectors | Fixed:later light-print declarations use matching specificity. Actual browser checks both paths. |
| 10-decimal floor plus6significant figures | Proposed to Zach in new decision file and FT-SD-Q1@1; no policy change/acceptance. Offset decoy supports preserving detail but does not resolve product policy. |
| Dimensionless coefficients at10decimals | Proposed to Zach in new decision file and FT-SD-Q2@1; no policy change/acceptance. Symmetry noise example is real; tiny does not universally mean noise. |
| PDF/PPTX finding kind colours absent | Deferred by FR-007 and explicit out-of-scope list; no code added. |

The original report's open categorical issue was a gap in FR-006's mapping, not a
reason to add export kind colours. Dark graphics review threshold3:1 is disclosed;
kind text remains the spec's4.5:1. Palette hues are a review choice, not accepted policy.
At20categories, similar hues still require labels/exact values; no claim of categorical
distinguishability from colour alone. Fixed exports still need phone zoom.

## Verification

Original215tests pass. New2regressions fail before and pass after. Full217pass;
core208pass/9optional skips. Core environment had an uninstalled SciPy namespace
residue (no distribution); moved outside the venv before the genuine absence run.
Summary/full PDF/PPTX bytes equal original PR16 and each other across fresh processes;
existing fresh-process JSON/HTML/Markdown check passes. No new dependency.

16actual offline Chromium screenshots: before dark/forced-dark print and after
light/dark/both overrides/both dark-to-print cases, each at1280/390.
[capture.py](capture.py) asserts actual computed panel and all20fill colours for
each after mode. [Manifest](manifest.json) / [hashes](image-hashes.json).

- Dark [before1280](before-dark-1280.png) / [after1280](after-dark-1280.png),
  [before390](before-dark-390.png) / [after390](after-dark-390.png).
- Forced-dark print [before1280](before-print-forced-dark-1280.png) /
  [after1280](after-print-forced-dark-1280.png), [after390](after-print-forced-dark-390.png).
- [Light1280](after-light-1280.png), [light390](after-light-390.png),
  [forced light1280](after-override-light-1280.png), [forced dark390](after-override-dark-390.png),
  [system-dark print1280](after-print-system-dark-1280.png).

Builder-independent review within the Codex lane, not owner acceptance. Visually
inspected dark before/after, print and phone views; CSS probes cover every mode.
No prior Data-Guide implementation or unnamed private experiment material read.
