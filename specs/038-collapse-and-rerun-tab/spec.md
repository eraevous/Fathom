# Spec 038: collapsible Findings, and reruns open in a new tab

**Serves:** P0@2, DG-RE@1 (the report is derived from the artifact; nothing here changes the artifact), FT-SERVE24-R1@1.
**Requested by Zach, 2026-11-23 (live):** "When running on the browser, the Updated report should open in a new window or tab. Findings, plus the categories underneath it, should all be able to be 'collapsed'." Asked whether they start open or collapsed, he chose **"Open, can collapse"**.
**Records:** `FT-UI38-R1` (requirement, provisional, written by the implementer), `FT-UI38-C1`, `FT-UI38-E1`.

## A. Collapsible Findings (report.html)

- The Findings section is a `<details open>`: its heading is the toggle, with the finding count beside it.
- Each kind group under it (Observations, Interpretations, Hypotheses, Suggested actions, Open questions) is its own `<details open>`, with its count.
- Everything starts **open**, so a reader without JavaScript, a printout or a search sees what they saw before.
- With JavaScript, two buttons appear: **Collapse all groups** and **Expand all groups**.
- A link into a collapsed group (from Key findings, the Dataset summary or an address-bar `#id`) opens the groups it sits in before the browser scrolls to it.
- The script runs inside the existing navigation script, so the report still carries exactly the two scripts it had (`fathom-navigation`, `fathom-transpose`).
- The wrapper is layout only. The rule that sets inferred readings in italics already skipped evidence disclosures (`<details>`). It now skips only those, not the new wrappers, so the text inside each group is styled exactly as before. Apart from the wrappers, the Findings markup is unchanged (checked by stripping the wrappers and comparing with main).

Not changed: report.md (its `## Findings` stays a plain heading), guide-profile.json, the "Show full per-item detail" toggle, the Dictionary.

## B. Rerun opens the updated report in a new tab (`guide serve`)

- **Rerun with this configuration** opens a tab during the click (browsers allow pop-ups only then), shows "Profiling…" in it, and loads the updated report into it when the profile finishes. The status line says "Report updated and opened in a new tab."
- Later reruns reuse that tab instead of opening another one. If the reader closed it, the next rerun opens a new one.
- If the browser blocks the tab, the status line says so and how to allow it. The report below the controls still updates, as before.
- `/report` is now served with `Content-Security-Policy: … sandbox allow-scripts`. A report in a top-level tab therefore runs in an opaque origin, as it already did inside the sandboxed frame: it can run its own navigation script but cannot read or navigate the control page (checked in Chromium). The control page's own headers are unchanged.

Not changed: tokens, Host/Origin checks, the fixed paths, Stop and idle expiry, the saved report (no server controls are ever written into it).

## Checks

- `tests/test_collapse_038.py`: the section and all five kind groups are collapsible and start open, with counts; the controls are hidden until the script runs; the page still has only its two scripts; text inside a group keeps its inferred-reading italics; report.md is unchanged in shape; the serve page opens the tab before awaiting the rerun and reuses it; `/report` carries the sandbox and the control page does not.
- In Chromium (Playwright): Collapse all, then following `#<finding id>` into a closed group opens that group only; Expand all opens everything; the Findings heading collapses the whole section. A real `guide serve` session: Rerun opens one tab with the updated report; a second Rerun reuses it (2 pages before and after); from the tab, reading `opener.document` and navigating the opener are both blocked.
- Screenshots at 1280 (light) and 390 (dark).
- Full suite and `aec check` (0 errors). `docs/demo-report.html` rebuilt with `scripts/build_showcase.py`.
