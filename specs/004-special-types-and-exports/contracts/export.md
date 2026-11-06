# Export contract

`guide export PROFILE.json --out DIR [--formats pdf pptx]` defaults both optional
formats. Valid saved artifact required. HTML/Markdown always written; each binary
is independent. Unavailable dependency is explicit in export-status.json and exit 0;
invalid input exits 2 before output. Comparison artifacts can export context/deltas
without column/sample/chart topics. PDF/PPTX never open source CSV or fetch assets.

Special types may be supplied as column type overrides. Automatic recognition is
labelled inferred. No new config for lookup/credentials or sensitive-data tags.
