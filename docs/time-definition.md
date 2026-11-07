# Define clock fields explicitly

`02:39:34:07 AM` and `14:05:09:23` have four clock fields. The last could mean decimal fractions or video frames. Fathom asks: it preserves the last field as written and computes hour/minute/second counts, leaving that field out of sub-second measurements until you declare its meaning. No date, frame rate or timezone conversion is invented.

```yaml
columns:
  fractions:
    type: temporal
    date_format: "%H:%M:%S:%f"
  frames:
    type: temporal
    date_format: "%I:%M:%S:%F %p"
    frame_rate: 24
```

`%f` remains a one-to-six digit **decimal** fraction after either a dot or colon: `07` means .07 seconds, `7` means .7 seconds. `%F` is Fathom's portable frame-index token, **not POSIX's ISO-date shorthand**. It requires seconds and a positive finite numeric `frame_rate`; it cannot coexist with `%f`. A rate alone does not resolve builtin TIME's fourth field. Portable numeric tokens use ASCII digits in Python and the browser. Frame indices are nonnegative JavaScript-safe integers (up to 9,007,199,254,740,991), with leading zeros preserved in the raw field. An index at or above the declared rate produces `frame_at_or_above_rate`; an unrepresentable integer produces `frame_not_safe_integer`. Other field/range mismatches are `format_mismatch`.

Declared frames are profiled as counts/ranges at their rate. They are not silently rounded to microseconds. No SMPTE/drop-frame, media synchronization or frame-to-wall-clock conversion is implemented. Frame-based timestamp declarations still have written calendar/intraday profiles; declared calendar-series chronology is explicitly declined. Naive/offset bases and the rest of spec022 remain unchanged.

Open **Define time fields** under any temporal format picker on `guide configure` or `guide liftoff`. The dropdown remains available. The card uses existing stored samples, lists their fields in order and shows observed min/max for aligned layouts. Assign each field a role, enter a rate for frames, inspect the generated pattern, sample previews, match count and named faults, then select **Use this format** to copy it into YAML. Roles are not automatically accepted. Literal / ignore matches that sample text exactly: it does not discard arbitrary variable text.

Sample evidence cannot establish units. Max 23 or 29 may fit some frame rates and also fractions; above 29 rules out common 24/25/30 fps, not higher rates. The rate is always your declaration. Layout alignment and sample-only denominators are disclosed; samples with other separators can fail the generated pattern.

All controls and grammar run inline without network/dependencies. Native disclosures/selects work with the keyboard. With scripts off, the card lists fields, evidence, tokens and YAML/terminal fallback; live-only controls are hidden:

```bash
guide profile DATA.csv --config fathom.yaml --out report
```
