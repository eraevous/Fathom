# Verify

pip install -e '.[test,exports]'
python -m pytest
guide profile tests/fixtures/special/planted.csv --out reports/special
guide export reports/special/guide-profile.json --out reports/special-export

Open the PDF and PPTX; inspect summarized findings, sample tables and chart axes.
Repeat export into another directory and compare bytes. Run core tests without
extras and assert unavailable status while HTML/Markdown remain. See validation.md.
