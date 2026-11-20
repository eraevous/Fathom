# 032: Approximate display ("about 5") in the HTML report, issue #44

**Draft for Zach. Nothing here is wired, and nothing users see changes with this PR.**

Owner request, Zach on #44 (2026-11-17): "Click to display full number, round to 0 when the last significant digit is 1 or 9. Round to 5 if the penultimate sig digit is 4 or 5 and the final sig digit is > 7 or < 3, respectively."
Reading confirmed 2026-11-18 (reading 9, relay-kit-private `kairos/decisions/answers-2026-11-18.md`): "Nine, yes. I think so." Recorded result: go ahead with the spec, then the HTML hover/click wiring, and show Zach the worked-example table again with the spec. Because he said "I think so", the table below is **a question, not a settled rule** (Kate's advice, records-kate.md source).

Serves: P0@2 (a report people can read at a glance). Must not break spec 008 (stored values stay exact). Helper: `fathom/approximate.py` in #57 (unwired).

## First: is this what you meant? (Yes / No / Adjust per row)

| exact | shown | why |
|---|---|---|
| 4.93 | 5 | two figures give 4.9; a second figure of 9 rounds to one figure |
| 4.8 | 5 | 4 then 8: snaps to 5 |
| 4.75 | 5 | rounds to 4.8 first, then snaps (see Q5) |
| 4.7 | 4.7 | no rule applies; keep two figures |
| 4.1 | 4 | second figure 1 |
| 5.2 | 5 | 5 then 2: snaps to 5 |
| 5.3 | 5.3 | no rule applies |
| 5.9 | 6 | second figure 9 |
| 48 / 52 | 50 / 50 | snap to 5 at that scale |
| 148 | 150 | only the last pair snaps |
| 91 | 90 | second figure 1 |
| 1234 | 1200 | two figures (see Q4: counts) |
| 999 | 1000 | carries into a new place |
| 0.0487 | 0.05 | small values keep their scale |
| 0.95 | 0.95 | 9 then 5: no rule applies |
| -4.8 | -5 | sign kept, magnitude rounded |

## Open questions for Zach (the spec does not decide these)

1. Two significant figures as the starting precision? It's the only count that turns 4.93 into 5.
2. HTML only (click to reveal), leaving exports, Markdown, findings text and verdict gates exact?
3. "≈" or "about" as the marker?
4. Are integer counts exempt (a row count of 1234 shown as 1200)? Exempting them is the narrower scope; including them is what the helper does today.
5. *(from Kate)* Order: round to two figures, **then** snap. That makes 4.75 → 4.8 → 5. Snapping on the unrounded value would show 4.8. Which?
6. *(from Kate)* Edge cases, currently: zero and non-numbers are shown as they are; ties round half up (2.45 → 2.5); negatives keep their sign. Keep these?

Until he answers, the narrower reading is the default for the wiring plan: two figures, HTML only, "≈", integer counts **exempt**, round then snap.

## US1: Approximate numbers in the HTML report (P1, after Zach's answers)

- Numeric values in HTML report tables and summaries are shown approximated, with the marker, when the approximation differs from the exact value (`is_approximate`).
- One click on the value shows the exact value (a `<button>` with the exact value in its accessible label, so it isn't click-only for keyboard and screen-reader users). Hover may show it too, but never instead of the click.
- No script dependency beyond the report's existing inline script; the report still opens offline.

## US2: Everything else stays exact (P1)

- Stored values, exports (CSV, JSON, Parquet), Markdown, findings text and verdict gates are unchanged, byte for byte, unless Zach widens Q2.
- Verdicts and thresholds compute on exact values, never on the displayed ones (FT-AD-004).

## Records

Kate's proposed records FT-AD-001 to -007 are in `records-kate.md`, verbatim (`author_role: independent`). They are appended to `.aec/records.jsonl` as `provisional` once Zach answers Q1–Q4, since three of them name his choice.

## Tests (for the wiring PR)

- The worked-example table above, as the helper's table test (#57 already has most rows).
- HTML: an approximated cell carries the marker and a button whose label is the exact value; a value that doesn't change has neither.
- Exports, Markdown and verdicts: byte-identical before and after (US2).
- Integer counts: per Q4.

## Boundaries

- Display only. No change to how anything is computed or stored.
- Not a locale or number-format feature (thousands separators, decimal commas): out of scope.
