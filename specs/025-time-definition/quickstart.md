# Quickstart
`guide configure tests/fixtures/time_definition/clocks.csv --out /tmp/clock-card`
Open configure.html, open Define time fields under clock's format picker, assign12-hour/minute/second/frame/AM-PM, declare24fps, and Use. The row with frame24 is a named fault. Select fraction instead to interpret07as.07seconds, never automatically.
`guide profile tests/fixtures/time_definition/clocks.csv --config tests/fixtures/time_definition/frames.yaml --out /tmp/clock-profile`
Without config the fourth field is explicitly ambiguous, whole-second counts still show. No network or install beyond existing Fathom.
