---
status: proposed
author: claude:dg#configure
date: 2026-11-04
---

# Intent: spec012 configurator page

1. DEC-067's wording reached this builder through the lead session, not as a file in
   `docs/decisions/`. It is quoted in the spec as relayed; Zach's own record should land
   in `docs/decisions/` separately.
2. "Exclude" read narrowly as `exclude_from_target`. Removing a column from profiling
   would hide its findings, which DEC-067 item 4 forbids; it needs its own decision.
3. Section omission changes views (HTML, Markdown, PDF, PPTX) only. The artifact keeps
   samples and missingness patterns, so `render` of the same artifact is consistent and
   nothing measured is lost. If omission is wanted for privacy (sample rows hold raw
   values), that is a different feature: dropping data from the artifact.
4. Optional sections offered: `samples` and `missingness_patterns` only. Findings, the
   dataset summary, "What the data cannot tell", relations and provenance are not
   optional, because each carries findings or context.
5. `bins` applies to every histogram (numeric values, positive log view, string
   lengths). The default rule (sqrt(n), capped at 10) is unchanged and now disclosed in
   the artifact (`bin_rule`) and the report's dictionary.
6. Suggestions: only a date reading (>=80% of nonmissing values parse under one named
   format) is suggested, because it is a lexical fact. No target is suggested; candidate
   reasons are type, populated share and distinct count. Interval pairs are offered in
   both directions because direction is a domain declaration.
7. Out-of-range numbers typed into the page are flagged and not emitted (the Python
   generator applies the same rule), so a generated file never fails validation on them.
8. No time-series / granularity knob: `config.py` here has no such key (another builder
   adds `time_series` on 011). The page lists it as an extension point.
