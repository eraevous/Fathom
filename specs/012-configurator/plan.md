# Plan: Configurator page

Python 3.12; no new dependency (page JS is inline, hand-written). New module
`src/fathom/configure.py`; CLI `configure` subcommand; `config.read_config` split out of
`load_config` so the page can keep a passed-through raw config.

## Constitution check
PASS. Suggestions are observable facts with reasons, never relevance (DG-RB). The target
list is unranked (DG-RC). Artifact first (DG-RE): the page is built from the profile and
the profile is written beside it; the report reads `report` settings from the artifact.
Deterministic (DG-RF). Evidentiary thresholds are not configurable.

## Design
- `build_schema(doc, frame, raw_config)`: columns with facts and suggestions (type
  temporal + date_format when >=80% of nonmissing values parse under one DATE_FORMAT;
  ambiguous ties suggest no format), target candidates (numeric/categorical/boolean,
  populated, not all-distinct text), interval suggestions (both directions of each
  temporal pair, <=10 pairs), knobs, sections, fixed rules with sources, extension
  points, passthrough `base`, and `initial` selections from `--config`.
- `config_yaml(schema, selections)`: emit only non-default values; ordered keys;
  every string double-quoted with \u/\U escapes for non-ASCII; reserved-word keys quoted.
  `YAML_JS` mirrors it line for line.
- `univariate.bin_count/bin_rule`; histograms carry `bin_rule`; profile document gains
  `report: {generator, bins, bin_rule, omitted_sections}`.
- Renderers: `omitted(d)`, `omitted_notes(d)` and `bins_note(d)`; exports drop omitted
  keys from their view.
