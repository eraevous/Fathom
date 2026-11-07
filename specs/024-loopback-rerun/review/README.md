# FT-R17 review — real loopback rerun

Synthetic fixture: [synthetic.csv](synthetic.csv), eight rows/four columns. Planted missing value, repeated key, two zeros and an extreme 999. Existing report findings surface the missing value (1/8), repeated key, 999 (1/7 valid) and long right tail; zeros remain in the numeric profile. Domain cause, true row unit, and whether 999 is a missing-value code remain unknown. No analysis rule changes in this transport slice.

[capture.py](capture.py) starts the actual server in a fresh process under the independent offline harness, permits numeric loopback only, drives a config edit and rerun, inspects the embedded report, then clicks Stop. Each browser blocks every non-session-origin request. [browser-checks.json](browser-checks.json): no external request, JS/console error or horizontal overflow; Stop exits cleanly. No session token is saved in screenshots/log evidence.

| View | 1280 light/dark | 390 light/dark |
| --- | --- | --- |
| Config + live controls | [light](live-light-1280.png) / [dark](live-dark-1280.png) | [light](live-light-390.png) / [dark](live-dark-390.png) |
| Embedded standalone report | [light](report-light-1280.png) / [dark](report-dark-1280.png) | [light](report-light-390.png) / [dark](report-dark-390.png) |

[Scripts disabled, 390](no-js-390.png): page readable; live controls hidden; copyable terminal fallback and Ctrl+C instruction. Static reports contain no live controls and existing socket-free export/render tests still pass.

Found/fixed: status initially announced completion before the embedded page finished loading; it now waits for iframe load. Browser capture waits for paint after bringing an offscreen frame into view. Kept controls above the form and report below it, with a direct link, so a report does not bury the configuration. Existing palette/typography retained, buttons wrap on narrow screens, native keyboard controls and role=status.

Limits: Chromium/Linux review, not real Windows firewall/dialog testing. Session URL is a local capability; this does not authenticate multiple users/processes on the same machine. Idle shutdown is checked between requests; an accepted slow request has a two-second read timeout. No network assets/dependencies. Report-byte identity applies to the three saved artifacts, not the random ephemeral session URL or local activity log.
