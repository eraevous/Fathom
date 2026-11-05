# Intent: HO-DG-20261105-N8M2 / DEC-095 depth repair

Maintenance on main95de071, not a report feature. The handoff authorizes tool
adoption and label-only new record versions; no new requirement/claim, wording,
relation, acceptance or report behavior is authorized. Kate reviews first (DEC-084),
Zach merges, CLA stays unticked. No standing thread created.

Use Telosmith main b0e202fa4b2087679901620c999f1968f6c62b0e (descendant
of c5ed7af); v0.5.0 is absent from remote tags. Install this exact commit, regenerate
only the generated snippets via init, copy its PostToolUse hook and CI shape.
Keep Fathom's established purpose/records, tracked generated snapshot convention,
and Spec Kit workflow. Init does not overwrite existing files, so remove the two
obsolete generated snippets before regeneration; retain the existing ledger/README.
Update agent installation guidance to the same pin so it cannot reinstall the old
tool that lacks the hook's required commands. No Fathom runtime dependency changes.

There are61 latest unlabelled records:7accepted decisions with existing local quote
anchors become committed;14claims,12evaluations,27evidence and1authority become
provisional. Tests/merges are not owner acceptance. Preserve all fields except version
and the added epistemic label, including relations and anchors. In particular, do
not repin downstream relations or add supersedes metadata: those are beyond the
label-only authorization. Record the old/new references, exact preserved-prefix hash
and committed-label citations in an audit manifest. Historical unlabelled versions
remain historical; the completeness check is on latest records.

Run the generated hook on a committed unchanged tree with the pinned tool on PATH:
exit0 and zero stdout/stderr are the required decoy. Also exercise a disposable linked
code change to demonstrate the hook speaks, then restore it. Regenerate edges and run
check; execute the CI body locally and obtain hosted CI output for the PR. Structural
findings are review prompts, not a claim of semantic safety. No product code edits.

Watch PR23: if it merges first, merge main as the handoff explicitly permits, keeping
all ledger lines. Do not preemptively incorporate the open feature branch.
