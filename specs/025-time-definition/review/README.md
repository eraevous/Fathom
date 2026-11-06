# FT-R17 review — time-definition card

Synthetic-only fixture: [clocks.csv](../../../tests/fixtures/time_definition/clocks.csv). Six four-field12-hour clocks with fourth values07,23,24,29,00,99; ordinary-clock decoy, custom dated-clock candidates and an unrelated numeric column.

Acceptance findings:
- Undeclared: all 6 first-three-field clock readings valid; 6 explicit fourth-field ambiguities, raw values retained; no fraction/frame observations. Hour 02 has 3 rows; second 34 has 4. Ordinary clock has no ambiguity finding.
- Declared 24 fps: frame 07, 23, 00 valid;24,29,99 produce 3 named `frame_at_or_above_rate` faults. No conversion or repair.
- Fraction decoy: all 6 valid;99 means 990,000 microseconds, not 99 frames. Rate 29.97 accepts 29 and rejects 30. Leading-zero frame text remains lexical; safe-integer overflow is a named fault.
- Custom frame timestamps retain written date/clock, with explicit refusal of frame chronology for calendar series. Meaning, true frame convention and synchronization remain unknown.

[build.py](build.py) runs ordinary commands under the existing independent socket/client denial harness, including actual optional PDF/PPTX. [identity.json](identity.json) proves all saved files identical across hash seeds 1/73. [capture.py](capture.py) uses actual shared configure/Liftoff HTML, offline browser contexts and native keyboard disclosure. It tests frame preview/faults/YAML and switching to fractions removes the old rate. [browser-checks.json](browser-checks.json): 16 views, no requests/JS errors/page overflow.

| Page / scripts |1280light/dark|390light/dark|
|---|---|---|
|Configure, on|[light](configure-scripts-light-1280.png) / [dark](configure-scripts-dark-1280.png)|[light](configure-scripts-light-390.png) / [dark](configure-scripts-dark-390.png)|
|Configure, off|[light](configure-no-js-light-1280.png) / [dark](configure-no-js-dark-1280.png)|[light](configure-no-js-light-390.png) / [dark](configure-no-js-dark-390.png)|
|Liftoff, on|[light](liftoff-scripts-light-1280.png) / [dark](liftoff-scripts-dark-1280.png)|[light](liftoff-scripts-light-390.png) / [dark](liftoff-scripts-dark-390.png)|
|Liftoff, off|[light](liftoff-no-js-light-1280.png) / [dark](liftoff-no-js-dark-1280.png)|[light](liftoff-no-js-light-390.png) / [dark](liftoff-no-js-dark-390.png)|

Visual problems fixed: inherited picker 36 px first-column rule crushed the new card's headers/raw values at 390; scoped field/preview column widths restore readable labels. Irrelevant frame hints hide after another role is selected; space and common-rate qualifications are explicit. Native selects wrap within the card, failure names/values remain labelled, and scripts-off fallback exposes tokens/config/command with no inert live button. Retained Fathom palette/typography; no new CSS/JS library.

Limits: min/max describe aligned stored samples, not unseen data. Literal/ignore is exact. No guessed rate, wildcard grammar, drop-frame/SMPTE interpretation or rounded chronology. Linux/Chromium review; no new network feature. Builder conformance, not owner acceptance/held-out usefulness.
