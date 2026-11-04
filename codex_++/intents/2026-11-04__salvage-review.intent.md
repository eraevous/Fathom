# Intent: review PR16 / HO-DG-20261104-XKSJ item1

Review against spec008 at a52ce37, pandas2.2.3. Preserve numeric readings pending
Zach; two new status:proposed decision files and provisional ledger records, explicitly
authorized by the handoff; not human decisions. Relay suggested records only, but
its note is expressly not authority and the task explicitly permits proposed files.
No existing decision/record line changes, no acceptance, no Data-Guide code.

FR-006 requires SVG light attributes mapped to theme tokens: fix missing categorical
series mapping with dark tokens (graphics contrast >=3:1 as review threshold), retain
all light attributes and fixed-export colours. FR-008 requires light print: test the
CSS cascade including explicit dark and dark system preference; print overrides need
equal/higher specificity. PDF/PPTX kind colours are explicitly out of scope (FR-007),
so report as deferred, not implement. No new dependencies.

Tests first, browser proof before/after; inspect affected HTML at1280/390 and both
print/system overrides, full/core suites and fresh bytes, regenerate AEC/check.
Post review on existing PR16 and fast-forward its branch; this is item1's PR, not
a fourth PR. Other items get separate branches/PRs.
