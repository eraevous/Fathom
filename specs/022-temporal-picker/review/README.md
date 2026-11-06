# HO-DG-20261106-8RZJ PR A review

Spec022, provisional; Kate first, Zach merges. Built from main628cf40 while #34 remained open; #32 merged subsequently, and its README/Brief intro lines are untouched. No new dependency, network feature, protected-document change or data lookup.

## Validation

Full installed test/stats/export suite after final ledger appends: **439passed, 2skipped**, one dependency deprecation warning ([output](tests.txt)). Pinned Telosmith b0e202fa4b20: **0errors, 100inherited warnings** ([check](aec-check.txt)); [report-only impact](code-impact.txt). Purpose refs resolve structurally, spec-quality checklist passes. Structural evidence is not acceptance.

[Fresh-process identity](identity.json): profile/configure/liftoff/export, two hash seeds1/99, sockets and networking clients denied; **12files byte-identical** including actual PDF and PowerPoint. No optional extra silently missing. [Browser checks](browser-checks.json): actual offline Chromium, zero requests/errors/document overflow; keyboard input, custom20/20 match, bad%Q error blocks YAML, canonical built-in/custom selection and generated YAML checked. Scripts-off retains raw samples/formats/commands and hides live-only controls.

## Acceptance fixture

Authored `tests/fixtures/temporal/clocks.csv`,24rows/4columns; no real observations.

| Planted item | Found/displayed | Limit/decoy |
| --- | --- | --- |
| Local clock strings, AM/PM and fractional seconds |23valid/1invalid, earliest00:05:00, latest14:05:09.123000; hour14 has11values; minute/second components and observed precision | No date/year, no midnight date anchor, no assumed timezone |
| Naive and two offset timestamp bases |23valid/1invalid; naive,+02:00,-05:00 separated; written dates retained; hour and weekday×hour counts | No pooled absolute-instant earliest/latest or UTC conversion |
| DMY custom timestamps |24valid under%d/%m/%Y %H:%M;20stored sample previews match; day/month ambiguity warning | Does not silently choose DMY; raw string remains |
| Bad date/clock/pattern controls |24:00,minute/second60,Feb30,bad%Q/dangling%/incomplete date fail explicitly; invalid config produces no output | Valid leap/calendar, ISO/YEAR and ordinary numeric1976–1999 decoys retained |
| Wrong calendar-series basis | Standalone clock or mixed naive/offset series explicitly declined with reason; homogeneous offset series retains offset | Calendar-only panels stay ISO/YEAR; no new panel timestamp contract |
| Stored sample bounds |20source positions, repetitions retained, sample-only match denominator; truncated excluded; examples-only fallback disclosed | Not whole-column quality rates; missing/disabled samples cannot manufacture10rows |

Python/Node parser and YAML parity covers built-ins/custom patterns, fractions, offsets, malformed dates, literal dots and token errors. Hostile samples stay escaped. Malformed saved intraday counts fail loading; historical date-only timestamp notes remain available for old artifacts. New timestamp profiles no longer claim time of day is excluded.

## Visual review

Sixteen actual screenshots: configure/Liftoff picker, scripts off, clock profile;1280/390light/dark. Fixed a live invalid-pattern script error and phone preview columns/row header during review. Long local values now wrap; no page overflow. Palette inherited from main (no restyle). Old static form controls remain usable through the no-script command fallback; live matching needs script. Minute/second tables show observed components and disclose other components zero; full counts remain in the artifact.

| View/theme |1280|390|
| --- | --- | --- |
|configure-light|[image](configure-light-1280.png)|[image](configure-light-390.png)|
|configure-dark|[image](configure-dark-1280.png)|[image](configure-dark-390.png)|
|liftoff-light|[image](liftoff-light-1280.png)|[image](liftoff-light-390.png)|
|liftoff-dark|[image](liftoff-dark-1280.png)|[image](liftoff-dark-390.png)|
|nojs-light|[image](nojs-light-1280.png)|[image](nojs-light-390.png)|
|nojs-dark|[image](nojs-dark-1280.png)|[image](nojs-dark-390.png)|
|profile-light|[image](profile-light-1280.png)|[image](profile-light-390.png)|
|profile-dark|[image](profile-dark-1280.png)|[image](profile-dark-390.png)|

## Narrow readings

Portable token subset documented in [temporal-formats](../../../docs/temporal-formats.md); unsupported locale/platform tokens rejected by name. Complete dates only, no strptime default1900/January. Each UTC offset is a separate written clock basis, not a timezone/DST declaration. The legacy parse_date API stays date-only; profiles use parse_temporal. Custom/inferred timestamp row-level calendar heuristics are not newly expanded; intraday/date profiles cover the requested values. Panel contract unchanged. Suggestions remain unticked, counts on bounded stored samples only. Every later handoff item has its own branch/PR.

Reproduce the authored fixture config in [identity.py](identity.py); run that with existing extras. [capture.py](capture.py) reads its /tmp pages (generate profile/configure/liftoff as in that script), uses offline browser contexts. No new browser/runtime dependency is added to Fathom.

Records appended:FT-TIME22-R1@1 (before code), FT-TIME22-C1@1, FT-TIME22-E1@1; requirements implemented_by, claims depends_on, evidence supports exact claim. Existing ledger is an exact prefix. No requirement acceptance asserted.
