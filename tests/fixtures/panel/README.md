# Synthetic panel fixtures
All tables are authored synthetic data. Rebuild with generate.py (seed 20261105).
No source data, model fitting, organisation names, custom metric definitions or
real volume settings. truth.json records source row/state/zero/quantity counts.
panel.yaml uses only a deliberately synthetic volume boundary; there is no default
in product code. joined.yaml adds arbitrary metric_a/b/c quantities and model/window/
horizon labels. One missing signal match and one extra metric key are intentional.
Poisson/NB/burst/closure/missing/change/weekly/annual/exposure patterns are plants.
The regime-age omission and all other found/missed results are in spec 014 validation.
