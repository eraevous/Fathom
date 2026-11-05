# Plan: Time series

Python 3.12; no new dependency (scipy already the optional `stats` extra; `scipy.signal.periodogram`
is imported lazily and its absence is reported). `statistics.NormalDist` gives the Bonferroni z.

## Constitution check
PASS. Series are human declarations (DG-RB: no domain meaning from names). Missing vs zero vs
absent event is reported, never imputed (no auto-cleaning). Nothing enters pair selection (DG-RC).
Artifact first (DG-RE): `time_series` key; the report section is derived. Deterministic, optional
dependency degrades (DG-RF).

## Design
- `src/fathom/timeseries.py`: parse time (strict ISO date-time, else the column's `date_format`
  as a date), regularise per granularity (floor; week = ISO Monday), per-period sum or row count;
  observation process; four dimensions; `correlogram` (ACF, PACF, bands, support, dominant lags,
  family-wise signal); `signals`; `informative` (charts for two granularities); findings via the
  existing `finding` callback, generator `rule:timeseries-v1`.
- `src/fathom/temporal_view.py`: tables and SVG stem plots in the repo's chart style; HTML and
  Markdown sections inserted after Findings.
- `config.validate_config`: `time_series` key.
- Caps: 100,000 periods per granularity; 2,000 regularised periods stored per granularity in the
  artifact (count of the rest kept); lag defaults 168/28/26/24.
