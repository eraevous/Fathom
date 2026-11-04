# Plan: Cold-user fixes

Python 3.12; no new dependency. Additive artifact content only (schema version
unchanged): a new `parse_formats` value `ISO_DATETIME` and a longer `parse_basis`
string on date-time columns; existing fixtures contain no date-times, so no golden
artifact changes.

## Constitution check

PASS. Typing, not domain meaning: a lexical date-time is labelled inferred, with
alternatives retained. Artifact remains the interface; renderers unchanged. Missing
extras still degrade (FT-R13, spec004 FR-005: "no crash or silent success"; the
stderr line removes the silent part). Byte-identical outputs; CLI echo has no clock.

## Design

- `parsing.parse_date`: new branch for `\d{4}-\d{2}-\d{2}[ T]HH:MM(:SS)?`, hours
  0–23, minutes/seconds 0–59, returns the calendar date. Named token, consistent
  with the committed token reading of `date_format` (report-univariate intent §6).
- `config.validate_config`: error messages list `TYPES` / `DATE_FORMATS`.
- `target.target_candidates`: near-unique rule skips temporal columns; they fall
  to the existing "unsupported type pair" exclusion (spec007 plan: dates excluded).
- `univariate`: `parse_basis` discloses date-time handling; description sketch
  says row unit is declared when `row_unit` is set.
- `cli`: `summary_line`, export notice, additive `validate` JSON.

## Diagnoses (no behaviour change)

Contrast threshold and zero-share findings: see
`docs/decisions/2026-11-04-proposed-contrast-threshold.md`.
