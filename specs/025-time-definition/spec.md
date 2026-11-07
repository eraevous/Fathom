# 025 — Define clock fields without guessing

HO-DG-20261106-M0M3; proposed for Zach. Stacked on PR35 while open.
Serves: P0@2, DG-RB@1, DG-RE@1, DG-RF@1, FT-TIME22-R1@1, FT-CLOCK25-R1@1.

## US1 — Preserve an ambiguous fourth clock field (P1)
Recognise 12/24-hour HH:MM:SS:FF, optional AM/PM. Without an explicit declaration, preserve FF verbatim, warn/question whether it is fractional seconds or frames, and compute hour/minute/second statistics only. Never turn it into a fraction automatically. Declaring %f after a colon uses the existing one-to-six digit decimal fraction contract (07 means .07). Declaring portable %F plus a positive finite frame_rate means integer frame counts; values >= rate are named faults. Raw strings remain unchanged, no date is invented and no timezone conversion is added.

## US2 — Define fields using an offline card (P1)
Every temporal picker offers a native disclosure card. Tokenize one stored sample in order, preserving separators/literals; each field has a role selector: year, month, day, 12/24-hour, minute, second, fraction, frame, AM/PM, offset, literal/ignore. No role is automatically accepted. Show observed sample min/max and frame-compatible hints with their limitations (common24/25/30 rates, not all possible rates). Show generated pattern, per-sample preview, match count/denominator and named faults. Frame role exposes rate input. Use this format explicitly copies pattern/rate into canonical YAML controls. Dropdown remains. No-script card lists the same fields, tokens, YAML and CLI command. Pure inline script, native keyboard controls and textContent for user values.

## Acceptance
Synthetic undeclared four-field and declared out-of-rate violations, with ordinary-clock/fraction/frame clean decoys. Python/browser grammar and fault parity, config/card round-trip and exact declared-rate handling. No valid pattern/output mutation on config errors; raw fields preserved; explicit findings and report explanation. No threshold/verdict changes to existing analyses. Byte-identical reruns, offline commands/exports, full extras suite, card screenshots1280/390light/dark with scripts on/off.

## Boundaries
No SMPTE drop-frame, media synchronization, inferred frame rate or automatic frame-to-wall-clock conversion. Fraction precision remains microseconds (1–6digits); frame profiles retain counts/rates separately. Declared calendar series decline frame-based timestamp chronology explicitly. No new dependency, network feature or protected-document change.
