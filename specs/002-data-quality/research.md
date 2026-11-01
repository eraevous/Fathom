# Research decisions

Decision: use only repository wording and the slice-1 implementation. The absent
reference and unseen acceptance tables are not accessed. Alternatives: importing
an older report would violate scope; adding new visualization/statistics libraries
would increase machinery without serving these quality rules.

Decision: native checkbox/CSS plus details/summary, with plain Markdown fallback.
Rationale: one-click offline global switch and individual evidence disclosure
without external assets, scripts, analytics or nondeterministic IDs.

Decision: simple transparent heuristics with coverage metadata. Rationale: useful
quality evidence must remain distinguishable from domain explanation. No tests
can establish that a suspected sentinel is truly missing, or that a date gap is
an acquisition error. The report asks for those confirmations.

Decision: preserve version 1 with additive optional fields. Legacy results can be
rendered using stored measurements; complete-row counts unavailable there are
labelled unknown, not reconstructed from marginal null counts.
