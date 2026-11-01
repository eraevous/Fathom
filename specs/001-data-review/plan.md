# Implementation Plan: Data review to decisions

**Branch**: `001-data-review` | **Date**: 2026-11-01 | **Spec**: [spec.md](spec.md)

## Summary

Implement the three stories as one small vertical slice: CSV → GuideDataFrame →
Profiler → ProfilingResult → saved JSON → Markdown/HTML. An evidenced review queue
and human working record make the table actionable. Target-selected summaries
and saved-result comparison complete the bounded loop. No remote subsystem.

## Technical Context

**Language/Version**: Python 3.12+.
**Primary Dependencies**: pandas 2.2.3 (canonical frame), PyYAML 6.0.3 (safe config).
Optional scipy >=1.14,<2 adds p-values only. setuptools >=68 builds the package;
pytest 9.2.0 verifies behavior. Existing AEC pin verifies records. Every direct
third-party dependency is justified in [research.md](research.md).
**Storage**: local CSV/config input, versioned JSON and static report files.
**Testing**: pytest with hand-calculated synthetic fixtures, violating/clean
pairs per diagnostic, subprocess reproducibility, hostile text and CLI failures.
**Target Platform**: local Python CLI/library; offline reports in modern browsers.
**Project Type**: library and thin CLI.
**Performance Goals**: no unsupported throughput promise; bound pair output to 20,
frequencies to 10 and examples to 3 per column. Local tables fit in memory.
**Constraints**: deterministic outputs for fixed dependencies; unknowns stay unknown;
no original data alteration; no sensitive data, network calls or narrative engine.
**Scale/Scope**: single CSV/wide, five semantic types, two pair routes, three output
views and aggregate before/after comparison.

## Constitution Check

Pre-research and post-design gates both PASS:

| Charter rule | Implementation/verification |
| --- | --- |
| 1 One flow | connector owns input, profiler alone bridges the two models; renderer reads only result |
| 2 Typed findings | findings have kind/generator/evidence/uncertainty/provenance; tests/test_understanding.py |
| 3 Label inference | effective override separate from retained inference; alternatives; routing tests |
| 4 Question/budget | no target gives no pairs; deterministic target screening and exclusions; pair tests |
| 5 Compare | saved profiles and context first; aggregate deltas, unknown lineage; comparison tests |
| 6 Artifact | schema version 1; render saved result only; renderer/CLI tests |
| 7 Verification | violating/decoy fixtures; metrics, routing, missing scipy, fresh-process bytes |
| 8 Public | only authored synthetic fixtures and code; review staged files |

No charter exception. April breadth is explicitly deferred under the later DG-D1
outcome definition, not silently declared complete. See the intent note.

## Project Structure

```text
specs/001-data-review/{spec,plan,research,data-model,quickstart,tasks}.md
specs/001-data-review/contracts/cli.md
codex_++/intents/2026-11-01__data-review.intent.md
src/fathom/{__init__,__main__,models,config,connectors,profiler,renderers,cli}.py
tests/{test_understanding,test_pairs,test_outputs,test_cli}.py
tests/fixtures/{review,revised,clean}.csv
tests/fixtures/{review,revised}.yaml
pyproject.toml
```

**Structure Decision**: small modules mirror the accepted layers. No registry,
plugin framework, API server, transform engine or frontend is necessary. The
artifact is validated in models; config validation is separate from metric logic.

## Implementation sequence

1. Package and models/config/strict connector; records precede these files.
2. Write synthetic decision/routing fixtures and tests, then profiler and renderer.
3. Add bounded pair routes and optional enrichment with unavailable status.
4. Add comparison and CLI, round-trip/fresh-process verification and README.
5. Regenerate AEC edges, record implementation claims and bounded test evidence;
   review diff, run checks, push feature branch and open one PR with CLA unticked.

## Validation and drift

Use `python -m pytest`, CLI quickstart and AEC checks. Recheck the purpose before
adding a subsystem or changing responsibilities. Record observed limitations in
validation.md and PR. Conformance does not prove most-project usefulness or owner
acceptance. Stop immediately after opening the first MVP-slice PR.
