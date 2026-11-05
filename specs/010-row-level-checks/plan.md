# Plan: Row-level and temporal structure checks

Python 3.12; no new dependency. New module `src/fathom/rows.py` called from
`profiler.profile` after `quality_profile`; emits findings through the existing `finding`
callback, so the renderers need no change (findings section shows the message, which
carries the count and positions; evidence holds the full measurement).

## Constitution check
PASS. Observations carry counts and the rule text; meanings are questions. Intervals are
human declarations only (DG-RB: unknowns stay unknown). Checks never enter pair selection
(DG-RC). Artifact first (DG-RE): `row_structure` is the stable key. Deterministic (DG-RF).

## Design
- `parsing.parse_datetime`: strict ISO date or date-time -> `datetime` (date-only as
  midnight, flagged). Used only for interval and duplicate-timestamp checks.
- `rows.row_structure(rows, columns, cfg, emit) -> dict` with keys `blank_rows`,
  `duplicate_rows`, `repeated_keys`, `temporal`, `intervals`, `interval_question`, `rules`.
- Repeated keys: scan columns in table order; skip a candidate whose partition equals an
  already-reported key; at most 3 keys; constant columns listed up to 10 (count kept).
- Temporal outliers on calendar dates (day resolution): period rule then IQR fence.
- `config.validate_config`: new optional `intervals` key.
- Existing `duplicates` finding message gains positions; its id is unchanged.
