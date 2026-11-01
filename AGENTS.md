# AGENTS.md: working rules for AI agents in Fathom

These rules apply to Codex, Claude Code and any other coding agent working here.

## What Fathom is

Fathom (formerly Data Guide) turns raw or semi-cleaned tabular data into understanding someone can use and pass on: an enhanced data dictionary, a diagnostic EDA engine and a repeatable working record. It is not an automatic plot generator. Understanding comes before modelling.

The MVP is **data to decisions**: decisions about the data, about other processes that turn data into decisions, or answers to questions (`DG-D1`). Its output should also work on its own as data documentation for most data projects (`DG-A1`).

**This repository starts with documents only, on purpose** (`DG-D4`). It is a test of how far a project gets when it is built from its guiding documents with AEC and Spec Kit. There is no earlier code to reuse.

## Read first, in order of precedence

1. **`.aec/records.jsonl`:** the purpose (`P0`), requirements `DG-RA` to `DG-RF`, direction `DG-D1`, assumptions `DG-A1` to `DG-A4`, and the decisions `DG-D2` to `DG-D4`. Zach accepted all of them. Read the latest version of each.
2. **`docs/decisions/`:** Zach's own words behind those records, by date.
3. **`CHARTER.md`:** the engineering rules (accepted).
4. **`docs/vision.md`:** the vision. It is a synthesis, not a specification.
5. **`docs/design.md`:** the April design, distilled. It was approved, but later records win over it.
6. **`docs/acceptance.md`:** how usefulness is judged (proposed, `FT-R4`). Check each slice against it before calling it done.

Where these conflict, follow the higher item and record the conflict. Don't settle it yourself.

## Authority

- **Design intent, scope and acceptance:** Zach. Agents propose, and only Zach accepts. Merging a PR doesn't accept anything.
- **Facts about a dataset:** the data and the people who own it. Fathom never states an inferred meaning as a domain fact.

## How to build: Spec Kit with AEC

Spec Kit skills are in `.agents/skills/`: `speckit-constitution`, `-specify`, `-clarify`, `-plan`, `-tasks`, `-analyze` and `-implement`. The AEC extension adds report-only hooks after specify, tasks and implement (`.specify/extensions/aec/`).

1. **Constitution.** `.specify/memory/constitution.md` is still the template. When you fill it, it must restate `CHARTER.md` and point to it. It must not add principles of its own. A principle the charter lacks is a proposal for Zach, recorded in an intent note.
2. **Specify, plan, tasks, implement, one feature at a time,** in `specs/NNN-name/`. Each spec names the records it serves (for example `Serves: P0@2, DG-RA@1`).
3. **Records come before code.**
   - For each feature, append a `requirement` record if the feature needs one that isn't there yet. Mark it provisional and say it is for Zach to accept.
   - When a feature is built, append a `claim` with `evidence` (the tests), linked to the code with `implemented_by` and `observed_on`.
   - Never edit an existing line; append a new version instead.
   - Vocabulary: https://github.com/eraevous/AEC/blob/main/docs/reasoning-vocabulary.md
4. **Record non-obvious trade-offs and unanswered questions** in an intent note, `codex_++/intents/<YYYY-MM-DD>__<topic>.intent.md`. Where a document is silent, take the narrower reading and write down that you did.

## AEC commands

```bash
pip install "aec @ git+https://github.com/eraevous/AEC.git@860b7815f208fac09c4e2ba57e5fbfe418ed2ba7"
python3 -m aec edges . -o .aec/edges.jsonl            # regenerate; never hand-edit
python3 -m aec check .aec/records.jsonl --edges .aec/edges.jsonl
python3 -m aec code-impact .aec/records.jsonl OLD.jsonl NEW.jsonl   # what a code change affects (two edge snapshots)
python3 -m aec source show <record-ref>              # the passage a record is anchored to
```

AEC results are structural. They show what changed and what relied on it; they don't show whether the work is good.

## Rules for what Fathom produces

These come from the accepted records and the charter.
- **Typed findings.** Each finding is an observation, interpretation, hypothesis, action or question. It names what produced it (a rule, a human, or later an AI narrative) and carries its evidence.
- **Inferred is labelled, not hidden.** Inferred types and readings are labelled as inferred until a human says otherwise. Useful results that rest on an inference are still shown, with the label (`DG-RB`).
- **Unknowns stay unknown.** What the table can't tell (the row unit, the generating process, the missingness mechanism) is reported as an open question, never as a guess.
- **The question selects the analysis.** No all-pairs (Cartesian-cross) explosions of metrics or plots (`DG-RC`).
- **Comparisons state context first:** snapshot dates, sources and transformations, before the measured deltas (`DG-RD`).
- **A machine-readable artifact is the interface.** Reports are derived from it (`DG-RE`).
- **Usefulness has a fallback.** Without a declared question, usefulness is judged by the general uses of documentation and EDA: reference, understanding, QA and validation (`DG-A4`).
- **AI narrative is a separate, labelled layer,** never mixed into rule findings (`DG-A3`). None is in scope until a spec says so.
- **Tests:** every check has a violating fixture and a clean decoy. Output is byte-identical across runs. A missing optional dependency degrades the output; it doesn't crash (`DG-RF`).

## Hard rules

- **This repository is public.** No real data, credentials, client or employer material, and no organisation-specific code. Fixtures are synthetic, or public datasets with their source stated.
- **Don't look at or copy from any earlier Data Guide implementation,** including the archived `eraevous/Data-Guide` repository and its history. Build from this repository's documents.
- **Every third-party dependency is justified in the plan,** and optional dependencies degrade cleanly.
- **Never edit lines in `.aec/records.jsonl`, `docs/decisions/` or other append-only files.**
- **Leave the CLA checkbox in the PR template unticked.** It is Zach's.
- **Never push to `main`, never force-push, and never merge.** Work on a branch and open a PR.

## Drift

Stop and check whether the plan still serves the purpose before you:
- add a subsystem;
- change a component's responsibility;
- contradict `docs/design.md` or a record;
- spend most of the effort on machinery rather than on what an analyst learns.

Write what you noticed in the PR description.
