# Identifier roles and key documentation

Declare known roles in YAML or the configurator:

```yaml
columns:
  account_code: {role: identifier}
  measured_count: {role: quantity}
```

The role is separate from effective type: an identifier can be numeric or text. Inferred identifier-like suggestions stay unticked. Existing declarations prefill; choose `quantity` to override identifier inference, or default to restore it. A schema key is a human key declaration. Role declarations do not establish what an entity means or whether a key is valid for a business process.

The Identifiers section lists raw-label counts, missing values, distinct/repeated labels, rows beyond first occurrence and rows participating in repetition. It distinguishes uniqueness among populated cells from a complete row-key candidate. Repeating labels may be entity keys or collisions; the report asks rather than decides. Up to ten literal duplicate examples and one-based positions are shown, with omissions disclosed.

Length and run-length character-class patterns describe observed formats; variation is not an invalidity verdict without an owner rule. Pattern classes are Unicode digit(D), upper(U), lower(L), other letter(A), whitespace(W) and literal punctuation. Leading zeros are counted and preserved. Raw labels `001` and `1` remain distinct.

Numeric labels are read exactly (no floating-point collapse above2^53). Input-row ordering omits missing values and reports strict/non-strict increase/decrease, constant, mixed or insufficient. Fractions have ordering but no assumed integer step. Integer gaps are counted/ranged only between observed labels, never expanded into rows or called missing records. Numeric readings with more than1,000decimal digits of magnitude are not computed and say why. Raw key identity remains unchanged.

Identifier-role columns are excluded from per-type distribution summaries and every target-ranking path before budget selection, including missingness-quality candidates. Identifier targets have an explicit exclusion reason. Ordinary dictionary and QA evidence remains available. Summary-only export decks keep their existing budget; full decks/PDF include identifier tables.

Profile links resolve to repeated-key findings or declared grouping only where present. Profiles do not invent a panel-file URL. Panel reports document their actual declared series-key components, link actual series entries and label counts as whole source-input counts, separate from training-model parameters. Components can repeat in a composite series key.

Older artifacts without identifier details remain readable and request re-profiling for unavailable key/format counts. No PII classification, automatic key repair or entity semantics are introduced.
