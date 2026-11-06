# Feature Specification: Terminal Liftoff configuration
Created2026-11-05; provisional. Serves:P0@2,DG-RA@1,DG-RE@1,FT-LIFT-R1@2,FT-DEMO2-R1@1.
Input:HO-DG-20261105-E4V9 item2; main ad16fe6. Independent of PR26.
## User Scenarios & Testing
### US1 (P1): Terminal-only two-stage flow
`guide liftoff DATA.csv --out DIR --yaml PATH` writes exactly the untouched page's
YAML, without a browser. Given current unticked suggestions, it is {} plus newline;
no inferred target/type/interval/series is accepted. The no-JS fallback points at
this command. Users edit YAML explicitly before profile.
### US2 (P1): Explain exclusions honestly
The profile stderr summary splits config exclusions, unsupported types and budget
omissions. Other eligibility exclusions retain a separately named category and
reasons; never imply the human excluded them. Target itself is not an exclusion.
### Edge cases
Nested YAML path; path collides with source/report artifact; empty defaults; no target;
no excluded columns. Optional --yaml preserves existing output when omitted.
## Requirements
FR1:Exact page/CLI default YAML bytes. FR2:No applied suggestion or new --accept
semantics. FR3:No-JS command is visible. FR4:Exclusion categories retain reasons.
FR5:No network/dependency/verdict change; deterministic repeated runs.
## Key entities
Default selection:existing configurator initial state. Exclusion:column/reason,
classified for display only. No analysis routing changes.
## Success criteria
A terminal user runs both stages with generated YAML; exact JS/Python bytes match.
Synthetic config/unsupported/budget/eligibility decoys are distinct in stderr.
## Assumptions
Only --yaml is needed (handoff says and/or --accept). Defaults remain unticked;
{} is deliberately honest, not an auto-accept feature. Other eligibility is a
fourth bucket because identifiers/constant/copy exclusions are not type failures.
