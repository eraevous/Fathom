# Validation — product polish

## Automated checks

Final working-tree run: **526 passed, 2 skipped**, with one third-party AnyIO/pytest deprecation warning. Python 3.12, core plus available scipy/reportlab/python-pptx, pinned Telosmith b0e202f (package 0.5.0). The two skips are historical AEC migration snapshots requiring their older pinned AEC version. Eight new product tests cover local links and scope disclosures, deterministic synthetic demo rebuilding, unchanged artifact bytes, offline script contracts, control reset/repeated filtering/theme/hash recovery through Node, and literal HTML escaping.

Existing offline, optional-export, profile/configurator/Liftoff, temporal, panel, serve, style and record tests all ran in that suite. No repository lint/type-check command is declared. `git diff --check` passes. AEC structural check reports 0 errors and 100 inherited warnings; it is not a usefulness verdict.

An early parallel run reported one output-byte mismatch while the renderer was being edited between its two subprocess runs. It is not counted as a clean baseline. The frozen final tree passed the full suite, including that test. No claim that a pre-existing runtime bug was fixed is made.

## Found and corrected

- The original README said no local server exists, despite implemented `guide serve`; corrected and linked the loopback/token/expiry boundaries.
- It described HTML as script-free despite progressive navigation and transpose controls; corrected.
- It described long tables as universally deferred despite the separate panel command; narrowed the limit to arbitrary long-table contracts.
- It excluded portable time patterns despite current temporal/clock support; corrected.
- Moving the long guide broke repository-relative references until they were rebased; tests now verify local targets.
- A first new test passed GuideDataFrame rather than its contained frame to build_schema; the test setup was corrected and rerun.
- Manual source review identified dark-theme print token inheritance on the landing page; print now forces the light tokens.

## What remains unverified

Actual browser screenshots and responsive visual acceptance remain **blocked**, not passed. Local Chromium launch fails during its singleton socket initialization (`Operation not permitted`), including the approved escalated launch. The managed cloud browser rejects file URLs and cannot reach the local HTTP preview (`ERR_CONNECTION_REFUSED`). The preview server was stopped. No screenshot is fabricated or represented as reviewed.

Node/control tests and source/CSS assertions are not substitutes for a rendered-browser pass. Before merge, inspect landing, report, configure and Liftoff at desktop/mobile widths, light/dark, scripts disabled, print, keyboard focus, no-match/Clear, fragment navigation and Back/Forward. Check landing copy success and denial on a real browser. An independent internal source review found no blockers and reran the five product UI tests; it also verified exact synthetic demo reproduction and local IDs/links/resources. This is not cross-family review or owner brand/usefulness acceptance.

## Acceptance scope

The authored synthetic `tests/fixtures/review.csv` remains the public demonstration. No real MtG data or private reports are copied into this slice. Analytical findings are unchanged; the slice adds discoverability and presentation, not new diagnostic rules. It does not implement MtG/SQLite intake, deploy a website or create an account. The proposed visual direction and broad usefulness remain for Zach to judge.

## Structural impact

The committed base edge snapshot used an older method. Direct comparison was rejected with `method mismatch: python_ast, resolution_names_sha`; the base was therefore regenerated from an untouched archive of b72ec90 using the same pinned Telosmith as the changed tree. The valid comparison derives 7 change events and flags 52 affected records, with 98 conclusions having no status change. These are structural review pointers, not invalidated owner decisions. The complete report is in `review/code-impact.txt`. Full conformance tests re-exercise the affected renderer/configurator paths, but prior visual/usefulness claims require the pending browser and owner review. No historical records were rewritten or automatically accepted.
