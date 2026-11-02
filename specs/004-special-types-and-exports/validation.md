# Builder validation: 004 special types and exports

HO-20261102-001. Authored synthetic data only; builder evidence does not establish
Zach/Kate's independent acceptance on unseen tables.

| Table | Found in report | Missed / review noise |
| --- | --- | --- |
| special/planted.csv, 24x7 | One repeated-digit phone placeholder, one short phone, one malformed email, one test-like email, two malformed/invalid-port URLs, latitude91 and longitude−181; domain counts and inferred recognition labels retained | All eight planted special problems surfaced as findings/actions; no supported planted family missed |
| special/clean.csv, 24x7 | All five types recognized; common domains and valid counts; no special review actions | No planted problems or special false alarms; syntax success is not real-world validation |
| special/late.csv, 5x6, authored after implementation commit | Phone extension incompatible with the narrow grammar; two email forms outside practical ASCII grammar; FTP and port0 outside URL policy; two coordinates outside inferred degrees; test2 email candidate | Does not recognize valid extension/internationalized/quoted-email/FTP forms; centidegree4500/−7500 gets a degree-range review; structurally valid example.invalid email/URL passes with no liveness knowledge (no lookup permitted) |

The reports alone expose consequences: which contact/location fields need owner
review, counts/examples, explicit policy limits and suggested actions. Dictionary,
raw samples, provenance, summary and unknown meanings provide documentation without
opening CSVs. Silence on liveness is labelled, not a pass. The late table was not
used to tune the grammar. Its unsupported cases remain visible limitations.

## Exports and tests

Planted: PDF20 pages, PPTX24 slides/9 native charts. Clean: PDF20 pages,
PPTX23 slides/9 charts. Late: PDF14 pages, PPTX21 slides/8 charts. PDFs opened with
pypdf/PyMuPDF; text extraction confirms ordered sections, all three sample windows
and recorded seed0. The planted PDF first page was visually inspected; table
headers repeat, long cells wrap and wide samples split columns. PowerPoint opens
with python-pptx; native charts have both axis titles. Slides separate summary,
finding kinds and individual charts; box views use native shapes.

Repeated calls and separate CLI processes produce byte-identical PDF, PPTX,
HTML/Markdown and status. PDF invariant metadata, PPTX fixed properties/ZIP times
and embedded-XLSX properties/ZIP times eliminate clock variation. Serializer
versions are recorded (local ReportLab4.4.9/python-pptx1.0.2). Different versions
can produce different bytes. No network/font service/source CSV is consulted.

Missing both or one optional serializer is explicit and independent; core views
still work. Invalid artifacts fail before output. PDF's bundled Vera font replaces
unsupported characters with `?`, with visible notice and status count: late table
36 rendered occurrences replaced. Exact originals remain in JSON/HTML/Markdown.
PDF is a summarized report with samples, not a byte-for-byte print of HTML;
PowerPoint omits the full dictionary and sample tables as FT-R13 permits.

Final local suite: **134 passed** with SciPy and both export extras; **129 passed,
5 skipped** in core (one optional SciPy test, four serializer tests). New special
tests cover violating/clean examples, overrides, date/phone ambiguity, exact
builder counts and rendered findings. Export tests cover absent dependencies,
content, fresh-process bytes, native charts and Unicode disclosure. Old tests pass.

No quality score, sensitive-data tagging, new pair analysis or AI narrative. AEC
structural checking and code-impact review do not certify usefulness. Original
record prefix and protected documents remain unchanged. This PR stacks on003 and
targets main; neither PR is merged by Codex.
