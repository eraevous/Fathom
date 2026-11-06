# Plan
Use a shared stdlib text-run classifier with explicit verdict/inferred/literal
contexts. HTML enhancement preserves script/style/pre/code/SVG content and raw
attributes; escapes text; consumes existing artifacts only. Apply to profile,
Brief/configurator and panel; reuse runs in Markdown and optional PDF/PPTX text.
No added dependency. Existing ReportLab and python-pptx remain optional.
Navigation is one HTML/CSS/short-script component: static list first, progressively
collapsed on phone, ordinary button with aria-expanded/aria-controls, native links.
Keep current palette. Add stable anchors without changing report section order.
Top navigation preserves plotting width; print hides controls. Hide evidence and
provenance with native disclosures; keep verdict and inline gates visible.
Constitution gates:single artifact/flow, typed findings, no inferred semantics as
fact, no analysis selection or numeric modifications. Tests cover planted problems,
clean/hostile-name decoys, semantic formatting, both reports' navigation, script-off
fallback, export runs, immutability and reruns. Actual offline browser screenshots,
PDF/PPTX review, full extras after final records, AEC check and structural impact.
