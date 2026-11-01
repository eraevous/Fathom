# Validate the slice

Use Python 3.12 and a virtual environment:

```bash
python -m venv .venv
.venv/bin/pip install -e '.[test]'
.venv/bin/python -m pytest
.venv/bin/guide profile tests/fixtures/review.csv --config tests/fixtures/review.yaml --out reports/before
.venv/bin/guide profile tests/fixtures/revised.csv --config tests/fixtures/revised.yaml --out reports/after
.venv/bin/guide render reports/before/guide-profile.json --out reports/rendered
.venv/bin/guide compare reports/before/guide-profile.json reports/after/guide-profile.json --out reports/comparison
```

Open report.html offline. Inspect the missingness and duplicate observations,
their separate review actions and evidence links, the dictionary, human metadata,
inferred readings and open questions. Compare contexts precede measured deltas;
the report does not claim lineage or causes. Regenerated report bytes must match.

Optional: install `.[stats]` and request numeric target pairs; p-values become
available. With SciPy unavailable, counts and coefficients are unchanged and the
p-value field explicitly reports unavailable. The core review loop still works.

Run the AEC commands in AGENTS.md after installing its pinned tool. A passing
structural check is not owner acceptance or evidence of usefulness in real work.
