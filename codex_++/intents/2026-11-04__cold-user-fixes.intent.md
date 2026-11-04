# Intent: spec009 cold-user fixes (claude:dg#colduser)

1. `date_format` stays a named token, as committed in
   2026-11-01__report-univariate.intent §6 and enforced by `DATE_FORMATS`; the cold
   user's strftime pattern is still rejected, now with the accepted names. Accepting
   strftime would be a new config surface; narrower reading taken.
2. `ISO_DATETIME` keeps only the calendar date. Offsets, fractional seconds and
   one-digit hours are not recognized (narrower reading); time-of-day profiles are
   not in FT-R14 and are disclosed as not analysed in `parse_basis`.
3. Temporal columns no longer hit the near-unique identifier rule in target
   candidates; they stay excluded via the existing unsupported-type-pair reason.
4. `validate` stays JSON (CLI contract: "prints the resolved schema"; test_cli parses
   `mode`). Echoed settings are an additive `resolved` key rather than prose lines.
   `profile` prints two plain lines on stdout. Both are deterministic.
5. Export exit code stays 0: spec004 contracts/export.md ("Unavailable dependency is
   explicit in export-status.json and exit0") and FT-R13@1. The stderr line serves
   FR-005's "no silent success".
6. Contrast threshold and zero-share: recorded choices / outside scope; proposals in
   docs/decisions/2026-11-04-proposed-contrast-threshold.md. No behaviour change.
7. Records append after main's last line; open PR #16 also appends, so the second to
   merge needs a trivial append-order rebase and an edges regeneration.
