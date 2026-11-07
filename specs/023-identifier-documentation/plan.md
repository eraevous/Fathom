# Plan: identifiers
## Technical Context
Python3.12, existing pandas/PyYAML, stdlib Counter/re/Decimal. No added dependency. Additive schema2 identifier metadata; legacy views remain supported.
## Constitution Check
One connector→profiler→artifact→view flow; typed evidence/unknown key meaning; role-based exclusions, no all-pairs. Public/synthetic fixtures; exact arithmetic and deterministic bounded output. Pass.
## Research
Spec Kit read-only research verified late target filters permit quality-pair re-entry; place central rank filter. Controlled role key must be removed from base_columns passthrough in both YAML implementations. Explicit schema.key is human, not name inference. raw integer IDs must avoid floats. See research.md.
## Design
Pure identifiers module computes role/key/format/numeric counts from raw cells after univariate role assignment and before selection. Per-column optional identifier metadata, typed findings and dedicated shared view helpers. No hidden owner thresholds. summary_tables skips IDs and lists reasons. target_candidates rejects identifier target; rank_pairs filters every candidate touching an ID before budgeting. Native role selector/suggestions use existing configure schema/YAML paths. Panel metadata documents declared series-key components and actual series-entry anchors without altering signal calculations.
## Validation
Fixtures/tests before code; role/quantity/empty/huge-ID/duplicate/gap/quality-backdoor controls; real links and saved validation, YAML Python/Node parity. Full extras after records; exact offline reruns; actual1280/390light/dark profile/configure/panel screenshots. Pinned AEC edges/check/impact.
