# Feature Specification: Report layout and advanced univariate understanding

**Branch**: 003-report-and-univariate | **Created**: 2026-11-01
**Status**: Accepted scope; FT-R14 detail and implementation readings remain provisional.
**Input**: HO-20261102-001.

Serves: P0@2, FT-R6@3, FT-R9@1, FT-R10@1, FT-R11@1, FT-R14@1,
FT-R4@2, DG-RB@1, DG-RE@1, DG-RF@1, DG-D5@2, DG-D6@1.

## Clarifications

Agent readings: a labelled title/description precedes dictionary, provenance,
summary, findings, relations. Sample tables sit inside the dictionary section.
Technical data remains collapsed; the existing full-finding switch stays intact.
FT-R14's details are implemented as proposed, with limitations and suggested
changes reported rather than accepted. No quality score or new pair methods.

## User Scenarios & Testing

### US1 — Understand and inspect the table (P1)

A reader gets a human-supplied or explicitly inferred title/description, dictionary
examples and first/last/random sample rows with recorded settings, then provenance,
summary/usefulness/unknowns, typed findings and relations. Technical detail is
collapsed. Independent test: saved-artifact reports, exact section order, sample
indices/seed, truncation markers and one-click full detail in a browser.

Acceptance: 50-row synthetic input yields 20 rows in each view; random selection
is reproducible, without replacement within a view; small inputs return all rows.
Human text wins; inferred descriptions disclose their filename/schema basis.

### US2 — Learn from richer per-column profiles (P1)

A reader sees numeric distribution/box plots; textual/categorical composition;
and parsed temporal coverage/counts. Evidence highlights repeated identifiers,
implausible-zero candidates, ambiguous/two-digit/placeholder/future dates and
univariate patterns while preserving raw values and uncertainty.

Acceptance: common English release dates parse; two-digit-year ambiguity and
future-normalized dates are findings; $0 gross and repeated titles are surfaced.
Every diagnostic has a violation and clean decoy; exact metrics match hand work.

## Requirements

- FR-001: Implement FT-R6@3 order with title/description first and technical internals hidden.
- FR-002: Configurable first/last/random rows (default 20), recorded fixed seed,
  raw-value note, visible truncation and per-column examples; artifact-only views.
- FR-003: Every chart has a descriptive title and labelled axes with units or counts.
- FR-004: Config title/description are human; fallback filename/schema description is inferred with basis.
- FR-005: Numeric zeros/negatives counts/shares, integer/noninteger counts,
  percentiles 1/5/25/33/50/66/75/95/99, skew/kurtosis interpretations, common/rare
  values, histogram and box view; expose numeric formatting assumptions.
- FR-006: Text/category candidate blanks, lengths, case, special characters,
  common substrings, entropy, top-N coverage, rare levels and top-value bars.
- FR-007: Common date formats with inference/ambiguity labels; earliest/latest/span,
  weekday/month/quarter/year counts, large gaps, placeholder/implausible dates,
  lag-1 count autocorrelation and counts-over-time chart.
- FR-008: Repeated identifier-like values and zeros against large nonzero quantities
  become evidenced findings/questions/actions, not unlabelled domain facts.
- FR-009: Deterministic inputs/seed/artifact views; existing core/statistics degradation,
  legacy artifact rendering, local-only processing and all prior bounded pair behavior remain.
- FR-010: Builder planted/clean/late tables checked against docs/acceptance.md with
  found/missed ledger; no independent acceptance, quality score, FT-R7/8 or AI layer.

## Key Entities

Dataset identity with provenance; bounded sample-row windows; per-column univariate
statistics, parse evidence and chart specifications; typed findings; unchanged
version-1 profile with additive fields.

## Success Criteria

SC-001: Exact samples and metrics agree with synthetic expectations.
SC-002: All charts carry labels/titles and raw-row text is visibly truncated/escaped.
SC-003: Named date, zero and identifier misses become report findings on builder tables.
SC-004: Fresh-process output and saved-artifact rendering match bytes.
SC-005: PR discloses found/missed, narrower readings and proposed FT-R14 changes.

## Assumptions

Only local CSV/wide data. Unspecified semantics remain questions. Calendar parsing,
substrings, rarity and plausible-zero thresholds are transparent readings, not
owner-accepted detail; no current-time-dependent inference or fuzzy date correction.
