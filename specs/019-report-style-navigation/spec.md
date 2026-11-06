# Feature Specification: Report typography and navigation

**Branch**:019-report-style-navigation. **Created**:2026-11-05. **Status**:provisional.
Input:HO-DG-20261105-WJZQ; relayed DEC-125 quote. Kate first; Zach accepts/merges.
Serves:P0@2,DG-RA@1,DG-RB@1,DG-RE@1,DG-RF@1,FT-R6@4,FT-R17@2,FT-STYLE-R1@1.

## User Scenarios & Testing

### US1 — Read the result before its machinery (P1)
A reader scans the Brief/profile/panel and distinguishes measured verdicts from
inferred readings, identifiers and evidence links without reading repeated hashes.
Acceptance: a planted-zero/contrast fixture exposes short verdict tokens, inferred
identity/type/unknown labels in italics, literal column/value/rule/hash text in
monospace; evidence remains available behind each finding. An ordinary sentence
and a column named `constant` are decoys: neither becomes a verdict by its name.
Exports use the same distinctions where the format allows. Existing text and
finding order are retained; only technical detail is collapsed.

### US2 — Reach a section on either screen size (P1)
Brief and profile offer the same keyboard-reachable navigation, containing only
available sections, with counts for counted objects. At phone width it starts
collapsed; a button opens it. Without scripts it becomes a static list. Print
hides it. Acceptance:1280px/390px, scripts on/off, no dead anchors or document
horizontal overflow. Report remains readable without scripts.

### Edge cases
Absent optional sections; legacy artifacts; hostile literal names/HTML; nested
technical details; dark theme; generated configuration scripts and chart geometry
must remain untouched. A short report does not gain empty navigation destinations.

## Requirements
FR1:One rule set in docs/report-style.md, shared by the output views. Bold verdict
tokens/deciding numbers only; italic inferred readings; underline links only;
monospace literal identifiers/values/rules/hashes. FR2:Bullets enumerate at least
three parallel facts; numbering denotes ordered steps. FR3:At most three visible
heading levels; evidence/uncertainty/provenance collapsed with verdict visible.
FR4:Shared accessible progressive navigation, static without scripts, hidden in
print. FR5:No JSON, ordering, verdict, threshold or palette change; deterministic,
offline and no runtime dependency. FR6:Key findings have no bold span longer than
N=8 words; every prose `(inferred)` is italic. Literal data is never reinterpreted
as a verdict or inferred assertion solely because it contains one of those words.

## Key Entities
A text run has a presentation role (plain/verdict/inferred/literal). A navigation
item has a destination, label and optional measured count. Both are derived views.

## Success Criteria
Same saved artifact bytes before/after, same bytes across reruns of each output;
short emphasis and inference fixture checks pass. Both sizes and scripts-disabled
views have usable links, visible verdicts and no document overflow. Optional
PDF/PPTX remain deterministic, with tested bold/italic/monospace text runs.

## Assumptions
Use top navigation at all widths to preserve full column/chart width and avoid
reflowing existing plots. Counts refer to stored items, not current disclosure
state. Only sections actually present are listed. N=8 is a style guard, not an
analysis threshold. Literal raw evidence/code/pre/SVG labels retain exact text.
