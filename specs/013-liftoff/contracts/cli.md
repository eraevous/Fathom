# CLI and page contract

`guide liftoff DATA.csv --out DIR` → liftoff-profile.json(schema2),liftoff.html.
No --config. On invalid input no partial output directory. Page contains Brief,
Configurations, read-only rules, exact-evidence details and generated YAML pane.
No selections →{}; selected controls → supported existing config keys only.
Download liftoff.yaml + separate advisory config-manifest.json with YAML digest.
`guide profile DATA.csv --config liftoff.yaml --out REPORT` is unchanged.
Standalone `guide configure` retains its existing output filenames and behavior.
