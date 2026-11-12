# Intent: one bounded bundle delivery
The owner requested multiple datasets/bundles, additional formats/access, and
later normalized relational tables. This first implementation deliberately adds
only orchestration of existing local CSV profiling, not a new analysis subsystem.
It preserves separate row units and avoids accidental joins/fanout.

Issue #39 already carries the wider initiative. Fresh open PR inspection showed
#42, #45 and #47, with no bundle branch; the separately mentioned SQLite/MtG
intake ownership is unresolved and is not touched. Existing active Fathom work is
not restarted or canceled. No claim of owner acceptance of this proposed schema.

New output directories prevent stale success artifacts. Safe-path checks constrain
ordinary local inputs, but do not claim protection against concurrent adversarial
filesystem changes. Error summaries omit potentially revealing raw exceptions.
No dependencies added. Existing CSV/profiler/renderers remain the only data flow.
