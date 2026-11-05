# Plan
Existing stdlib date/regex, pandas and renderers; no dependency. Explicit-only YEAR
in shared parsing/config; add annual floor/advance/calendar in both existing engines.
Default auto selection gains year only for declared YEAR; no analysis additions for
other formats. Annual edge coverage includes the whole declared year rather than
one anchored day. Panel gets a time-column date_format key, YEAR requires period year.
Suppress subannual univariate distributions from anchors; label precision in the
first overview table. Complete parse failures retain invalid counts and emit format
coverage/suggestions without fallback; console warning and exclusion guidance.
Tests first, synthetic fixtures and clean numeric/no-match/ordinary-date decoys.
Then full extras suite after appending convention-correct evidence, AEC checks/impact,
offline replay and actual report screenshots. Constitution gates pass:single artifact,
explicit declarations, typed evidence, no new analysis selection or accepted thresholds.
