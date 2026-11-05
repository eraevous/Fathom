# Report-head review and acceptance
Pinned public taxis (repository fixture/source manifest), 6,433 rows. 1280×900:
[before profile](before-profile-1280.png), [after profile](after-profile-1280.png),
[before Brief](before-brief-1280.png), [after Brief](after-brief-1280.png).
Phone: [profile](after-profile-390.png), [Brief](after-brief-390.png).
Actual offline Chromium, zero requests and no document overflow; checks.json.
Visually checked head spacing, legibility, links and conditional wording. Fixed an
initial lag-1 cycle headline to use the existing lag>=2 cycle rule. Wide detail
rows still scroll locally; no layout redesign or Office feature.

Full tests:382 passed, including15 offline cases;6 new focused cases failed before
implementation. Historical artifact decoy strips only new disclosure metadata;
all old values/verdicts remain equal. AEC:0 errors,100 inherited warnings.

Found: Brief cash tips 0/1,812; conditional24-hour cycle and34empty hours.
Configured fare-target report: selected total/fare then distance/fare (r0.9201707),
Queens marked gap13.2547>=SD11.3636, Manhattan not marked10.6105<11.3636.
Fare skew3.2167 passes moment gate but displacement0.42248IQR<0.5IQR; passengers
passes both (skew2.3586, displacement0.53925IQR). These match unchanged verdicts.
Clean/identical-distribution groups remain unmarked; missing legacy gates say
unavailable. No new zero rule/target association is run in stage-two or Brief.

Narrow reading: the Brief has no target/pair analysis, so it cannot truthfully show
Queens or distance/fare without a declaration. Headlines only select evidence
already present; they never apply suggestions. Unlike diagnostics have no global
rank: stable coverage slots, existing rank within relations. Relay numerical
examples differ from this pinned public fixture; original computations are retained.
Confusion numbering1–8 was not relayed; mapped topics closed: buried headline,
unexplained unmarked contrasts and apparently inconsistent skew wording.

Follow-ups (out of scope): native PowerPoint charts; reduce Brief boilerplate.

PR26 CI follow-up: appended relation-only R1@2/C1@2/E1@2. Requirements hold
implemented_by; claims depend_on requirement and code; evidence supports C1@2.
followup(raw) now returns no migrations. Full extras with CI-pinned Telosmith0.5:
380passed/2skipped (only frozen AEC0.4 impact-snapshot tests skip). Earlier382pass
run preceded the final claim/evidence append and used AEC0.4; it did not validate
that final ledger. The final full run includes the repaired ledger. No old lines edited.
