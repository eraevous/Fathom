# Research decisions (repository documents only)

- Decision: use Python 3.12 and pandas 2.2.3. Rationale: AGENTS uses Python and
  design requires a DataFrame wrapper; pandas supplies that established container.
  Alternatives: bespoke table/frame risks departing from the canonical model.
- Decision: strict CSV parsing with stdlib csv, then pandas object storage.
  Rationale: preserve headers and lexical values; pandas defaults can erase
  leading zeros and interpret domain strings as nulls. No automatic cleaning.
- Decision: PyYAML 6.0.3 for non-interactive configuration, safe_load only.
  Rationale: YAML configuration is explicit in design; no custom parser.
- Decision: stdlib statistics/math and counted lexical values for core summaries.
  Rationale: small auditable metric surface; no plotting dependency is needed.
- Decision: optional scipy >=1.14,<2 for Pearson p-values; the coefficient and
  pairwise count are core. Rationale: tested statistical implementation, optional
  inferential context; assumptions are stated and p-values never select actions.
- Decision: pytest 9.2.0 for verification; setuptools >=68 for packaging; existing
  AEC tooling pinned to 860b7815f208fac09c4e2ba57e5fbfe418ed2ba7 for record checks.
  These are development tools, not runtime requirements. No other direct third
  party dependency. pandas' transitive numerical/date packages are managed by it.
- Decision: no research on external product patterns or archived code. All scope
  and architecture choices come from AGENTS, records, charter, design and vision.

All design unknowns are narrowed in the intent note and spec clarification log.
