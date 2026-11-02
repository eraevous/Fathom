# Intent: report and univariate slice (HO-20261102-001)

Agent readings, not new owner decisions; FT-R14 stays provisional.

1. Title/description precede dictionary → provenance → summary → findings →
   relations. Samples belong to dictionary. Evidence/rules/hashes stay collapsed.
2. Samples default to 20 (0..100), seed 0 (0..2^32-1), text limit 120 (20..1000).
   Windows may overlap; random is without replacement and displayed in row order.
   Preserve original CSV lexical cells alongside canonical missing values in the
   input wrapper; only bounded, visibly truncated samples enter the artifact.
3. Description is a deterministic schema sketch, never inferred domain fact;
   supplied title/description/units/roles are labelled human.
4. Numeric currency/thousands/parenthesis parsing is labelled; currency symbols
   do not establish units or exchange rates. Quantiles use linear interpolation;
   skewness/excess kurtosis use population standardized moments (undefined→null).
   Histogram has <=10 sqrt(n) bins; box uses min/25/50/75/max, no fitted density.
5. Blank candidates preserve empty/whitespace/token distinctions without conversion.
   Common substrings means case-folded word tokens of length >=2 (top 10), not
   arbitrary substring mining. Rare means count<=2 or share<=1%; entropy is bits.
   Casing examines alphabetic characters; special characters exclude whitespace.
6. Dates: strict ISO, English month-name dates and slash dates; format evidence is
   kept. Numeric ambiguity defaults month-first with alternatives and a question;
   a date_format override can choose explicitly. Two-digit years use fixed pivot
   69 (1969..2068) and are always flagged, never silently repaired. No locale or
   runtime-clock dependence. Snapshot dates govern future checks; without one,
   only year>2100 is called beyond a fixed bound. 1900-01-01/1970-01-01 are possible
   placeholders, not known defects. Invalid dates are not coerced.
7. Temporal lag-1 uses consecutive monthly counts including zeros, switching to
   years beyond 1200 months; constant/short series is undefined. Time charts show
   <=60 periods and disclose omitted middle periods; no stationarity/causal claim.
8. Identifier-like means declared key/role or id/key/code/title/name in the name;
   repeated titles may be legitimate. Quantity-like means human role or amount/
   gross/revenue/cost/price names. Rare zero candidates require >=5 finite values,
   <=20% zeros and median positive nonzero>=100 and at least80% of nonzero values>=100 recorded units; ask for meaning.
9. New fields are additive in artifact v1; old artifacts keep unavailable fields
   unavailable. No quality score/subscores. Existing slice-2 relations unchanged.
10. Builder tables are synthetic; later audit tables are not independent blind
    acceptance. Report all misses and proposed FT-R14 refinements openly.

Drift check: univariate helper and parse helpers remain profiler responsibilities;
chart specs are in the artifact and renderers never read source tables. No new
runtime dependency or advanced pair-analysis subsystem for this feature.
