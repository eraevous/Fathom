# Feature Specification: Row-level and temporal structure checks

**Feature Branch**: 010-row-level-checks (stacked on 009-cold-user-fixes, PR #19)
**Created**: 2026-11-04 (CT) | **Status**: builder readings provisional, for Zach to accept.
**Input**: cold-user run on seaborn `taxis` (6,433x14) and the fathom-002 judge note:
pandas showed row-level structure Fathom missed (dropoff == pickup, duplicate pickup
timestamps, a pickup outside the bulk month; blank rows and k-rows-per-key structure
in the fathom-002 table).
Serves: P0@2, DG-RA@1, DG-RB@1, DG-RC@1, DG-RE@1, DG-RF@1, FT-R14@1. Proposed: FT-ROW2-R1@2 (supersedes @1).

Relation to open PR #17 (spec-only `specs/009-row-level-checks`, unaccepted): this slice
builds a structure-only subset (blank rows; repeated-key multiplicity and within-key
constants). It does not build #17's aggregate label cues, one-positive-per-key or
conditional zeros. It reuses #17's modal group size 2..20 covering >=90% of keyed rows,
at most 10 example positions and 1-based data-row positions, and departs from #17 in
three places (builder readings, for Zach to reconcile):
1. Key candidates are screened by repeat pattern over every column, not by name cues
   (`id`, `individual`, ...), because name cues would read domain meaning into names.
2. A key needs >=10 distinct values (#17: >=3), so small balanced designs stay quiet.
3. #17's year-heading value scope is replaced by "not wholly blank, empty in every
   numeric column (>=2 numeric columns)".

## User scenarios

### US1 — Rows that carry no values or repeat exactly (P1)
Given a table with wholly blank rows, Fathom reports the count and the first 10 row
positions and asks what a blank row stands for. Exact duplicate rows keep the existing
`duplicates` finding and gain the first 10 positions of repeating rows. Decoy: partially
blank rows are not wholly blank.

### US2 — Repeated-key structure (P1)
Given a column in which values repeat with one regular multiplicity k (modal group size
2..20, >=10 distinct keys, groups of size k cover >=90% of nonmissing rows), Fathom says
"most nonmissing rows belong to groups of exactly k by <col>" with the coverage share, and lists columns constant within every
group of that key that vary between keys. Phrased as a question ("would analysis need to account for this grouping?"), never as a declared key.
Decoy: a column whose values repeat irregularly is silent. Columns with the identical
partition are reported as the same grouping, not as separate keys.

### US3 — Observations of selected temporal structures (P1)
Not anomaly detection: these observe a few named structures. On temporal columns: (a) values outside the dominant calendar month or year when >=99%
of values share it, and values beyond Q1 - 3xIQR / Q3 + 3xIQR (IQR > 0); (b) duplicate
timestamps when values carry a time of day and >=90% of values are distinct; (c) declared
intervals `intervals: [{start: a, end: b}]` give end < start, end == start, and the
duration distribution in seconds, parsed from the full date-time and disclosed as such.
With >=2 temporal columns and no declared interval, one question only. Decoys: clean date
column silent; undeclared pair produces the question and no counts.
Limits: (a) works at day resolution, and the period rule fires only for values across a
month/year boundary, so same-day or same-month stragglers are never reported. (c) only
strict ISO date/date-time pairs are measured; unparsed pairs (MM/DD/YYYY, Z/offset
suffix, fractional seconds) are counted in the message and raise a question, and
"0 of 0" is never shown as a clean result.

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
  proposal (codex_++/intents/2026-11-04__contrast-threshold-proposal.intent.md §2) stands untouched.
- FR-007: README gains one short "What it finds" bullet list addition.

## Out of scope
#17's value-scope inference, aggregate cues, one-positive-per-key, conditional zeros;
composite keys; time zones/offsets; inferred interval pairs; any cleaning.
