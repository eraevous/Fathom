# Intent: report polish, HO-20261102-003

1. FT-R18 explicitly authorizes native default-closed column entries, static CSS
   grid/phone stacking and scalable charts. No drag/reorder/filter/axis controls.
   Measure both default and all-columns-expanded heights, same fixture/config.
2. Numeric display rounds to magnitude (large values whole, small values enough
   significant digits); declared degree units retain5decimals. No invented currency
   units. Numeric examples formatted, raw examples retained; identifier lexemes stay
   literal. Logical order rows/valid/missing/invalid/distinct, min/q1/median/q3/mean/
   max, spread, zeros/negatives. Compact stats width; supplemental tables disclosed.
3. Log eligibility uses existing overall population skew>=2 with >=2positive values;
   log bins include only positives; zero/negative/invalid counts explicit. No offset
   is invented, no cleaning. Constant/no-positive/benign decoys no log. Linear stays.
4. Near-unique means >=90% distinct among >=5nonmissing values; identifier role
   (human or existing inferred cues) also suppresses top-N bars. Frequencies stay
   in artifact/tables; explanation says values rarely repeat or identifier-like,
   not that repetition is necessarily a defect. Applies legacy render too.
5. Intermediate ticks are deterministic normalized linear positions, compact K/M/B
   or percentages where needed; numerical geometry stays true. Box labels in
   separate readable summary, axis captions horizontal/wrapping outside SVG marks.
6. Default PPTX<=12slides:5overview/finding/unknown topics +<=7representative charts,
   deterministic priority/column coverage; visible omission/mode notice. Full via
   --deck full. No target/group analysis added; selection is presentation only.
7. Before is PR#11 head; public Vega movies and FiveThirtyEight recent-grads pinned
   with hashes, source/conversion recorded. These are builder review, not unseen
   acceptance. Existing review tooling only, no new runtime dependency.
8. Local merge of the decision branch is explicitly requested despite AGENTS' broad
   'never merge' rule; this is record integration only, not merging either PR/main.
   Preserve both record suffixes byte-for-byte; rebase after#11/#12merge, no force push.
