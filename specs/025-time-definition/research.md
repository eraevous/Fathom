# Research decisions
- Decision: portable %F for integer frame index plus declared numeric rate. Rationale: requested spelling fits existing token serializer; document difference from POSIX ISO-date shorthand. Alternative: named FRAME builtin would obscure field-level definition.
- Decision: no frame-to-microsecond conversion. Rationale: would round and imply unrequested synchronization/drop-frame semantics. Keep count/rate separate; decline chronology explicitly.
- Decision: unknown fourth retained lexically and excluded from sub-second summaries; valid firstthree fields remain useful. Alternative: discard entire row would lose clock evidence.
- Decision: native disclosure + select per ordered field, exact literal separators/ignore. Rationale: keyboard/no-JS accessibility, no wildcard addition. Max evidence names common rates, not an inferred semantic verdict.
- Decision: add rate to both controlled YAML builders. Research found base_columns overlay would otherwise overwrite edits. No unresolved design question blocks this narrower scope.
