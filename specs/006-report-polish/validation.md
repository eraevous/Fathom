# Builder acceptance: 006 report polish

Checked against docs/acceptance.md. These are authored/public builder checks,
not Zach/Kate's deliberately unseen acceptance tables. Reports preserve inferred
meanings and open row-unit/generating-process/missingness questions.

| Table | Report findings and consequence | Missed / noise / limits |
| --- | --- | --- |
| polish/planted.csv,20x7, authored after implementation | Repeated Title with confirmation action; gross tail/mean versus median with inspection action; one two-digit-year and ambiguous day/month date with confirmation actions; date gap review; malformed email1/20 with review; missing_a/b co-missing4/20(20%),8missing cells,16complete rows, collection-process action. Positive log17values,3zeros separately counted. Title top-N suppressed while repetition finding remains. | Planted Grop A category typo is not identified as a possible spelling error. Zeros' positive median is below the existing100threshold, so no unusual-zero action: visible coverage alone is not a quality finding. Benign lockstep structure and quality contrasts also prompt review. |
| polish/clean.csv,20x7 | Complete20rows/7columns, unique titles, ordinary positive distribution with no extra log, strict dates/valid emails; no repeated-title/date-ambiguity/invalid-email/missingness actions. | Existing lockstep action on deliberately linear gross/missing_a/missing_b is review noise, not a confirmed defect. Clean is not action-free. |
| polish/movies.csv,3201x16, pinned public | Repeated titles, unusual zero gross, skew/date ambiguity/gaps/missingness remain report findings with review actions. Worldwide Gross log now covers3147positives and discloses47zeros; statistical mean displays85,343,400 and examples146,083. Default12slides replaces the roughly60-slide deck; dictionary entries compact. | No domain ground truth; public observations are not planted defects. Summary omits39of46charts visibly. Default HTML still16,861px; full expanded45,082px. |
| polish/college.csv,173x21, pinned public | Four columns share one missing row;172complete rows; skew/quantity summaries remain actionable. New static layout/default12slides makes the dictionary/distributions easier to scan. | No domain ground truth; bounded default deck omits68of75charts. Full PDF remains80pages; phone exports need zoom. |

Report-alone consequence: the synthetic analyst can see why tail/century ambiguity,
repeated identities and shared absence require review before choosing summaries or
handling missing values. Standalone documentation identifies observed values/types,
labelled inference, evidence and unknowns; domain meanings remain explicitly unknown.
The miss/noise ledger prevents claiming universal usefulness from conformance tests.

Validation:154tests pass with extras; core147pass/7optional skips. Existing fresh-process
repeatability and missing-dependency checks pass; public summary AND full exports
were additionally run in separate processes with byte-identical HTML, Markdown,
PDF, PPTX and manifest. No new runtime dependency. See [visual review](review/README.md)
for actual HTML/PDF/PowerPoint1280/390, heights, fixes and remaining issues.

FT-R18 narrows the prior builder display choices; earlier FT-PL-E2/E3 describe the
historical slice005 result, including old log/width restrictions. This slice adds
new records and does not rewrite that history. All protected files and earlier
record bytes are preserved. AEC is structural evidence, not acceptance.

AEC check: **0errors,0warnings**. Regenerated1802edges/29files. Code-impact comparison
flags22affected conclusions (6stale requirement links and16review flags),39unaffected;
these are structural prompts, not test failures or authorization decisions. The
full affected suite and fresh-process exports were rerun; new FT-PO evidence covers
the revised behavior. Earlier evidence remains an append-only historical account.
Authored records: FT-PO-R1@1/@2 (provisional), FT-PO-C1@1, FT-PO-V1@1,
FT-PO-E1@1–E3@1. FT-R18@1 and its decision passage were integrated unchanged from
7facafb, not newly accepted by Codex. PR#11/#12 remain open at pre-publication check;
the local authorized decision merge preserves both parents. PR is stacked on#11;
main rebase waits for both prerequisites to merge, with no force push.
