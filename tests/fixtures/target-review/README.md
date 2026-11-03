# PR15 review regression fixtures

All CSVs are authored synthetic data; YAML declares the target and effective category
readings. No external/private data or new dependency.

- boxes.csv: nine zeroes+50, nine negatives+50, ten zeroes, ten positive quantities,
  one large tail value. Log boxes must label plotted n1/excluded9/small, n0/excluded10,
  and clean positive n10/excluded0. Complete group summaries remain unchanged.
- tiny.csv: nine A values1e-12 and one B value1e-7. Positive grouped-box geometry must
  remain positive/unrounded; statistical percentile rounding is intentionally unchanged.
- rates.csv: three groups, three outcome levels, one long label containing angle
  brackets. Checks horizontal shares/vertical groups and exact accessible rate tables.
- scatter.csv:50 deterministic numeric points for the plotted coordinate disclosure.
- high-cardinality.csv:20groups×20levels,400rows, exactly independent distributions.
  All groups and levels must appear on non-overlapping PowerPoint panels/legends.

See tests/test_review_fixes.py for exact assertions, legacy/zero/linear/ordinary-deck
and valid-artifact decoys, and spec007/review-fixes-gallery for actual image evidence.
