# Feature Specification: Clock times, timestamps and format picker
Created2026-11-06; provisional; HO-DG-20261106-8RZJ PR A. Branch022-temporal-picker from main628cf40 (#34 still open). Kate first; Zach accepts/merges.
Serves:P0@2,DG-RA@1,DG-RB@1,DG-RE@1,DG-RF@1,FT-TIME22-R1@1.

## User Scenarios & Testing
### US1 — Read local clocks and timestamps (P1)
Time-of-day strings such as14:05,2:05 PM,14:05:09.123 have no invented date. The dictionary profiles earliest/latest local clock, hour distribution and minute/second/subsecond granularity. Timestamps retain written calendar-date statistics and add hour and weekday-by-hour counts. Naive values and explicit offsets have distinct labelled clock bases; no UTC conversion, timezone assumption or date invention. Mixed bases have separate summaries, never one absolute earliest/latest claim.
Acceptance: authored clocks, AM/PM, fractional seconds, timestamps with/without offsets and invalid ranges; plain dates/years and non-date text decoys.
### US2 — Declare a format and preview it (P1)
Built-ins include TIME and DATETIME alongside existing names. Portable strftime-style custom patterns accept complete date and/or clock fields; invalid/unsupported tokens fail before any output, naming the token. Configure and liftoff expose the same offline picker on columns with temporal candidates:10–20 stored raw samples where available, built-ins ranked by sample matches, custom pattern/live parsed values and match rate, day/month ambiguity warning. Selection goes into YAML as a human declaration; no suggestion is applied automatically. With scripts off, list formats and copyable command.
Acceptance: custom day/month timestamp, invalid%Q/incomplete date/invalid ranges, ambiguous03/04, existing custom config round-trip, browser preview/Python parity, YAML quote safety, no-script and malicious sample strings.
### Edge cases
Missing/truncated/disabled samples:show available stored cells and disclose sample-only denominator; never fetch data. Date-only profiles stay compatible. Offset-aware chronology is not silently mixed with naive or differently-offset clocks. Standalone times cannot declare a calendar series. No new dependency, server, new bivariate analysis or timezone database.

## Functional Requirements
FR1:Local TIME/DATETIME parsing and profiles preserve raw values, invalid counts and clock bases. FR2:portable custom patterns validate upfront with token-specific errors. FR3:shared offline picker and YAML, keyboard controls and no-script commands. FR4:typed findings/evidence when mixed clock bases or invalid values need review. FR5:deterministic outputs/legacy loads/optional exporter degradation; full extras and offline tests,1280/390light/dark review.

## Key Entities
Parsed temporal reading (kind, optional written date, clock, granularity, offset/basis, format and ambiguity); per-basis intraday profile; stored-sample format choice; declaration.

## Success Criteria
Planted times/timestamps have correct observed counts and no invented dates/conversion; invalid values remain counted. Python and live sample previews agree on supported grammar. Chosen patterns round-trip into validated YAML. Invalid patterns create no output. Repeat reports match byte for byte; pages make no network requests and remain readable without scripts.

## Assumptions
Portable pattern subset is documented; unsupported locale/platform tokens rejected explicitly. %I requires%p; date patterns require year/month/day; year-only uses YEAR. All observed local clocks are displayed, not inferred UTC instants. Existing calendar-only panel contract remains unchanged; declined clock bases in series are explicit.
