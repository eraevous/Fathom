# Local CSV bundle (proposed implementation contract)
Serves: P0@2, DG-RA@1, DG-RB@2, DG-RE@1, DG-RF@1.

A local analyst can profile several named CSV tables and navigate their reports
without pretending they form one table. This is a bounded slice of issue #39 and
the owner's November 12 request for multiple datasets and bundling. It does not
accept a new project purpose or implement the separate SQLite intake work.

Manifest JSON version 1: `version`, `tables`; each table has a unique portable
`id`, relative `path`, optional inline existing Fathom `config`. No unknown fields.
Sources must resolve beneath the manifest directory. No joins, inferred links,
network access, archives, SQL, new adapters, or new profiling computations.

Each successful table retains ordinary profile JSON/HTML/Markdown. A separate
bundle JSON index records manifest/source hashes, declared row unit (or null),
status and relative artifact links; an HTML index is derived from that index.
A failed source/config produces a visible per-table failure, never a silent skip;
other tables still run. Invalid manifest structure rejects the entire run.
Outputs require a new directory to prevent stale success reports and overwrites.
Synthetic tests cover success, failure decoys, escaping, traversal, symlink escape,
determinism and preserved single-table artifacts. Independent review and owner
acceptance remain outstanding.
