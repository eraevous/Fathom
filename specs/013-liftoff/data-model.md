# Additive schema2 liftoff block

Top-level kind/profile and default fields remain valid and unchanged. `liftoff`
has version1, stage/discovery, effective_configuration{}, configuration schema,
automated_findings, previews.intervals/time_series and coverage/rules/limits.
Each preview has status/provisional, exact declaration, result, typed findings
and engine dependencies/rules. Evidence paths point under that preview, not an
empty ordinary declared-series/interval block. No accepted interpretation stored.

Series controls are optional schema additions; ordinaryconfigure schema retains
its base/passthrough. Liftoff stores all eligible series candidates but previews
first20; configuration can select those offered candidates. No data frame stored.
