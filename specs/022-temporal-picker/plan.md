# Plan: temporal formats and picker
## Technical Context
Python3.12, existing pandas2.2.3/PyYAML, stdlib regex/datetime; inline browser script only. No new dependency. Existing renderers, export degradation and typed evidence remain.
## Constitution Check
One data flow, derived artifact views, inferred/declared labels, bounded within-column profiling, raw values preserved, unknown timezone meaning, deterministic/offline and synthetic acceptance fixtures. Pass before/after design. No protected-document edit.
## Phase0 Research
Read-only Spec Kit research agents inspected parser consumers and configure/liftoff integration. Decisions in research.md. No external lookup.
## Phase1 Design
New temporal_formats module defines portable tokens and rich reading; legacy parse_date remains exact-compatible. Profiler inference/counts use rich reading; temporal_profile delegates date statistics and adds per-clock-basis intraday summaries/charts. Calendar-only row/panel contracts remain; declared series refuses mixed clock bases and standalone times explicitly. Additive schema2 fields validated, legacy loads unchanged.
Picker uses stored samples, capped20 positions, schema descriptors and shared Python/JS token grammar. One canonical date_format input, ranked built-in select updates it, live preview uses textContent and no Date.parse/UTC conversion. YAML generators both validate custom strings. No-script static sample/formats/commands. Configure/Liftoff share render_page seam.
## Validation
Fixtures/tests first; portable-token failure before output; old date-only compatibility; profile/preview parity; inferred labels; clock-basis separation; stored-sample/truncation limits; invalid/malicious strings; selected YAML; live keyboard/no-script,1280/390light/dark, offline/no requests. Full installed extras after final record appends; exact reruns; pinned AEC check/impact. No hidden acceptance table access.
