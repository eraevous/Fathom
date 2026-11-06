# Local clock times and temporal formats

Declare a format when its meaning is known. The type remains `temporal`; raw values and invalid counts stay in the artifact.

```yaml
columns:
  clock: {type: temporal, date_format: TIME}
  recorded_at: {type: temporal, date_format: DATETIME}
  local_stamp: {type: temporal, date_format: "%d/%m/%Y %H:%M"}
```

TIME accepts `14:05`, `2:05 PM`, `14:05:09.123` and clock offsets. It has no calendar date. DATETIME accepts ISO dates plus a local clock, with optional seconds/fractions and `Z`, `+02:00` or `-0530`. Fractions have one to six digits. Naive clocks and each UTC offset have separate distributions and local earliest/latest readings. There is no implicit timezone assignment or UTC conversion. Timestamp calendar counts refer to the written dates, not normalized UTC dates.

The dictionary adds hour counts, minute/second components, observed precision and (for timestamps) weekday-by-hour counts. Minute/second components are not elapsed intervals or a claim about collection cadence. Mixed clock bases are an observation to review. Declared calendar series cannot order bare times or mixed offsets together; their reason is reported. Homogeneous-offset series retain the offset and written local clock. Calendar-only panel input remains ISO/YEAR.

Existing built-ins remain: ISO, ISO_DATETIME, MON_D_Y, MDY, DMY, YEAR. YEAR is an explicit annual anchor; undeclared integers remain numeric. The exact legacy `parse_date` API stays date-only; new profiles use the richer temporal reading.

Portable custom patterns use these tokens:

| Token | Meaning |
| --- | --- |
| `%Y`, `%y` | Four/two-digit year; two-digit pivot69 |
| `%m`, `%d` | Numeric month/day |
| `%b`, `%B` | English abbreviated/full month |
| `%H`, `%I` | 24-hour/12-hour clock |
| `%M`, `%S`, `%f` | Minute, second, one-to-six fractional digits |
| `%p` | AM/PM; required with `%I` |
| `%z` | Explicit numeric UTC offset or Z |
| `%%` | Literal percent |

A date needs year, month and day; no1900/January defaults. A clock needs an hour; fractional seconds need seconds. Unsupported locale/platform tokens (including `%Z`, `%c`, `%-d`) and malformed/incomplete patterns fail by naming the token or required field before output is written. Values that fail a valid pattern stay invalid; invalid dates never roll over. No date/time format is inferred from a lookup or network request.

`guide configure` and `guide liftoff` share an interactive picker. It ranks built-ins by matches among up to20 stored sample rows and previews custom patterns. Counts concern shown samples, not every input row. Repeated values are retained, source positions deduplicated; truncated cells are excluded from the denominator. Fewer examples are shown when sample rows are unavailable; this limit is disclosed. Date-looking prefixes can expose a picker even when a complete timestamp requires a custom pattern. Ambiguous day/month readings are warnings, not automatic selections.

Choose a built-in or edit the canonical named-format/pattern input; the chosen value goes to YAML. Invalid patterns block YAML download. Without scripts the samples, available formats and command remain visible: edit YAML, then run `guide profile DATA.csv --config fathom.yaml --out report`. No dependency, remote service or external page asset is needed.
