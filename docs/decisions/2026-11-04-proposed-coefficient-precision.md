---
status: proposed
author: codex:aec
date: 2026-11-04
---

# Proposal for Zach: Retain the coefficient precision exception

Should skewness, excess kurtosis, Pearson r, eta, Cramers V and lag-1 autocorrelation retain ten decimal places?

The current exception suppresses numerical residuals such as skewness 2.961e-16 for a symmetric column. A magnitude-only floor also suppresses any actual coefficient below 1e-10; it is not proof that every such value is noise. Alternatives: uniform significant figures or a separately justified numerical-zero tolerance.

Spec008 FR-001 records this builder reading as provisional. Review confirms its
implementation and its trade-off, not Zach's acceptance. No numeric policy changed
in this review. Zach can accept, reject or replace it through a later appended
decision. This is an agent proposal, not Zach's words or a committed decision.

New proposal file explicitly authorized by HO-DG-20261104-XKSJ despite AGENTS'
usual use of this directory for human decision sources; existing passages untouched.
