# FT-R17 follow-through: liftoff and remaining integration views

32actual offline Chromium screenshots,1280/390,light/dark. No report assets/network.
[Manifest](manifest.json) / [hashes](image-hashes.json) / [capture.py](capture.py) /
[download and stage-two checks](checks.json). Reproduction uses the existing review
Playwright/Chromium environment, not a runtime dependency. Profile fixtures before
running capture.py as in spec quickstart; no runtime date enters output.

| View | Light1280 /390 | Dark1280 /390 |
| --- | --- | --- |
| Brief / observation process | [desktop](liftoff-brief-light-1280.png) / [phone](liftoff-brief-light-390.png) | [desktop](liftoff-brief-dark-1280.png) / [phone](liftoff-brief-dark-390.png) |
| Conditional measurements | [desktop](liftoff-conditional-light-1280.png) / [phone](liftoff-conditional-light-390.png) | [desktop](liftoff-conditional-dark-1280.png) / [phone](liftoff-conditional-dark-390.png) |
| Configurations | [desktop](liftoff-form-light-1280.png) / [phone](liftoff-form-light-390.png) | [desktop](liftoff-form-dark-1280.png) / [phone](liftoff-form-dark-390.png) |
| Series controls | [desktop](liftoff-series-light-1280.png) / [phone](liftoff-series-light-390.png) | [desktop](liftoff-series-dark-1280.png) / [phone](liftoff-series-dark-390.png) |
| Standaloneconfigure | [desktop](configure-form-light-1280.png) / [phone](configure-form-light-390.png) | [desktop](configure-form-dark-1280.png) / [phone](configure-form-dark-390.png) |
| Declared row findings | [desktop](declared-row-light-1280.png) / [phone](declared-row-light-390.png) | [desktop](declared-row-dark-1280.png) / [phone](declared-row-dark-390.png) |
| Declared temporal process | [desktop](declared-temporal-light-1280.png) / [phone](declared-temporal-light-390.png) | [desktop](declared-temporal-dark-1280.png) / [phone](declared-temporal-dark-390.png) |
| Declared temporal stems | [desktop](declared-temporal-chart-light-1280.png) / [phone](declared-temporal-chart-light-390.png) | [desktop](declared-temporal-chart-dark-1280.png) / [phone](declared-temporal-chart-dark-390.png) |

DOM checks: no horizontal document overflow, shared panel tokens white/dark#162427,
all generated IDs unique, no JS in Brief or ordinary report, untouched{}, unticked
series/intervals, standaloneconfigure retains #22’s 12 unticked series controls, temporal stems
resolve to light/dark accent. Row/temporal screenshots use explicit full-findings
mode because repeated pickup/dropoff findings are summarized by default.

Visually inspected representative Brief/form/row/temporal/conditional views in desktop
and phone, both themes; remaining modes checked through computed CSS/DOM. Kept exact
counts/rules and conditional labels adjacent. Shortened the long temporal summary,
retaining every signal state and original statement in disclosures; added in-page
navigation. Configurator now uses the common palette, including warning/state colours.
Phone process headers shortened; numerical counts formatted. Saved-artifact rule/control
ordering normalized so restored HTML matches the original.

Open: full Brief+form remains long(about12478px desktop/19191px phone on taxis,
including the configurator). Complete signal/lag tables need disclosures and local
scrolling; fixed Office output needs zoom and does not include the new Brief or
existing temporal section. No claim of exhaustive pixel/font review or independent
Kate/owner acceptance. This pass follows existing table alignment/chart-label/
contrast practice already referenced in earlier FT-R17 galleries; no new design system.
