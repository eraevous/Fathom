# Feature Specification: Declared identifiers and key documentation
Created2026-11-06; provisional; HO-DG-20261106-8RZJ PR B. Branch023-identifier-documentation from maina0fcf56. Kate first; Zach accepts/merges.
Serves:P0@2,DG-RA@1,DG-RB@1,DG-RC@1,DG-RE@1,DG-RF@1,FT-ID23-R1@1.
## User Scenarios & Testing
### US1 — Declare an identifier (P1)
Configurator role selector accepts identifier/quantity/default. Inferred identifier-like readings are observable suggestions, unticked; existing declarations prefill and can be changed. YAML preserves roles. An identifier is excluded from per-type distribution summaries and target ranking, with explicit reasons, including a declared identifier target and quality-pair backdoors.
Acceptance: numeric/string identifiers, human quantity override, undeclared near-unique suggestion, identifier target, no-target quality candidate and role round-trip.
### US2 — Understand a key (P1)
An Identifiers report section shows each declared/inferred identifier with basis, unique/nonmissing/complete-row-key status, missing cells, duplicate counts and examples/positions, observed length/character-class patterns and leading zeros. Numeric labels get exact ordering in input-row order and integer gaps/ranges (not inferred missing records). Repetition suggests a possible entity key or collisions, never declares domain meaning. Link matching repeated-key findings, declared time-series grouping and panel series IDs where present. Panel reports document declared key components and link actual series entries.
Acceptance: unique row-key decoy, repeated entity key with regular groups, missing/duplicate/mixed-format/leading-zero/gapped/decreasing/large-integer controls, panel key links, unknown/empty/legacy handling.
### Edge cases
No values gives unknown uniqueness. Missing values prevent a complete row key. Raw keys preserve leading zeros and lexical distinctions; numeric ordering is a separate reading. Gaps are counted as ranges, not expanded or treated as missing records. Exact arithmetic; no float collapse of large IDs. All examples bounded10 with omissions disclosed. No PIItagging, new group analysis, target rule/threshold change or domain inference.
## Requirements
FR1:explicit role control/unticked inferred suggestions and validated YAML. FR2:dedicated evidenced identifier summary in HTML/Markdown/export where supported. FR3:central distribution/ranking exclusions, including identifier targets/quality candidates. FR4:real repeated-key/series links only, no invented cross-file link. FR5:deterministic/offline/optional extras degrade, legacy loads, full extras before push and1280/390light/dark visual review.
## Key Entities
Identifier reading (basis, row/key counts, duplicate examples, format summaries, exact numeric order/ranges); declared role; evidence references and series links.
## Success Criteria
Planted key issues are readable without raw JSON; count/role/value/position tests agree exactly. Leading zeros and large keys survive. Unticked suggestions make no declaration. Every excluded identifier has a visible reason; no budget slot consumed by it. Real anchor links resolve. Repeat bytes and offline commands pass.
## Assumptions
Observed uniqueness is a candidate key, not an entity definition. Pattern variation is described, not labelled invalid without an owner rule. Numeric missing-label ranges do not claim missing rows. Identifier stats in panel describe whole raw input/key components, not training-model parameters. No new runtime dependency.
