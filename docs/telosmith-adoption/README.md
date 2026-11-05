# DEC-095 depth repair / HO-DG-20261105-N8M2

Maintenance only; no Fathom runtime code or dependency changes. Branch from main
95de071. Kate reviews first (DEC-084); Zach merges; CLA unticked.

## Tool and integration

Telosmith main **b0e202fa4b2087679901620c999f1968f6c62b0e** includes c5ed7af.
`git ls-remote --tags` found no v0.5.0 tag, so install/CI use the exact commit.
The package is telosmith 0.5.0; its command/module remain `aec`. The generated
extractor method identifies itself separately in its snapshot metadata.

Ran `aec init . --owner 'Zach Rhodes' --hooks` from that installed commit. Init
never overwrites files: backed up and removed only the two old generated snippets
first. It regenerated both and created .aec/.gitignore; existing records, purpose,
README and snapshot were kept. The generic purpose-stub next step was inapplicable
to this established ledger and was not followed. No Spec Kit extension replacement.

Installed the generated hook at .claude/settings.json and the generated workflow
at .github/workflows/aec.yml, byte-for-byte. Agent install guidance uses the same
pin. Checkout fetch-depth 0 permits merge-base snapshots. Structural errors fail CI;
code impact is report-only and writes GITHUB_STEP_SUMMARY. Tracked edges remain
tracked under Fathom's existing convention; temporary before/hook snapshots ignored.

## Labels, with no assertion or relation changes

[labels.json](labels.json) records the original byte prefix/hash, all 61 mappings,
and exact decision-file citations. Every appended record differs only in version
and the new epistemic field. Text, tier, authority, status, anchors, methods, limits,
relations and historical pins are identical. No new supersedes edge or downstream
re-pin: the task excludes content beyond labels. Existing unlabelled historical
versions remain; latest completeness is the check.

| New committed label | Existing acceptance citation |
| --- | --- |
| DG-D1@2 | docs/decisions/2026-11-01.md: “The MVP here is data -> decisions” |
| DG-D2@2 | same: “Charter looks good, too” |
| DG-D3@2 | same: “The April design spec and plan: **Distil, don't copy.**” |
| DG-D4@2 | same: “Blow it away.” / “Who builds: **Codex, cold.**” |
| DG-D5@3 | 2026-11-01-evening.md: quality first, then univariate; -evening-2.md: “Addendum to DGD5.” |
| DG-D6@2 | -evening-5.md: “quality score off for now” |
| DG-D7@2 | -evening-6.md: “Layouts will need to have some better dynamism in the future as well.” |

The other 54 become provisional:14 claims, 12 evaluations, 27 evidence and 1 authority.
Builder observations/tests/merges are not owner commitment. AU-owner's conservative
label does not change its governs field or any existing decided_by/status field.
Latest totals: **34 committed, 71 provisional, 0 unlabelled** (was 27/17/61).

## Verification

- Full 292 passed; core 281 passed / 11 optional skips. Two new audit tests failed before
  migration and pass after. They enforce complete labels, exact byte-prefix retention,
  all 61 mappings, unchanged other fields and actual committed-label quotes.
- Legacy records-link tests recognize only exact assertion-equivalent label aliases;
  they do not accept unrelated later wording. The two frozen AEC 0.4.0 diagnostic
  tests still pass under their recorded tool. Telosmith 0.5 rejects those legacy
  snapshots' unknown extraction method, so those two tests explicitly skip on other
  tool versions; six metadata/audit tests pass with the new tool. No method guard
  override or frozen-snapshot rewrite was used.
- Generated hook on committed unchanged code: **exit 0, stdout 0 bytes, stderr 0 bytes**.
  Temporary `pass` in linked profile function: **exit 2, stdout 0, stderr 8,888 bytes**,
  9 affected / 14 structural pointers. Source bytes restored in a finally block; hook
  again exit 0/stdout 0/stderr 0. No diagnostic mutation committed.
- Refreshing the tracked snapshot after a commit changes its generated base_revision
  header to that HEAD; all edge lines stay identical. Restored the recorded generated
  snapshot after the hook check. This header refresh is not hook output or report drift.
- Exact generated CI script run locally: exit 0; summary below. Baseline/current
  snapshots were both extracted with the new pinned tool, not mixed legacy methods.
- No src/, pyproject.toml, fixture, protected-document or docs/decisions changes.
  Original 281,227 ledger bytes remain an exact prefix; 61 new JSON lines follow.

```text
aec edges: 4041 edges from 54 files (0 skipped)
aec check: 0 error(s), 97 warning(s) (structural)
# derived 0 change event(s) from the structural diff
# aec impact

0 affected, 99 conclusions with no status change
```

The 97 warnings are 58 historical deprecated-relation warnings and 39 superseded-reference
warnings. Unchanged main with the new tool already has 64 warnings (58+6); label-only
versions add 33 old-pin warnings. They are disclosed, not suppressed. Re-pointing those
records is outside label-only authority; it would assert updated support, not merely
label it. Structural silence / 0 affected does not establish semantic safety or acceptance.

Full local check output: [check.txt](check.txt). CI output is also pasted in the PR
after the hosted workflow runs. No PR23 content was included while it remained open.
