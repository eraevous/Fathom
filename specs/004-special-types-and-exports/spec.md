# Feature Specification: Special types and optional exports

**Branch**: 004-special-types-and-exports | **Created**: 2026-11-01
**Status**: Accepted scope with proposed implementation readings.
**Input**: HO-20261102-001; follows completed spec003 on a stacked branch.

Serves: P0@2, FT-R12@1, FT-R13@1, FT-R4@2, DG-RB@1, DG-RE@1,
DG-RF@1, DG-D5@2, DG-D6@1.

## Clarifications

Checks establish local syntax/range only, never existence, ownership, sensitive
status or correctness. No network lookup. Exports use saved artifact only; optional
dependencies never prevent core HTML/Markdown output. No quality score or new pairs.

## User Scenarios & Testing

### US1 — Inspect special-type problems (P1)

A reader sees inferred or human-overridden phone/email/URL/latitude/longitude types,
counts, bounded examples, domains and typed findings for invalid formats/ranges,
phone placeholders and test emails. No value is corrected and no PHI/PII is tagged.
Independent test: planted/clean tables, exact counts and absence of network calls.

Acceptance: 000-000-0000, test@test.com, malformed URLs and coordinates beyond
±90/±180 are surfaced; benign synthetic formats and boundary values are decoys.
Human string overrides suppress special routing while retaining the inference.

### US2 — Share a saved report (P1)

A reader exports a saved artifact to PDF and PowerPoint through optional extras.
PDF contains summarized findings and first/last/random sample tables. PowerPoint
has summary, key findings and labelled charts with one topic per slide. All files
are deterministic for fixed artifact/dependencies; core reports still render when
extras are absent. Independent test: open generated files, inspect contents, and
compare repeated/fresh-process bytes with explicit missing-dependency tests.

## Requirements

- FR-001: Infer labelled special types by explicit names or strong lexical evidence;
  support human overrides and retain reasons/alternatives.
- FR-002: Phone format and placeholder counts/examples; email syntax, domains and
  test addresses; HTTP(S) URL structure/domains; independent latitude/longitude
  range counts/examples. Counts are local checks, not verified domain facts.
- FR-003: Preserve core metrics/raw values, type routing, evidence, uncertainty,
  generator and diagnostic/clean-decoy requirements. No sensitive-data tagging.
- FR-004: Add optional PDF and PowerPoint exports derived exclusively from the saved
  artifact. PDF uses summarized view plus samples; slides contain summary, key
  findings and charts, one topic per slide; chart axes/title stay labelled.
- FR-005: Missing export dependencies yield explicit unavailable status and keep
  HTML/Markdown; no crash or silent success. Fixed metadata/ZIP times/seeds give
  repeatable bytes. Report unsupported-glyph substitutions explicitly for PDF.
- FR-006: Preserve old artifact views and CLI errors; verify builder found/missed
  tables against acceptance, disclose limits and no independent outcome claim.

## Key Entities

Special-type inference/override, format/range statistics and evidenced findings;
export bundle (core views, optional binaries, deterministic export-status.json).

## Success Criteria

SC-001: Each special check has a violating fixture and clean decoy with exact counts.
SC-002: PDF opens with summary/samples and PPTX opens with topics/charts from the artifact.
SC-003: Repeated and fresh-process PDF/PPTX bytes match; missing extras preserve core reports.
SC-004: PR lists planted/late-table found/missed/false alarms and export limitations.

## Assumptions

Phone validation is syntactic, not regional allocation. Email grammar is a practical
ASCII subset; URLs use HTTP(S), without access checks. Geographic readings depend
on names/overrides and assume degrees, labelled inferred. No geocoding or map pairs.
Export font/glyph limitations and potentially large slide counts are disclosed.
