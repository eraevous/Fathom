---
status: proposed
author: codex:aec
date: 2026-11-04
---

# Proposal for Zach: Retain the 10-decimal storage floor

Should finite stored statistics use max(10 decimals, 6 significant figures), rather than exactly 6 significant figures?

The offset fixture quantiles 1730000133.67, 1730000656.5 and 1730001179.33 collapse to 1730000000 under exactly six figures. The current rule preserves them, but retains more precision than the literal request at ordinary and large magnitudes. Alternative: literal six figures with an explicit offset/scale representation.

Spec008 FR-001 records this builder reading as provisional. Review confirms its
implementation and its trade-off, not Zach's acceptance. No numeric policy changed
in this review. Zach can accept, reject or replace it through a later appended
decision. This is an agent proposal, not Zach's words or a committed decision.

New proposal file explicitly authorized by HO-DG-20261104-XKSJ despite AGENTS'
usual use of this directory for human decision sources; existing passages untouched.
