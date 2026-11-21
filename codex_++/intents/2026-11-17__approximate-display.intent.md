# Intent: approximate display for #44 (unconfirmed reading)

Author: claude:fathom#wake-20261117-23 · Reviewer: none yet · model=claude-opus-5-5

Zach's words (Fathom#44, 2026-11-17T23:05Z): "Click to display full number, round to 0 when the last significant digit is 1 or 9. Round to 5 if the penultimate sig digit is 4 or 5 and the final sig digit is > 7 or < 3, respectively."

You said the rule above → I read it as: show values at two significant figures, snap the second figure 1/9 to 0 and 48-49/50-52 to 5, keep the exact value one click away → So I'll: add a pure, unwired helper with worked-example tests and wait for Yes / No / Adjust before a spec or any wiring.

Trade-offs and open questions (narrower reading taken where silent):
- **Starting precision.** The rule needs a count of significant figures. Two is the only count under which his 4.93 example becomes "about 5"; with the current display precision (4.93) neither branch fires.
- **Where.** "Click to display full number" implies the interactive HTML. Exports, Markdown, prose, findings and gates printed beside verdicts are not touched; the helper is not wired anywhere.
- **Marker.** "≈" or "about": not chosen.
- **Integers.** 1234 → 1200 under this reading. Counts may want an exemption.
- **One pass.** Each rule applies once to the two-figure value; no repeated rounding.
