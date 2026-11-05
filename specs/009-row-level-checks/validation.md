# Spec009 validation and main readability check

This is a specification/fixture PR, not an implemented slice. No new application
regression passes are claimed. Eight fixture/decoy tables match truth.json.
Future tests are US1–4 plus boundary/unknown/routing/degradation/fresh-byte cases;
implementation and owner-held usefulness judging remain future work.

## Current main68890bf

Main source archived separately and used to profile the empty-values/repeated-key
synthetic tables. Actual HTML inspected offline at1280/390:
[empty desktop](readability/empty-values-main-1280.png),
[empty phone](readability/empty-values-main-390.png),
[key desktop](readability/repeated-key-main-1280.png),
[key phone](readability/repeated-key-main-390.png).
[DOM assertions](readability/dom.json) / [capture harness](readability/capture.py).

The slice1 JSON-dump criticism is no longer literally true on main. HTML has no
pre blocks, uses Dictionary→Provenance→Dataset summary→Findings→Relations, starts
columns collapsed, summarizes repeat findings with a full-view toggle, and hides
source hashes/evidence. Markdown also uses readable tables and disclosures rather
than a serialized artifact. This is not a repeat or rescoring of the experiment.

Still open: many separate Dataset…none flagged/0cards reduce information density;
long reports and fixed-export phone zoom remain. The report is more readable,
not proven maximally useful or superior on the owner's tables.

Found on authored empty fixture: missingness graph/exact pattern has9rows with
all3years missing; constant indicator and co-missing/lockstep columns are findings.
Missed: no explicit9-row value-blank observation tied to an inferred measurement
scope. Repeated-key fixture has840rows and frequencies in dictionary, but no
210×4row-unit/invariance/one-choice observation; ttme zeros are counted, not stated
as mode4concentration. Mixed-unit inference is not supplied by these generic counts.
Spec009 proposes those statements rather than claiming main has no row evidence.

AEC after-specify purpose-link report: P0@2and all cited requirement refs resolve;
none superseded at this branch base. No records accepted by the hook.
