# Spec 032 records, as written by Kate (verbatim)

Source: relay-kit-private `kate-replies:replies/HO-FTH-20261120-AYR2--b6b3febf39bc.md` (ask b6b3febf39bc), API Kate, model gpt-6.1-sol, 2026-11-20T05:37:06Z. Targets Fathom main at the time of the ask (spec 032 draft; helper in #57).
`authored_by: chatgpt:kate` · `author_role: independent` (lane-rules §14). Not edited. Kate saw her instructions, the lane seed and the handoff (which quoted Zach's rule, the reading and the worked examples), **not** the code, the helper or `.aec/records.jsonl`: anything about those is "not assessed".
Status: proposed, `provisional`. Not yet appended to `.aec/records.jsonl`: FT-AD-001, -006 and -007 depend on Zach's answers to questions 1, 3 and 2/4, so they are appended once he answers.

---

- **[Opinion — proposed records]** Common fields: `version: 1`, `type: requirement`, `subject: spec-032`, `epistemic: provisional`. Each numbered item is one record; “Test” and “Out” supply its acceptance evidence and exclusions.
  - **FT-AD-001 — Starting precision**
    - Requirement: If Zach selects two significant figures, approximation shall begin at that precision.
    - Test: `1234→1200`; specify rounding mode and boundary cases before implementation acceptance.
    - Out: Deciding question 1.
  - **FT-AD-002 — Zero snap**
    - Requirement: Under the proposed two-figure rule, a second significant digit of 1 or 9 shall round to the nearest one-significant-figure value.
    - Test: `4.1→4`, `5.9→6`, `91→90`.
    - Out: Other starting precisions.
  - **FT-AD-003 — Five snap**
    - Requirement: Under that rule, leading pairs 48–49 and 50–52 shall snap to 50 at the corresponding scale.
    - Test: `4.8→5`, `5.2→5`; controls `4.7→4.7`, `5.3→5.3`.
    - Out: Unspecified stage ordering.
  - **FT-AD-004 — Exactness**
    - Requirement: Approximation shall change presentation only, preserving underlying values and verdict computations.
    - Test: Identical stored values and verdicts before/after display formatting.
    - Out: Computational rounding.
  - **FT-AD-005 — Reveal**
    - Requirement: An approximated value shall offer a single-click disclosure of its unapproximated value.
    - Test: Click reveals the original value without approximation.
    - Out: Hover as a substitute; inaccessible click-only controls.
  - **FT-AD-006 — Marker**
    - Requirement: Approximated displays shall identify approximation using Zach’s selected marker.
    - Test: Marker appears with approximated output.
    - Out: Choosing “≈” versus “about.”
  - **FT-AD-007 — Eligibility**
    - Requirement: Approximation shall affect only Zach-approved output surfaces and numeric categories.
    - Test: Approved surfaces/categories change; excluded ones remain unchanged.
    - Out: Settling HTML-only scope or integer-count exemption.
