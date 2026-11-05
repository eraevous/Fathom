# Verification
Run tests/test_offline.py first, then tests/test_panel.py and the full/core suites.
Run guide panel tests/fixtures/panel/panel.csv --config tests/fixtures/panel/panel.yaml
--aggregate week,month --out reports/panel.
Inspect state counts, training-only estimates, conditional floors, joined keys and
disagreement counts. Re-run with different PYTHONHASHSEED and compare every file.
Review panel.html and an aggregate view at1280/390 light/dark; check browser requests.
Compare native/aggregate training estimates after perturbing evaluation only.

