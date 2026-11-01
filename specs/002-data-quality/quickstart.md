# Validate slice 2

Use the existing Python 3.12+ setup and install -e '.[test]' (optional .[stats]).

```bash
python -m pytest
guide profile tests/fixtures/quality/workshop.csv --out reports/quality
guide render reports/quality/guide-profile.json --out reports/rerendered
guide profile tests/fixtures/quality/clean.csv --out reports/quality-clean
guide profile tests/fixtures/quality/holdout.csv --out reports/quality-holdout
```

Open the report offline, read only it against planted.json, expand evidence, and
switch Show full per-item detail on/off. Check summary totals, selected contrasts
and exclusions. Compare generated and re-rendered bytes. Record found/missed and
false alarms in validation.md; do not claim Zach/Kate's acceptance tables passed.
