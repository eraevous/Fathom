# Feature Specification: Row-level and temporal structure checks

**Feature Branch**: 010-row-level-checks (stacked on 009-cold-user-fixes, PR #19)
**Created**: 2026-11-04 (CT) | **Status**: builder readings provisional, for Zach to accept.
**Input**: cold-user run on seaborn `taxis` (6,433x14) and the fathom-002 judge note:
pandas showed row-level structure Fathom missed (dropoff == pickup, duplicate pickup
timestamps, a pickup outside the bulk month; blank rows and k-rows-per-key structure
in the fathom-002 table).
Serves: P0@2, DG-RA@1, DG-RB@1, DG-RC@1, DG-RE@1, DG-RF@1, FT-R14@1. Proposed: FT-ROW2-R1@1.

Relation to open PR #17 (spec-only `specs/009-row-level-checks`, unaccepted): this slice
builds a narrower, structure-only subset (wholly blank rows; repeated-key multiplicity
and within-key constants). It does not build #17's year-heading value scope, aggregate
label cues, one-positive-per-key or conditional zeros. Where #17 sets a threshold this
slice reuses it (modal group size 2..20 covering >=90% of keyed rows; at most 10 example
positions; 1-based data-row positions).

## User scenarios

### US1 — Rows that carry no values or repeat exactly (P1)
Given a table with wholly blank rows, Fathom reports the count and the first 10 row
positions and asks what a blank row stands for. Exact duplicate rows keep the existing
`duplicates` finding and gain the first 10 positions of repeating rows. Decoy: partially
blank rows are not wholly blank.

### US2 — Repeated-key structure (P1)
Given a column in which values repeat with one regular multiplicity k (modal group size
2..20, >=10 distinct keys, groups of size k cover >=90% of nonmissing rows), Fathom says
"looks like k rows per <col>" with the share, and lists columns constant within every
group of that key that vary between keys. Phrased as a question, never as a declared key.
Decoy: a column whose values repeat irregularly is silent. Columns with the identical
partition are reported as the same grouping, not as separate keys.

### US3 — Temporal structure (P1)
On temporal columns: (a) values outside the dominant calendar month or year when >=99%
of values share it, and values beyond Q1 - 3xIQR / Q3 + 3xIQR (IQR > 0); (b) duplicate
timestamps when values carry a time of day and >=90% of values are distinct; (c) declared
intervals `intervals: [{start: a, end: b}]` give end < start, end == start, and the
duration distribution in seconds, parsed from the full date-time and disclosed as such.
With >=2 temporal columns and no declared interval, one question only. Decoys: clean date
column silent; undeclared pair produces the question and no counts.

## Requirements
- FR-001: Each new finding is an observation (counts, share, rule text, <=10 positions)
  with a paired question; generator `rule:rows-v1`; never an action or selection input.
- FR-002: Artifact key `row_structure` (additive; schema_version unchanged) holds the
  stable evidence; HTML/Markdown findings show the count and positions via the existing
  findings section.
- FR-003: `intervals` config: list of {start, end}, both existing, distinct columns.
- FR-004: No interval inferred from column names (domain meaning); declaration required.
- FR-005: Deterministic ordering; no runtime dates; core dependencies only.
- FR-006: Zero-share finding is NOT generalised: no accepted spec allows it; the PR #19
  proposal (docs/decisions/2026-11-04-proposed-contrast-threshold.md §2) stands untouched.
- FR-007: README gains one short "What it finds" bullet list addition.

## Out of scope
#17's value-scope inference, aggregate cues, one-positive-per-key, conditional zeros;
composite keys; time zones/offsets; inferred interval pairs; any cleaning.
