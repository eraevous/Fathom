# Feature Specification: Headlines and inline verdict gates
Branch: `015-headlines-and-gates`. Created: 2026-11-05. Status: provisional.
Serves: P0@2, DG-RA@1, DG-RE@1, FT-R6@4, FT-R7@3, FT-DEMO1-R1@1.
Input: HO-DG-20261105-E4V9, item 1. Kate reviews first; Zach accepts/merges.

## User Scenarios & Testing
### US1 — Find the important evidence (P1)
A cold reader sees a Key findings block before the dictionary/profile and at the top
of the Brief, at most five concrete findings. Selected relationships retain their
existing rank; discovery measurements keep their provisional declaration wording.
Acceptance: public taxis exposes cash zeros, the selected distance/fare association,
marked Queens contrast, conditional 24-hour cycle and no-recorded-event hours when
those measurements exist in the relevant artifact. No new target or pair is selected.
A clean/empty artifact does not acquire claims of good quality or invented findings.
### US2 — Understand why the verdict differs (P1)
A group row says both its observed gap and its SD/rate gate, even when unmarked.
A numeric column explains both skew gates; a large third moment alone does not
imply the separate strongly-skewed verdict. Findings expose their existing rule
beside the verdict. Acceptance: synthetic marked/unmarked groups and skew decoys;
public Manhattan/Queens and fare/passengers are checked without changing results.
### Edge cases
Legacy artifacts without additive gate metadata explicitly say unavailable; undefined
or empty comparisons remain unknown. Headline text is escaped and IDs stay unique.
## Requirements
- FR-001: At most five evidence-backed headlines in profile HTML/Markdown and Brief.
- FR-002: Reuse existing pair ranking and findings; preserve conditional status.
- FR-003: Show numeric target contrast gaps/thresholds and skew conjunction inline;
  other threshold findings show their already-disclosed rule inline.
- FR-004: Verdict logic, thresholds, pair budgets and chosen analyses stay unchanged.
- FR-005: Self-contained offline and byte-identical reruns; no dependency addition.
## Key Entities
Headline: message, evidence link and source/status. Gate: observed measure, threshold,
comparison and existing verdict; additive evidence, never a new decision rule.
## Success Criteria
At most five headlines precede detail; each marked/unmarked example is explainable
from its row. Existing numerical/verdict fixtures continue to pass. Before/after
1280px screenshots show the difference, with phone smoke review.
## Assumptions
There is no single global finding rank. Preserve ranked relationships; use stable
coverage slots for existing zero, relation, group, cycle and gap evidence, filling
remaining slots in artifact order. No new importance score or domain inference.
