# .aec: purpose and justification records (AEC)

- `records.jsonl`: append-only reasoning records (purpose, requirements, claims, evidence, decisions,
  authorities). Never edit a line; append a new version. Vocabulary:
  https://github.com/eraevous/AEC/blob/main/docs/reasoning-vocabulary.md
- `edges.jsonl`: the structural snapshot of the code (`aec edges`). Regenerate it; never hand-edit it.
- `snippets/`: the Claude Code hook and CI job as `aec init` generated them. Both are installed
  byte-identical, at `.claude/settings.json` and `.github/workflows/aec.yml`.

The purpose stub `P0` has been replaced; `AGENTS.md` lists the accepted records to read first.

All AEC results are structural: they show what changed and what relied on it, not whether the
remaining evidence is good enough. That stays a review question.
