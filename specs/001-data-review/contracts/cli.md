# CLI contract

`guide --version` and `python -m fathom` expose the same local CLI.

```
guide profile INPUT.csv --out DIR [--config CONFIG.yaml]
guide render PROFILE.json --out DIR
guide compare BEFORE.json AFTER.json --out DIR
guide validate INPUT.csv [--config CONFIG.yaml]
```

Success exits 0. Invalid input/config/artifact exits 2 with a concise stderr
message and no traceback. Profile/render write guide-profile.json (profile only),
report.md and report.html. Compare writes guide-comparison.json, comparison.md
and comparison.html. Validation prints the resolved schema and writes no reports.
Output directories are created after complete successful computation/rendering.

Configuration keys (all optional): `question`, `target`, `pair_budget`, `columns`,
`row_unit`, `generating_process`, `missingness_mechanism`, `decisions`, `context`,
`schema`. Omitted question uses documentation/QA fallback. Schema/context and
column metadata follow data-model.md. Unknown keys/references fail. YAML is safe
data, never executable. Decisions do not execute transformations.

Version-1 JSON uses UTF-8, sorted keys, two-space indentation, newline terminator,
no NaN/Infinity. Array order is input/rule order; no runtime timestamp, random ID,
absolute-path resolution or environment fingerprint. Dependency availability is
explicit. HTML/Markdown derive solely from the validated saved result. See
data-model.md for all artifact entities; schema_version and kind dispatch fail
closed for unknown versions/kinds. Narrative generation is absent.
