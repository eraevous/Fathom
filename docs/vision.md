# Fathom vision (formerly Data Guide)

**What this is:** a working synthesis of Zach's 2025–2026 conversations about Data Guide, written by ChatGPT (Kate) on 2026-10-27. The original is in Zach's Drive: *Data Guide — Recovered Vision, EDA Philosophy & Claude Handoff*. It describes itself as a working synthesis, **not an approved specification.** What Zach has since accepted is in `.aec/records.jsonl`, with his words in `docs/decisions/`. Where this document and those records differ, the records win.

**Edited for a public repository (2026-11-01):** the following were left out:
- a paragraph on discussions at Zach's employer;
- the details of a 2025 case study, kept here only as the principle it illustrated;
- the section on the old repository's code history;
- the source list.

Nothing else was changed in meaning.

## 1. Identity and intended outcome

Fathom turns raw or semi-cleaned tabular datasets into understanding that is useful and can be communicated. It is meant as an enhanced data dictionary, a diagnostic EDA engine and a repeatable working record, not merely an automatic plot generator.

Its outputs serve several audiences and moments:
- **the working data scientist:** find structure, errors, hypotheses and transformations;
- **a collaborator or reviewer:** repeatable, auditable evidence;
- **stakeholders:** concise observations and decision support.

A point-in-time data snapshot and an exportable report are part of the vision.

## 2. Scope and features

### Profiling and semantics
- **Whole-dataset summary:** shape, schema, observed data types and inferred semantic types, granularity, missingness, duplicates, suspicious records, quality indicators and distributional composition.
- **Column-level dictionary:** meaning where known, examples, counts, nulls, frequency patterns, unique values, a visualization, diagnostics, and short evidence-based observations.
- **Types:** numeric, categorical, boolean, string, temporal, and specialised formats such as phone numbers and addresses. Automatic type inference must be overridable, and marked uncertain where appropriate.

### Distributional and relational EDA
- **Numeric:** central tendency, quantiles, variation, skew, kurtosis, frequency of zeros and negatives, outliers and distributions.
- **Categorical:** counts and rates, entropy, dominance, rare levels, and dummy or test values.
- **Temporal:** coverage, gaps, volume patterns, trends and seasonality.
- **Quality:** invalid formats, duplicates, sparse periods, suspect categories, schema drift and, potentially, join lineage.
- **Bivariate**, across meaningful type pairs (numeric×numeric, category×numeric, binary×numeric, category×category, binary×binary), with association and effect summaries suited to the types.
- **Multivariate and target-conditional:** segment comparisons, distributions by outcome, small multiples, correlation matrices, mosaics, Sankey flows and contextual visual diagnostics.
- Avoid plots that look impressive but can't be read, such as categorical parallel-coordinate plots.

### Workflow and deliverables
- **Workflow:** acquire and join → first-pass EDA → cleanse and transform → re-profile and compare → refine. The first-pass EDA should inform cleansing, rather than cleaning being a blind prerequisite.
- **Deliverables:**
  - machine-readable profile artifacts (JSON proposed);
  - a navigable data dictionary and report (Markdown or HTML) with embedded visual evidence and concise callouts;
  - transformations and before/after deltas;
  - optional PDF or PowerPoint export;
  - reproducible provenance.

## 3. Understanding before modelling

Zach's four-part framing (December 2025) is Assumptions, Data-Generating Process, Exploratory Data Analysis and Usefulness. The readings below synthesise several discussions; they are not a verbatim definition.

- **Assumptions:** expose what is being presumed about the row unit, variable semantics, mechanisms, completeness, timing and appropriate comparisons. Don't let a name or an encoding stand in silently for meaning.
- **Data-generating process:** consider how observations arise, what is collected and what is omitted, artifacts of workflows and sampling, and whether differences are causal, operational or merely recorded. Surface uncertainty about the process rather than fitting models as though the table were the whole system.
- **EDA:** understand the actual structure before intervening: shape, missingness, distributions, concentration, segmentation, interactions, dependencies, anomalies, temporal coverage and change over time. EDA should explain and diagnose; it is not a plot checklist.
- **Usefulness:** ask what decision becomes better, who would act, what a result justifies, how errors matter, and how evidence becomes an action, a model choice or a request for more data. An accurate model or a polished visualization without decision value is not enough.

**Principles the original illustrated with examples:**
- **Interrogate the schema's semantics, not just its statistics.** A category in a "diagnosis" field that is actually a service line, not a diagnosis, is a semantic problem.
- **Treat heterogeneity as a hypothesis.** Different subgroups may follow different processes and need different models; that is a hypothesis, not a deployment recommendation.
- **Standardised, inspectable dataset understanding beats ad hoc visualization and tribal knowledge.**
- **Describe error structure without inventing explanations.** Model behaviour can be described without speculative business explanations.

**AI collaboration:** Zach asked for a thought partner (reflection, questioning, planning), not an AI that takes over the analysis. That shapes how any generated narrative is labelled and reviewed. It does not mean all profiling must be manual.

## 4. Working invariants (from the original; now accepted, with amendments, as DG-RA to DG-RF)

- **A.** Separate observations, descriptions, interpretations, hypotheses and recommended actions. Attach evidence, confidence or uncertainty, and provenance.
- **B.** Never present inferred semantic types or narrative interpretations as known domain facts. Overrides and alternative explanations are first-class.
- **C.** Let the analysis question and variable semantics govern which metrics and visuals are chosen. Avoid combinatorial dashboards that become unreadable or uninformative.
- **D.** Enable iterative re-profiling and before/after comparison.
- **E.** Keep a machine-readable data artifact as the stable interface, with stakeholder documents as derived views.
- **F.** Test metric accuracy, degradation when dependencies are unavailable, type routing, output reproducibility and preservation of the declared purpose.

## 5. Questions the original left open

1. What is the smallest functioning slice that embodies "understanding" rather than only profiling?
2. Which core artifacts are contracts, and which are presentation exports?
3. How should missing domain semantics and unknown data-generating mechanisms be represented?
4. How are bivariate and multivariate analyses prioritised without an explosion of pair plots?
5. What does it take for an observation to count as useful to a particular decision?
6. Where do human-authored interpretations and AI-generated hypotheses live?

Some of these are now answered by accepted records (for example `DG-A3`, `DG-A4`, `DG-RC`). The rest are open for the specification work.

## 6. Coordination

Zach keeps decision authority. Amendments should say whether they are historical evidence, a hypothesis, a design proposal or an approved decision.
