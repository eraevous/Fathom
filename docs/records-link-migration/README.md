# Records link migration (HO-DG-20261104-XKSJ item3)

Relation metadata only. No app output or requirement assertion changed, no
requirements accepted, no human decision accepted, no experiment/replay run.
Stacked after PR16 review and PR17 (spec009). The project AEC pin is unchanged.

## Direction and scope

The AEC vocabulary defines **requirement → implemented_by → code**. It deprecates
`implements` and ignores it in impact propagation. Simply renaming a
claim→requirement link to implemented_by would remain wrong. Latest claims instead
use **depends_on** for their governing contracts/readings; the four explicit
claim→code bindings on FT-TA-C2 become depends_on code. Requirements carry actual
partial implementation paths; reading requirements depend on governing contracts.

[Version mapping](versions.json): **67 appended metadata-only versions**:
25 requirements, 10 claims, 22 evidence, 8 evaluations, 2 proposed decisions. The propagation
of repins is intentional: existing evidence must still support each equivalent new
claim; evaluations must keep that evidence lineage. Otherwise a claim migration
silently loses its supporting observations. All text, epistemic status, authorities,
tiers, anchors, methods and limits are unchanged. No new measurement/observation is
claimed by an evidence metadata version. Older contract pins with different wording
(for example FT-DQ-C1's FT-R6@2) remain pinned rather than silently adopting new scope.

Latest records now have **0 implements / 37 depends_on**, up from 0/1 at this branch's
base. The historical PR15 head had 0 depends_on; item 1 introduced the single existing
one. Deprecated historical lines remain citable and byte-for-byte unchanged.
`migrate.py` is deterministic, idempotent, dry-run by default and preflights a candidate
append with the installed pinned AEC before writing. No runtime dependency added.

Direct bindings in `migrate.py:PATHS` are reviewed partial satisfaction-review paths,
not statements that a requirement is met. FT-R4's report path cannot establish owner
usefulness; FT-R17's capture path cannot establish adequate visual judgement. New
links are post-review metadata, not evidence that the original author could have
seen or acted on them. No invented implementation for unbuilt FT-R8/target axes.

## Frozen diagnostic: exact PR15 diff

Source trees **3b89d7c..3367ab3**, full SHAs and input digests in [audit.json](audit.json).
Snapshots regenerated from those exact trees with project pin
**860b7815f208fac09c4e2ba57e5fbfe418ed2ba7**, AEC0.4.0, Python3.12;
extractor 0.3.0, same method for both. Base 1802 edges / 29 files;
head 2117 edges / 33 files, no skipped files. Full snapshots committed under snapshots/.
Only the ledger differs between before and after, not the source diff or tool.

| Ledger | Events | Affected / unaffected | Governing obligations named |
| --- | --- | --- | --- |
| [Historical3367ab3](historical-head.md) |20|23/45|Neither FT-R7@2nor FT-R18@1 |
| [Pre-migration10cf8c2](before.md) |20|28/55|Neither FT-R7@2nor FT-R18@1 |
| [Migrated current ledger](after.md) |21|42/41|FT-R7@3and FT-R18@2(same obligation text, new link metadata) |
| [Ablated new governing code links](ablated.md) |20|30/53|Neither current governing record; reading still reached |

One extra event comes from newly referenced spec007's capture function. More affected
records is not automatically better: broad report/export links are review pointers,
not defect evidence. The negative control removes only new governing bindings and
loses governing reach again, while retaining the reading. Before/after raw reports
are retained without rewriting statuses or shortening them to a success claim.

**This does not change the recorded historical P1 failure.** P1 was specified against
the original ledger at 3367ab3 and a different protocol pin. This is an authorized
records-hygiene diagnostic on a repaired, later ledger, not a P1 rerun, a trial,
a regrade, or proof of a Telosmith benefit. No DEC-021 replay was run.

## Verification and reproduction

Five tests in tests/test_record_links.py cover committed-prefix integrity and every
assertion field, relation direction and current support lineage, determinism/
idempotence and snapshot hashes, exact before/after impact outputs, and ablation.
The first 3 are stdlib metadata checks. The 2 impact diagnostics skip when the existing
AEC development tool is absent (no runtime/optional package added to Fathom).

```bash
python -m pytest -q tests/test_record_links.py
python -m aec check .aec/records.jsonl --edges .aec/edges.jsonl
python -m aec code-impact .aec/records.jsonl docs/records-link-migration/snapshots/base.edges.jsonl docs/records-link-migration/snapshots/head.edges.jsonl
```

To reproduce before: take exactly original_prefix_bytes of the current ledger
(audit.json), verify original_prefix_sha256, and pass that file to the same command.
Historical comparison uses `git show 3367ab3:.aec/records.jsonl`; no code change or
replay material is injected. To regenerate snapshots, make detached worktrees at
the two audited source SHAs and run `python -m aec edges . -o OUTPUT` from each root.
No source checkout was embedded inside Fathom's scan; no archived Data-Guide code read.

The ledger diff is append-only; all protected docs/decision passages unchanged in
this item. Application src/ unchanged, so the migration cannot change report bytes.

Final validation: **222 passed** with extras and AEC development tool; core
**211 passed / 11 skipped** (9 existing optional cases plus 2 AEC diagnostic cases).
AEC snapshot 2857 edges / 44 files, 0 skipped; check 0 errors / 0 warnings. Original record
prefix and every protected document/decision passage verified against 10cf8c2.
No application source changes.
