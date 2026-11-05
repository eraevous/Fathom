# FT-R17: panel HTML review
28 actual offline Chromium screenshots at 1280/390px in light/dark.
[Capture](capture.py), [manifest](manifest.json), [hashes](hashes.json),
[configuration/liftoff request checks](checks.json).

| View | Light desktop/phone | Dark desktop/phone |
| --- | --- | --- |
| Native panel | [1280](panel-top-light-1280.png) / [390](panel-top-light-390.png) | [1280](panel-top-dark-1280.png) / [390](panel-top-dark-390.png) |
| Four dimensions | [1280](panel-frequency-light-1280.png) / [390](panel-frequency-light-390.png) | [1280](panel-frequency-dark-1280.png) / [390](panel-frequency-dark-390.png) |
| Volume/boundaries | [1280](panel-boundaries-light-1280.png) / [390](panel-boundaries-light-390.png) | [1280](panel-boundaries-dark-1280.png) / [390](panel-boundaries-dark-390.png) |
| Metric disagreement | [1280](joined-metrics-light-1280.png) / [390](joined-metrics-light-390.png) | [1280](joined-metrics-dark-1280.png) / [390](joined-metrics-dark-390.png) |
| Week view | [1280](week-top-light-1280.png) / [390](week-top-light-390.png) | [1280](week-top-dark-1280.png) / [390](week-top-dark-390.png) |
| Month view | [1280](month-top-light-1280.png) / [390](month-top-light-390.png) | [1280](month-top-dark-1280.png) / [390](month-top-dark-390.png) |
| Reused target report | [1280](target-top-light-1280.png) / [390](target-top-light-390.png) | [1280](target-top-dark-1280.png) / [390](target-top-dark-390.png) |

Actual request capture:0 external requests; no document overflow; shared panel
colours and script-free panel/target report. configure/liftoff also request nothing
and untouched YAML remains {}. Those existing pages are not redesigned.

Visual findings/fixes:
- First pass split 156 into 15/6 and broke header words. Added minimum statistical
  table width, nonbreaking numeric cells and natural word wrapping.
- Source metadata squeezed labels; gave facts labels a stable minimum width.
- Detailed first row was long; all rows now open explicitly under compact headers
  with usable/zero/missing/absent/closed counts and unequal-exposure flag.
- Converted boundary tuples into ordinary numeric tables, with observed/normalized
  quantity, side, signed distance and coverage. Kept unknowns explicit.
- Put raw evidence/rules behind disclosures and used the existing shared palette.

Representative images were inspected visually. The pass uses existing in-repository
FT-R17 table/typography conventions: stable labels, tabular figures, adjacent context,
restrained colour, and evidence disclosures. No new chart framework. Native collapsed
report is about 1,814 px desktop/2,770 px phone; open rows/evidence grow it.

Open: wide exact tables require local phone panning. Comprehensive target reports
and all-open raw calendars remain long. No new Office panel layout; existing export
bytes/degradation are covered by the offline tests. This is builder review, not Kate
or owner acceptance; independent review remains with the requested reviewers.
