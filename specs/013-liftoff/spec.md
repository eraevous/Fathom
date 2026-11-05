# Feature Specification: liftoff — Brief + Configurations

**Branch**: 013-liftoff | **Created**: 2026-11-05 CT
**Status**: authorized scope, all implementation readings provisional for Zach.
**Input**: HO-DG-20261104-36XP, DEC-079/067/080 as relayed in the handoff.
Serves: P0@2, DG-RA@1, DG-RB@1, DG-RC@1, DG-RE@1, DG-RF@1,
FT-R6@4, FT-CFG-R1@2, FT-TS1-R1@2. Proposed: FT-LIFT-R1@1.

## User Scenarios & Testing

### US1 — Discover before knowing what to declare (P1)
`guide liftoff DATA.csv --out DIR` requires no config. It runs the default profile,
then every existing declaration-free check; adds a bounded conditional-zero
observation/question; discovers temporal pairs and event-series candidates; and
shows provisional interval and event-series measurements. The Brief starts with
what the table looks like and observation-process facts, followed by findings with
counts/rules, open questions and explicit declaration/coverage limits. It precedes
the existing configurator and read-only rules in one self-contained HTML page.

### US2 — Suggestions become effective only through selection (P1)
The embedded form starts with no selected target, interval, series or type override;
untouched YAML is `{}`. The user can select an interval, event/value series and
granularity, and target, download liftoff.yaml and run the unchanged
`guide profile DATA --config liftoff.yaml --out DIR`. Provenance stays in the separate
advisory manifest. Standalone `guide configure` keeps its existing behavior.

### US3 — Evidence and hypothetical declarations remain distinguishable (P1)
Ordinary profile findings and declarations remain unchanged in liftoff-profile.json.
New automatically measured zero contrasts and provisional measurements are isolated
under `liftoff`. Every provisional statement says "If you declare …", names the
assumed declaration, generator/rule and exact evidence. It is not a domain fact,
accepted recommendation, selected analysis or human declaration. Results include
all existing signal states, not only positive signals.

## Requirements

- FR-001: Write liftoff.html and liftoff-profile.json after successful computation;
  schema_version2. No config argument, network lookup or runtime dates.
- FR-002: Default type/date/row/key/timestamp checks run unchanged. Target candidates
  are unranked observable type/population/distinct facts. Interval suggestions reuse
  the existing temporal pair screen (both directions, up to10pairs); directions
  remain choices. Event-series candidates reuse >=30distinct finest eligible periods
  (hour if all parsed timestamps have time of day, otherwise day).
- FR-003: Preview every offered interval and at most20event series (input-column
  order, all eligible candidates counted). Reuse existing interval and time-series
  engines/rules, including their skip/insufficient/undefined/not-estimable states.
  Preview uses value:null and granularities:[auto]; different selections are not
  claimed to reproduce that preview. No provisional target association or by-group
  series analysis. List every preview omission and existing engine cap.
- FR-004: A liftoff-only conditional-zero check screens at most10numeric and10
  categorical/boolean columns (input order), at most20levels per grouping. Show an
  observation if a group has >=10finite values, every finite value is0, the rest
  has >=10finite values, and the zero-rate gap is >=0.30. State group/rest finite,
  zero, missing and invalid counts. Ask whether zeros are structural, unrecorded
  or literal; never assert the mechanism. At most20matching patterns shown, exact
  omitted count saved. It never changes target selection or stage-two rules.
- FR-005: The Brief shows short sentences grouped by kind, readable counts and
  rules; technical detail and full repetitive findings behind disclosures. It is
  static/script-free within the page. Only the configurator has JS, offline only.
- FR-006: Liftoff's form offers time-series selection, event/null or an observed
  numeric value, and auto/hour/day/week/month granularity. Series and interval
  declaration checkboxes start unticked. Python/JS YAML generation agrees; no new
  loader keys, applied guesses, threshold controls or provenance in YAML.
- FR-007: All strings escaped in HTML/attributes/JSON; hostile names cannot execute
  script or corrupt property-key lookup. Existing configurator behavior remains
  compatible, including config passthrough and advisory YAML digest.
- FR-008: Use the existing palette in liftoff/configurator and temporal/row sections;
  inspect actual1280/390light/dark screenshots, including stage-two reports. Fixed
  exports retain current behavior. No new dependency, server or dashboard.
- FR-009: Same input, fixed dependencies and seed produce identical artifacts/page
  across processes. Optional statistics/export absence degrades without crashing.

### Key Entities

Default profile; discovery candidate/coverage; automatic zero observation; conditional
interval/series preview; effective empty configuration; configuration schema; Brief;
advisory manifest; existing stage-two report.

### Edge Cases

No dates; fewer than30periods; constants; missing/unparsed timestamps/values; reversed
interval directions; date-format suggestions that remain unaccepted; many candidates;
empty datasets; hostile names; missing optional stats; JS disabled (Brief still works,
manual YAML instructions); changed series value/grain after preview.

## Success Criteria

- Taxis6433×14: Brief shows6equal pickup/dropoff pairs provisionally; hourly ACF
 24peak provisionally;1812/1812cash tips zero as observation/question;19repeat pickups;
 1pickup outside dominant month; each with rule and declaration label as applicable.
- Selected interval/time-series settings reproduce exact interval/process/ACF counts
  through the unchanged declared engines. Target payment-group counts/zero extrema
  corroborate the cash observation where selected; no new stage-two zero rule is added.
- Violating fixture + clean decoy for each new behavior; UI download→loader→profile
  and Python/JS parity; fresh-process bytes; full/core/AEC; actual light/dark review.

## Clarifications / narrower readings

Provisional mode is the handoff's proposed reading of "as much lifting as possible";
implemented as isolated hypothetical results, not effective declarations. Automatic
series previews are event counts only; selecting a value changes the question.
Cash-tip zero semantics remain a question; thresholds are proposed and read-only.
The old stage-two engine intentionally lacks a general conditional-zero finding;
unchanged group counts/min/max can corroborate it, but no new declared zero sentence
is promised. This preserves the explicit ban on changing stage-two semantics.
C-22, by-group previews, target ranking and timezones remain outside this slice.
