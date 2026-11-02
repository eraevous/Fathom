# Builder validation

python -m pytest
guide profile tests/fixtures/univariate/film.csv --config tests/fixtures/univariate/film.yaml --out reports/univariate
guide render reports/univariate/guide-profile.json --out reports/univariate-rendered

Inspect dictionary/provenance/summary/findings/relations order, samples and seed,
chart titles/axes, zero gross, repeated title and date warnings. Compare report
bytes after saved-artifact rendering. See validation.md for found/missed.
