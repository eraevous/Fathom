# Feature Specification: Time series (temporal structure)

**Feature Branch**: 011-time-series (stacked on 010-row-level-checks, PR #20)
**Created**: 2026-11-04 (CT) | **Status**: builder readings provisional, for Zach to accept.
**Input**: Zach (owner, high priority): "Add Time Series analyses to Fathom, including different
versions of sparsity (frequency, amplitude, wavelength, duration) and breakdowns of ACF/PACF and
other signals in various granularities." Kate (ChatGPT) design notes, taken as proposals.
Serves: P0@2, DG-RA@1, DG-RB@1, DG-RC@1, DG-RE@1, DG-RF@1. Proposed: FT-TS1-R1@1.

## User scenarios

### US1 — Observation process before structure (P1)
Given a declared series, Fathom reports raw rows, rows with a parsed time, missing/unparsed time,
distinct timestamps, rows repeating a timestamp, and per granularity the periods in span, the
**missing observations** (value series: no row, or rows with no parsed value), **explicit zeros**
(value sums to 0) and **periods with no event** (event series, counted as 0; the table cannot say
whether the process was observed). Missing periods and zeros are never merged.

### US2 — Four sparsity dimensions × granularities (P1)
Zach's vocabulary kept; intermittent-demand terms only as aliases.
- **Frequency**: zero share; inter-event interval in periods (mean = ADI alias).
- **Amplitude**: non-zero quantiles; CV² of non-zero values.
- **Wavelength**: ACF (pairwise-complete) and PACF (Durbin–Levinson) of values and of the
  occurrence indicator to `max_lag`, 95% band ±1.96/√n, dominant lags, calendar lags (24/168 h,
  7 d, 52 w, 12 m), periodogram peak only with the `stats` extra (else "not computed").
- **Duration**: zero-run and non-zero-run (burst) lengths; a missing period ends a run.
Reliability: n < 30 insufficient; zero variance undefined; lag > n/4 poorly supported.

### US3 — Temporal structure profile (P1)
Per series, signals (autocorrelation in values, in occurrence, repeating cycle, zero periods,
bursts) listed as present / absent / insufficient evidence by granularity, each with its rule.
"Present" for autocorrelation uses a family-wise (Bonferroni) band over the supported lags so that
white noise is quiet about 95% of the time. Questions, not interpretations: gaps ("unobserved or
nothing occurred?") and a dominant cycle ("a known schedule?").

### US4 — Unit of analysis (P2)
Single series core; optional `by:` analyses the top N groups by row count (default 5, max 20);
other groups and missing keys are counted, not analysed. Zach's open question (series vs
collection) is not settled here.

## Requirements
- FR-001: Config `time_series: [{time, value|null, by?, granularities: [auto|hour|day|week|month], max_lag?, top_n?}]`, declared only.
- FR-002: Undeclared, with a temporal and a numeric column: one question suggesting a declaration.
- FR-003: Artifact key `time_series` (additive; schema_version unchanged); report section "Temporal
  structure" with tables, ACF/PACF stem plots for two granularities, lag tables, rules.
- FR-004: Standard library core; scipy optional; deterministic; no runtime dates; no cleaning.

## Out of scope
Detrending, differencing, seasonal decomposition, cross-correlation between series, time zones,
sub-hour granularities, PDF/PPTX export of the section, collection-level summaries across groups.
