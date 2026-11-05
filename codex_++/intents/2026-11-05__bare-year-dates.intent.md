# Intent: declared years, not inferred dates
E4V9 addition4. Open PR27/28 listed. Stack on28 at80ee25d because YEAR precision
must work with its partial-edge coverage, rather than reporting an anchored Jan1
as a one-day annual stub. No reuse from any earlier implementation.
Explicit YEAR only; ordinary numeric columns remain numeric. Jan1 is an anchor,
never an observed month/day. Annual profiles/panels need native year calendars;
no generated fine-grain views or automatic aggregation. Existing ISO window bounds
and panel year limits retained. Existing temporal target association stays unsupported,
with useful routing guidance; scope is parsing/presentation, not a new association.
No domain knowledge inferred from the relayed public panel or its column names.
