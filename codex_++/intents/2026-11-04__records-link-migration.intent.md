# Intent: HO-DG-20261104-XKSJ item3

Records hygiene only, stacked after PR16 review and spec009. No app behavior,
requirements text, epistemic status, tiers, evidence method/limits, authorities,
anchors or accepted decisions change; no DEC-021 replay. No dependency added.

The linked AEC vocabulary defines implemented_by as requirement→code and deprecates
implements (any→requirement). A mechanical rename on claims is directionally wrong.
New claim versions use depends_on for their contract/readings; existing misplaced
claim→code implemented_by becomes depends_on code (only the four explicit FT-TA-C2
bindings). Requirements/readings carry implemented_by code. Reading requirements
use depends_on for the governing contract, not an invented inverse truth dependency.

To reach governing obligations, add reviewed partial implementation paths on those
requirements as metadata-only new versions. These paths flag satisfaction for review,
never invalidate or accept the obligation. They are current, post-review mappings,
not historical proof of what the author could have known on PR15. No new mapping
for unbuilt FT-R8 or an assertion of purpose achieved.

Repin dependent current records only where the referenced latest version's text is
identical: evidence supports the new equivalent claim version; evaluation links
retain that evidence lineage. Earlier contract versions with different text remain
pinned. All prior lines stay byte-for-byte. Metadata repinning is not reobservation.

Run one pinned extractor/engine (project860b781, AEC0.4.0/Python3.12) on exact frozen
3b89d7c and3367ab3trees. Same snapshots for historical ledger, pre-migration current
ledger, migrated current ledger, and an ablated no-new-links decoy. Commit raw impact
outputs and a mapping audit; show before/after excerpts in the PR. This is authorized
records diagnostics, not running/repairing/regrading precondition P1 or replay trials.
