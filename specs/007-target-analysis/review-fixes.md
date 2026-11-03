# PR15 repair round: HO-20261103-002

Scope: review5747421193 on3367ab3; existing spec007/FT-TA-R1@2. No new features.
Plan: regression tests first; repair data/geometry/spec/validation; add accessible
values and bounded PowerPoint panels; visual pass and AEC; eight thread replies,
resolution and final PR update. Existing dependencies only. No protected-doc edits.

- [x] F01 r4451047766: plotted log-box n/exclusions/caution; zero/negative/linear decoys.
- [x] F02 r4451047591: tiny positive unrounded quantiles; existing stats unchanged.
- [x] F03 r4451047741: rates' horizontal/vertical captions in all formats.
- [x] F04 r4451047657: required nullable target, matches purpose.target; no-target decoy.
- [x] F05 r4451047683: complete typed summaries/contrasts/nested rates; valid numeric/category decoys.
- [x] F06 r4451047707: required integer coverage counts, typed optional counts; legacy/zero decoys.
- [x] F07 r4451047624: per-kind Chart values with full labels and precise plotted values.
- [x] F08 r4451047641:20groups×20levels PowerPoint layout without label overlaps; ordinary deck decoy.
- [x] F09 full/core/fresh bytes/AEC/affected screenshots, protected-prefix check, append evidence.
- [x] F10 fast-forward publish same branch preserving main merge; reply/resolve8threads; update PR15 then stop.

## Verification completed before publication

- Regression file:32fail on3367ab3,32pass after repair. Full196pass;
  core188pass/8optional skips. Existing tests retained.
- Fresh-process summary/full HTML/Markdown/PDF/PPTX/status bytes match.
- FT-R17:47actual affected-view screenshots at1280/390 in
  [gallery](review-fixes-gallery/README.md), all8cases fixed with remaining general
  phone/legacy/font limits disclosed.
- AEC:2276edges/35files,0skipped; check0errors/0warnings. Impact15structural
  change events,24affected/47unaffected. Stale/review marks are structural prompts;
  historical evidence remains historical, new claim supported by new tests/views.
- Appended only FT-TA-C2@1, FT-TA-E4@1, FT-TA-E5@1; verified3367ab3record
  prefix and all protected docs/decision passages unchanged.
- F10 is the final remote sequence: fast-forward existing branch preserving the
  authorized two-parent main merge, verify CI/tree, reply+resolve the8threads,
  update PR description with CLA unticked and stop. No PR merge/main push/force.

Remote completion: tested tree published at d557a71; push and PR tests/AEC all
passed. Every authorized review thread has a one-line repair reply and is resolved
(the rates thread was already resolved before this round's reply). This checklist
completion is documentation only. Final PR-description update/CLA untick is the
last action of the round, immediately after its publication.
