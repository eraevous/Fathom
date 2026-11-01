# Intent: the first data-to-decisions slice

Author: codex:aec. Handoff: HO-20261101-004. Date: 2026-11-01.
Status: implementation readings/proposals; Zach has not accepted FT-R1.

## Purpose and authority

Implement `DG-D1@1` through the decision “what needs review before using this
table?”, while preserving `P0@2` and the six requirements. No acceptance is claimed
from code, tests, this note or a PR. Existing records and guiding documents stay
unchanged. No archived implementation was accessed.

## Gaps and narrower readings

1. **MVP breadth**: April lists six connector families, both shapes and guided CLI;
   later DG-D1 defines an outcome. Select one local CSV/wide path and an offline
   report that supports that outcome. Defer globs, Excel, JSON, SQL, Snowflake,
   credentials, long-shape profiling, guided mode, dashboard and advanced EDA.
   Preserve SchemaContract's shape/key/context/metric/value/type slots but reject
   long rather than silently pretending it is supported. This is a proposed slice,
   not a claim to have completed the April checklist.
2. **What is a decision?** Conditional review suggestions linked to counts, plus
   human decisions/rationales, are the smallest loop. Do not delete, impute, approve
   modeling, diagnose business causes or invent a fitness threshold.
3. **Unknown semantics**: explicitly ask about row unit, generating process and
   missingness mechanism; ask column meanings when absent. Human declarations
   carry human provenance; no numeric encoding establishes a domain meaning.
4. **Rules and confidence**: conservative deterministic lexical routing (boolean,
   ISO date, finite numeric, small repeated categorical, otherwise string). Label
   confidence as rule-based, not a calibrated probability. Preserve reasons and
   alternatives, including numeric codes. Any human type override wins without
   erasing inference; invalid numeric/date values under overrides are counted.
5. **Nulls and duplicates**: whitespace-only cells count as missing; `NA` and `null`
   remain literal values. Repeated full rows count beyond their first occurrence,
   with no assumption of an error or key. Do not infer the missingness mechanism.
6. **Selection**: explicit target, input-order candidates, default five pairs and
   hard maximum twenty. Only Pearson coefficients and grouped numeric summaries;
   no all-pairs, automated causal claims or inferred question answering. Unsupported
   pairs and budget exclusions retain reasons. No target means no pairs.
7. **Artifacts**: schema version 1, fixed ordering/rounding, input SHA-256 and
   explicitly supplied context. Missing dates remain null, not runtime timestamps.
   Bounded frequency/examples are data documentation, not a full data copy. Human
   notes/decisions live in configuration and the artifact; no separate state store.
8. **Comparisons**: aggregate row/schema/quality/shared-column deltas only, both
   contexts first; no row matching, attribution of cause or lineage reconstruction.
9. **Charts and optional dependencies**: embedded HTML bar charts for missingness
   and frequencies; no external assets or plotting library. Optional SciPy enriches
   numeric pairs with a p-value only; missing SciPy leaves coefficients intact,
   marks p-values unavailable. No p-value is a decision threshold.
10. **Scale**: local in-memory tables, no service or scale promise. No new storage,
    orchestration, plugin system or narrative subsystem is needed.
11. **Constitution governance**: the scaffold asks for additional governance and
    version policies absent from CHARTER. Omit them rather than invent rules.
    Version 1.0.0 labels this restatement, not a new owner acceptance.
12. **Clarification workflow**: follow the handoff's instruction to use narrower
    readings rather than asking design questions. Clarification records below are
    agent readings with citations, never fabricated owner answers.

## Drift check

The planned components keep the charter's Connector → GuideDataFrame → Profiler →
ProfilingResult → Renderer responsibilities. The only new code is this path and a
thin CLI. Comparison uses saved results; renderers never reopen the CSV. More time
should go to measured findings, uncertainty and reader actions than machinery.

## Validation limits

Synthetic tests can establish conformance and reproducibility, not usefulness for
most projects, trustworthiness of supplied context, or Zach's acceptance. A review
queue is evidence for the proposed MVP slice, not proof of the purpose's outcome.
