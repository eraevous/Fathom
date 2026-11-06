# Review locally
Use the existing test/stats/exports extras (no new runtime dependency).
Run `PYTHONPATH=src python -m pytest tests/test_report_style.py -q`.
Run review/build.py with /tmp/style-before using #29's src on PYTHONPATH, then with
/tmp/style-after and /tmp/style-repeat using this branch. The inputs are identical.
Run review/capture.py with Playwright/Chromium available, offline contexts enabled.
Convert actual PPTX with local LibreOffice to /tmp/style-slides/report.pdf, then
run review/export_capture.py with PyMuPDF. Review-only tools are not runtime deps.
Compare all three JSON files parent/new and every file after/repeat; see identity.json.
