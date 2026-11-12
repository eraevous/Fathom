# Try a local CSV bundle

Save beside two synthetic CSVs as `bundle.json`:

```json
{"version":1,"tables":[
  {"id":"observations","path":"observations.csv","config":{"row_unit":"observation"}},
  {"id":"categories","path":"categories.csv"}
]}
```

Run `guide bundle bundle.json --out new-report-directory` and open `index.html`.
Each table's `config` uses the existing inline profile configuration vocabulary.
A row unit is a declaration, never inferred as domain fact. Configuration values
and metadata remain in the standard per-table artifact. Source SHA-256 hashes
identify the bytes used; the manifest hash identifies the requested configuration.

Exit 0 means every table produced reports, not that its data is correct. Exit 2
means invalid manifest, output failure, or one or more failed tables. For partial
failures, inspect `bundle-index.json`; successful tables are still available.
Failure details are intentionally bounded to avoid copying machine paths or data
into errors; run `guide profile` on a failed source for its ordinary local details.

Output directory must not already exist. Inputs must be stable local files beneath
the manifest directory (no parent traversal or escaping symlinks). Reports can
contain values and declared context; review them before sharing. The bundle is
not automatically public, sanitized, compressed, joined, or a relational database.
