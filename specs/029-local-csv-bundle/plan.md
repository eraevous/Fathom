# Plan
Compose CSVConnector -> profile -> existing renderers; add no dependencies.
Validate complete manifest structure before processing. Validate each local source
boundary before reading. Keep table errors separate from manifest/output errors.
Build artifact strings before publishing to a newly created output directory.
Preserve relative source names rather than machine-specific absolute paths.

Trade-off: no overwrite/rerun-in-place, no discovery/globbing, no relationship
analysis. This avoids stale artifacts and keeps the slice independently reviewable.
Local path checks are not a sandbox against concurrent malicious filesystem edits;
run only against a stable local input tree. Normal reports may expose source values.
