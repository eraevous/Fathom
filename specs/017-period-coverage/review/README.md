# Partial-period and interpretation review
Pinned public taxis fixture and authored synthetic controls only. Actual offline
Chromium:17screenshots, zero resource requests or document overflow (checks.json).
1280px report head: [before](before-head-1280.png), [after](after-head-1280.png).
Time-series evidence: [before](before-temporal-1280.png),
[after](after-temporal-1280.png), [boundary table](after-edges-1280.png),
[amplitude before](before-amplitude-1280.png), [amplitude after](after-amplitude-1280.png).
Dictionary scope: [before](before-dictionary-1280.png), [after](after-dictionary-1280.png).
[Categorical hint](after-string-hint-1280.png); [conditional Brief edges](after-brief-edges-1280.png).
Phone: [head](after-head-390.png), [edges left](after-edges-390.png),
[edges panned right](after-edges-right-390.png), [amplitude](after-amplitude-390.png),
[dictionary](after-dictionary-390.png). Remaining images are in this directory.

Visual findings/fixes: the inherited420px statistics cap squeezed temporal tables,
splitting labels/numbers even on desktop. Scoped wider, naturally laid-out temporal
comparison tables; ordinary two-column observation facts still fit phone width.
Caption shortened; timestamp-span/exposure caveat sits outside the scrolling table.
No univariate width redesign. Visually reviewed desktop/phone boundaries, amplitude,
hourly dictionary qualification and category hint. Open: wide exact tables require
phone panning; report length and existing chart-label wrapping are unchanged.

Full tests after all record appends and final presentation changes:387 passed,
2frozen legacy-AEC snapshot skips (extras and pinned Telosmith0.5). Seven new
focused cases all failed before implementation; affected temporal/Liftoff family
59passed. Existing full offline suite passes. AEC:0errors/100inherited warnings,
5,371 edges / 70 files/0skipped. Impact 38 affected / 83 no status change / 54 structural
pointers (review prompts, not acceptance). followup(raw) is empty. Existing ledger
prefix/protected documents unchanged; FT-DEMO3-R1/C1/E1@1 are provisional.

Found: public February timestamp span1857seconds (~31minutes) versus2419200seconds
in that month; March2677426/2678400seconds. All six first/last hour/day/month edges
flagged; amplitude median/CV2 explicitly include2partial edges. The old monthly
median3216.5 is retained, never passed off as a full-month comparable quantity.
Exact public artifact comparison strips only edge_coverage/partial_edge metadata:
all prior time-series numbers, signals, lags and selected series are identical.

Synthetic cross-month stub is1800seconds of January; complete date-only February
(common/leap) has no partial edge. One-hour two-point span is31minutes with one
both-edge entry. Hourly and no-declaration decoys retain the right wording; high-card
strings offer type:categorical without recoding, ordinary categories do not. Legacy
coverage is unavailable rather than assumed complete.

Limits/narrow readings: timestamp span is not observed exposure. Last instant includes
one written precision unit (day/minute/second); no rescaling, exclusion or new verdict.
The20-level inference/grouping cap is unchanged. Confusion topics closed: partial
periods hidden inside amplitude summaries, date-only text contradicting hourly work,
and opaque high-cardinality type routing. Private eval1–8 numbering was not supplied.
Claude execution review requested; no acceptance inferred. Native PPTX charts and
Brief boilerplate reduction remain follow-ups.

Main #26 was merged by Zach during finalization. Reconciled main e8d3814 into this feature branch, retaining both ledger tails byte-for-byte (main exact prefix), and refreshed baseline/after screenshots. Full extras suite: 387 passed / 2 frozen legacy-AEC skips. This branch also spells out the related existing valid n<5 group caution inline; no threshold change. No PR merge or main push by the agent.
