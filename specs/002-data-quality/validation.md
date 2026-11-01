# Builder validation: 002-data-quality

HO-20261101-006; codex:aec; 2026-11-01. This is builder evidence, not independent
acceptance or a claim that Zach/Kate's unseen tables passed.

## Change-by-change acceptance check

| Change | Consequence visible from report alone | Standalone documentation check |
| --- | --- | --- |
| Quality diagnostics (FR-001/002) | Names suspicious values, skew and gaps; observations support separate hypotheses/actions with counts and rules | Meanings/causes remain unknown; inferred types and overrides remain visible |
| Ranking (FR-003) | Stronger later candidate wins one slot; missing-rate contrasts compete within the same budget | Ranking basis, scores, exclusions and screening limits are disclosed |
| Dataset summary (FR-004) | Complete rows/columns, duplicates/lockstep, types and missing-cell share expose scope at a glance | Figures link to findings; legacy complete-row counts explicitly unavailable |
| Readable views (FR-005/006) | Summary default suppresses repetitive type, meaning and quality items while preserving the consequential example | Typed sections, one-click evidence/full view, compact dictionary and provenance; saved artifact alone is sufficient to render |
| Builder holdout (FR-007) | Finds supported planted signals while exposing misses and unnecessary reviews | Report doesn't invent sentinel meanings, monthly schedules, causes or fitness claims |

The builder judges both acceptance questions supportable for the documented review
decisions on these synthetic reports. This is not the independent unseen-table
test in FT-R4; usefulness remains for Zach/Kate to judge.

## Tables and found/missed ledger

All inputs are authored synthetic fixtures in tests/fixtures/quality/. Planted
truth is in planted.json. The additional holdout was written after the diagnostic
implementation commit; its manifest records the frozen quality.py SHA-256. Presentation grouping was refined afterward. A subsequent adversarial shared-absence
check found a generic near-copy false alarm; the final rule additionally requires
>=95% agreement among jointly present cells. Both diagnostic hashes and the timing
are in planted.json. This guard was tested on the separate shared-absence table;
the initial holdout's sentinel/dummy/monthly misses were not tuned away.

| Table | Report found | Missed / false alarms |
| --- | --- | --- |
| workshop.csv — 41 × 13 | 999 in age/age_copy, 2/41 each (4.9%); dummy status 1/41; dominant keep 40/41; constant fixed; one exact duplicated column; three lockstep groups; availability_a/b co-missing 13/41 with north rate 13/21 vs south 0/20; daily gap Jan 20→31 (10 unrecorded positions); skewed amount (mean 255.561 vs median 12); one repeated full row | No planted diagnostic family missed; extra skew findings in age/copies/scaled amount are real patterns, not independent new causes; equivalent site recodings can yield repeated contrasts, disclosed rather than claiming independent evidence |
| shared-absence.csv — 100 × 3 | a/b co-missing on 95/100 rows; after the audit guard neither a near-copy finding nor a value exclusion is produced; a versus b remains eligible with a target | Initial rule falsely called the columns near copies based on null equality; corrected by jointly-present agreement, with a failing-then-passing decoy regression |
| clean.csv — 12 × 5 | 12 complete rows, 5 complete columns, zero missing cells/repeated rows and no review actions | No planted problems and no quality false alarms |
| holdout.csv — 31 × 16 | Age 999, 1/31 (3.2%); test_7 label; dominant usual 30/31; constant fixed; near_a/near_b agreement 30/31 (96.8%); a/b lockstep and co-missing 10/31; east missing rate 10/16 vs west 0/15; daily gap Mar 10→13 (2 unrecorded positions); skew mean 35.0968 vs median 3; one repeated full row | **Partial:** unlisted 888 is surfaced by skew, but not identified as a sentinel candidate; compound dummy label test alice appears as a rare alternative to a dominant value, but isn't labelled dummy. **Miss:** omitted March under a human-intended monthly schedule gets no temporal-gap finding (only three distinct irregular dates). **False alarm:** intentionally valid valid_extreme=999 gets a sentinel hypothesis/review; its measured extreme/skew is real but the suspected meaning is wrong against builder truth |

Opening measurements: workshop 28/41 complete rows (68.3%), 11/13 complete columns
(84.6%), 26/533 missing cells (4.9%); holdout 21/31 complete rows (67.7%), 14/16
complete columns (87.5%), 20/496 missing cells (4.0%). No missingness mechanism or
row-level lineage is inferred from these totals.

## Executed verification

- Python 3.12.14; pandas 2.2.3, PyYAML 6.0.3, NumPy 2.5.4, pytest 9.2.0. The earlier clean stats run used SciPy 1.18.1;
  the final preconfigured stats run used SciPy 1.17.0 and NumPy 2.3.5.
- With SciPy available: **101 passed** in the final stats run. Without SciPy: **100 passed, 1 skipped**,
  only the SciPy-present decoy. Existing forced-unavailable tests also pass.
  The presence decoy checks the public pearsonr function: uninstalling SciPy can
  leave empty namespace directories, which are not a usable optional dependency.
- Exact metrics, minimum samples, violation/clean decoys for each family, shared
  budget, stronger-later and reordered inputs, small exact-copy exclusion, wide
  screening limits and human type overrides are covered.
- Existing CLI fresh-process/hash-seed byte tests and artifact roundtrip tests
  pass for all three outputs. Legacy slice-1 artifact renders without inventing
  complete-row measurements. Installed profile/render/compare/validate workflows
  remain supported; pip check reports no broken requirements.
- Chromium through the available Playwright tool: summarized default; one click
  reveals all **44** grouped original items on workshop; second restores summary;
  finding IDs unique and every evidence anchor resolves. No external assets or
  script is needed. Inspected opening and findings screenshots locally.
- Structured source/artifact inspection and full suite verify text escaping,
  plain-text/table reports, section order, grouped/full items, evidence, and
  context-first comparison.

## AEC and authority

Purpose-link references resolve. Before implementation, aec check reported zero
errors and warnings. Final regenerated snapshot: **751 edges from 16 files**; aec check: **0 errors,
0 warnings**. The old/new code-impact report flags the old slice-1 satisfaction
claim/evidence and the new implementation-linked refinement/claim/evidence for
review; exact statuses are reported in the PR. These are structural review
signals, not invalidated obligations or owner acceptance. The post-change tests
and table review provide fresh bounded evidence; old candidate records stay in
history rather than being silently edited. All original record bytes and protected documents are checked against
merged main. No accepted requirement was edited or accepted again. The added
algorithmic refinement stays provisional; new claims/evidence are candidates.

The branch started from requested 968df98, then rebased on 83179e7 after PR #3
merged, before edits. Planning/records preceded implementation in commit history.
No force-push, main push, merge, prior Data Guide code or absent reference was used.

## Limits and drift

The fourteen intent-note readings explain thresholds and scope. No completeness
or independent outcome claim: sparse sentinel vocabulary, exact co-missing masks,
median-split contrasts, lexical/affine redundancy, inferred day cadence and
bounded screens can miss other patterns. Full findings are retained; summarized
views group repeated families/kinds and expose evidence without deleting them.
No new application dependency, connector, narrative subsystem, advanced analysis,
FT-R7 target-method suite or FT-R8 chart control was added.
