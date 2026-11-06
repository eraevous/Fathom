# Feature Specification: Paired findings, distribution summaries and tidy exports

**Branch**:020-distribution-summary. **Created**:2026-11-05 CT.
**Status**:provisional; HO-DG-20261106-XZSM / relayed DEC-126. Kate first; Zach merges.
Serves:P0@2,DG-RA@1,DG-RB@1,DG-RE@1,DG-RF@1,FT-R6@4,FT-R17@2,
FT-STYLE-R1@1,FT-VIEW20-R1@1,FT-TIDY20-R1@1,FT-PALETTE20-R1@1.

## User Scenarios & Testing

### US1 — Read related quantities separately (P1)
A reader sees the existing verdict as a parent and related group/rest, gap/SD,
before/after or other paired quantities as nested bullets, instead of one dense
sentence. HTML, Markdown and supported exports retain all facts and their order.
No line contains two or more comparison operators (=,≥,vs); literal identifiers
are not comparison operators. Existing gates are displayed, never recalculated.
Acceptance: a planted numeric group contrast and failed-gate decoy; multiple gates,
categorical rates, generic multi-comparison text and hostile/literal names. Technical
evidence stays closed. The original artifact and tidy message preserve source wording.

### US2 — Compare column distributions and transpose (P1)
After Key findings, the profile lists one compact summary table per effective type.
Rows name/link columns. Numeric metrics:n,missing%,distinct,mean,median,SD,IQR,skew,
zero%,min,max. Categorical/text metrics:n,missing%,distinct,top share,entropy,length
range. Temporal:span,parse coverage,declared period(s),stored univariate gaps.
Stored quantities only; missing metrics say unavailable rather than measuring more.
Tiny distribution marks accompany suitable stored numeric/text/coverage summaries.
A keyboard control transposes each summary in place. No-script hides controls and
retains the configured orientation. Report config sets columns_as_rows (default)
or metrics_as_rows; PDF/PowerPoint use it too. Wide export tables are paginated.
Acceptance: mixed types, constants, missing/invalid/all-missing, absent legacy stats,
coordinates, empty table, escaped names; both orientations, scripts on/off, reruns.

### US3 — Use flatter saved data (P2)
`guide export PROFILE --tidy DIR` creates deterministic stdlib CSVs:columns.csv
(one column/metric per row),findings.csv(one finding per row with flat evidence
fields),relations.csv and samples.csv when stored. Office extras are unnecessary.
Existing export --out works; --tidy can be combined with it. Nesting measurements
and a schema3/migration proposal are documented without changing schema2.
Acceptance: exact counts/values, raw strings/newlines, absent samples/relations,
nulls/empty containers, path collisions, loaded result immutability, socket denial.

### US4 — Read the proposed tool palette (P2)
Use the handoff's exact light/dark tokens and kind colors from the one palette
source. Actual text clears4.5:1 and informative graphics3:1 against surface AND
panel. Decorative backgrounds/borders are not data marks. Categorical marks avoid
reserved lime/red and nearby hues; all kinds retain text labels. No new assets.
Acceptance: exact token values; both backgrounds/modes; actual mark/foreground
colors including exports; opaque scatter marks; light/dark phone/desktop review.

### Edge cases
Zero denominators; unavailable rather than reconstructed means/SD for coordinates;
no calendar-coverage claim from parse coverage; no cadence inferred from chart bin
period; null statistics; long labels; one/many columns; transpose twice; no scripts;
missing optional exporters; source-order findings and first/last/random sample roles.

## Requirements
FR1:Nested related quantities and at most one comparison per rendered finding line.
FR2:All requested summary metrics from stored artifact, explicit unavailable state.
FR3:Real dictionary links, inline marks with exact textual equivalents, transpose
controls, config orientation; no-script/print fallback. FR4:Saved-artifact CSV export
without dependency/network or re-profiling. FR5:Reproducible nesting measurements,
proposal-only schema3 and compatibility plan. FR6:Proposed supplied palette, accessible
actual marks/text, no reserved status colors for data. FR7:No changes to measurements,
verdicts, thresholds, selection/finding order, schema2 fields/bytes or determinism.

## Key Entities
Derived finding tree; per-type summary table; render-only report options; flat metric
row/finding record/relation/sample; nesting-depth measurement; proposed palette roles.

## Success Criteria
Fixture controls and full extras pass; all original profile JSON bytes match baseline,
including when summary orientation changes. Transpose is reversible and keyboard
usable; default/no-script/export orientation agrees. CSV data/counts are reproducible
and faithful. No resource request, page overflow or inaccessible actual foreground
is introduced. Screenshots1280/390light/dark/script-off and actual exports reviewed.

## Assumptions
Stack survives on #28's017-period-coverage: #30 merged there through #29, not main.
Profile JSON remains the stable interface. report.summary_orientation is render-only;
saved render/export take explicit --config. n means stored valid/nonmissing count,
missing% uses all input rows; invalid counts remain in the dictionary. Parse coverage
is valid/nonmissing, not calendar completeness. Gaps are the stored univariate rule's
gaps. Periods are declared grains/YEAR precision, otherwise not declared. No new
statistical inference or entropy/cadence/expected-cell computation is added.

## PR34 review correction (2026-11-06)
Serves:FT-VIEW20-R1@2 (provisional). Nest only structured quantities, never parsed sentence clauses. One parent per relationship/contrast; coefficient display three decimals; all source values/gates retain roles. Findings without a structured pair remain intact single lines, overriding the earlier generic multi-comparison splitting reading. Each selected relationship occupies its own headline slot under the existing five-item cap and ranked order.
