# Intent: HO-20261103-002, eight PR15 review fixes

Serves existing FT-R7@2, FT-R19@1 and FT-TA-R1@2; no new feature or requirement.
Main944f82f merged locally into007-target-analysis before work, explicitly authorized
by this handoff despite AGENTS' general never-merge rule. No rebase/PR merge/force.

1. Log boxes label positive plotted n and excluded nonpositive n; linear boxes
   retain all complete cases. Cautions follow plotted n, complete group summaries
   unchanged. Legacy saved boxes without per-box exclusions keep their stored data but display
   plotted counts/exclusions as unavailable, never inferred from quartiles.
2. Separate unrounded normalized interpolation for grouped-box geometry only;
   existing rounded statistical percentile contract unchanged.
3. Rate captions match horizontal shares/vertical predictor groups or bins in
   the shared chart spec, propagating to every serializer.
4. Validate the nullable target envelope against purpose.target, complete nested
   group summaries/rates/contrasts and required/optional chart counts at artifact
   load, raising ValueError rather than exposing renderer exceptions. Legacy artifacts
   without target_analysis remain supported. Optional new box counts remain additive.
5. Each target SVG has a native Chart values disclosure: raw plotted coordinates,
   full group/bin/category labels and rates, five-number values/counts/exclusions;
   no HTML script. Disclosure values avoid display rounding that could erase tiny
   geometry; statistical/report formatting elsewhere stays unchanged.
6. Paginate tall PowerPoint target plots into readable group panels and a separate
   legend when necessary. Normal decks/layouts unchanged; explicit panel/continuation
   labels and scope notices. Keep all supported groups/levels, no shrink below8pt
   to conceal overlap. Summary pagination shares the existing7chart-slide budget; later charts can
   be omitted visibly, preserving the12-slide cap. Full decks retain all panels.

Each of the eight review comments receives a before-failing/after-passing regression
and clean decoys where meaningful. Re-run full/core/bytes/AEC and actual affected
HTML/PDF/Impress-PPTX1280/390 screenshots. Append claim/evidence only; keep earlier
records/decisions byte-for-byte. Reply/resolve exactly the eight authorized threads,
update PR15 last, then stop. No independent acceptance claimed.
