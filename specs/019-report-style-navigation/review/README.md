# Typography and navigation review — HO-DG-20261105-WJZQ

Stacked on #29 (`eab4d9329e347aa10000d8950895caccbe976e2b`), as requested.
Keep spec008's palette. No private Kairos sources or election-table copy.
The [shared rules](../../../docs/report-style.md) define N=8 and top navigation.

## What changed and why

The same short verdict/inferred/literal roles now serve HTML, Markdown, panel and
optional export text. Identity status comes from the artifact. Prose no longer
uses sentence-wide emphasis; chart titles no longer create a fourth heading level.
Three or more parallel facts use bullets; one/two headlines remain paragraphs.
Known identifiers, quoted values and examples are literal; a column/value named
`constant` cannot become a verdict merely through its spelling. Failed gates stay
failed and visible. Links alone receive underlining.

Existing per-finding disclosures remain closed, including generator/uncertainty/
provenance. The Brief's repeated Automatic/Provisional rule lines are now inside
the same disclosure; its conditional verdict still starts "If you declare". The
panel's multi-line full SHA/source rows moved behind a provenance disclosure.

One shared top navigation preserves the width available to plots/statistics.
Only present sections get destinations. Stored counts do not change when a detail
is expanded. Phone starts collapsed after enhancement, native buttons respond to
keyboard activation, no-script shows a static list, and print hides navigation.
No external CSS/JS, remote font or runtime dependency was added.

## Verification

Eight focused controls pass. The initial six-case check failed on the parent; two
later role/decoy controls and a separate demonstrated-red Brief rule-disclosure
assertion broaden the checks. Existing raw-markup/no-script assertions now test
visible text and allow exactly the local navigation script. Hostile-text checks
still prevent injection; only their inline-formatting assumptions changed.

Full extras, pinned Telosmith0.5: **419 passed, 2 frozen legacy-AEC snapshot skips**.
The complete socket-denied suite covers every command and optional export. Tests
inspect actual PPTX bold/italic/monospace/bullet XML and embedded PDF font faces.
[Identity evidence](identity.json):three parent/new JSON artifacts byte-identical;
every one of eleven generated output files is byte-identical on rerun, including
HTML, Markdown, PDF and PowerPoint. No analysis, gate, finding order or profile
schema change. Canonicalize a render-only copy to avoid an existing target-statistic
key insertion-order difference between fresh and JSON-loaded artifacts.

AEC structural check:0 errors /100 inherited warnings. Regenerated edges:5,975from78Python files,0skipped. Structural impact vs #29:
55affected /72with no status change /78pointers; these prompt review, not acceptance. Ledger retains the exact parent prefix;
followup(raw) is empty. Protected docs and decisions are untouched. Claims use
depends_on, requirements implemented_by, evidence supports the exact claim.

## Planted tables and acceptance

- Authored payments table:61 rows,31 cash zeros versus30 nonzero card values,
  one repeated start timestamp and one equal interval. The profile still finds
  group contrasts (means0/45.5), the selected categorical/numeric association and
  repeated timestamp. The Brief still shows cash zeros and the repeat, with
  conditional temporal/interval evidence available. Exact duplicate rows remain0
  because the two equal-start rows have different end values. All raw counts,
  thresholds, missed/unsupported analyses and finding order match the parent.
- Authored annual panel:52 rows,13 four-year observations ×2 entities ×2 candidate
  keys. Each of4 series retains13/49 usable annual periods and36 absent periods;
  absent is not zero. Unknown/insufficient estimates stay labelled; no inferred
  row meaning, aggregation or private-election claim. Monospace rules and short
  unavailable-state emphasis are visible in expanded details.
- Clean presentation decoys:declared descriptions stay plain; inferred descriptions
  italic; literal `constant`, quoted labels and hostile HTML stay literal; an
  ordinary sentence stays plain; an unmet gate still reads "not marked".

Against docs/acceptance.md:consequential existing facts remain available and their
status/evidence are easier to distinguish. No new diagnostic was intended or
added; no claim this replaces Kate's held-out usefulness judgment.

## Actual screenshots

28 screenshots at1280px and390px. [Browser checks](checks.json):zero resource
requests and no document horizontal overflow; present anchors resolve, native
keyboard toggle works, no-script links stay visible, print hides nav. Wide data
tables still use their existing local panning. [Export manifest](export-checks.json)
identifies actual PDF pages and actual LibreOffice-rendered PPTX slides; no mockups.

| View | Before1280 | After1280 | Before390 | After390 |
| --- | --- | --- | --- | --- |
| Same profile head | [before](before-profile-1280.png) | [after](after-profile-1280.png) | [before](before-profile-390.png) | [after](after-profile-390.png) |
| Same Brief head | [before](before-brief-1280.png) | [after](after-brief-1280.png) | [before](before-brief-390.png) | [after](after-brief-390.png) |
| Same panel head | [before](before-panel-1280.png) | [after](after-panel-1280.png) | [before](before-panel-390.png) | [after](after-panel-390.png) |

[Profile no-JS1280](after-profile-nojs-1280.png) / [390](after-profile-nojs-390.png);
[Brief no-JS1280](after-brief-nojs-1280.png) / [390](after-brief-nojs-390.png).
[Profile nav open390](after-profile-nav-open-390.png) /
[Brief nav open390](after-brief-nav-open-390.png).
[Closed finding evidence1280](after-finding-1280.png) / [390](after-finding-390.png).
[PDF head1280](after-pdf-head-1280.png) / [390](after-pdf-head-390.png);
[PDF findings1280](after-pdf-findings-1280.png) / [390](after-pdf-findings-390.png).
[PowerPoint head1280](after-pptx-head-1280.png) / [390](after-pptx-head-390.png);
[PowerPoint ranking1280](after-pptx-ranking-1280.png) / [390](after-pptx-ranking-390.png).

## Visual findings, fixes and limits

Compared parent/new views with the repository's earlier EDA/visual-review artifacts
(spec005/008) and the established practices of restrained emphasis, readable line
lengths, semantic hierarchy, progressive disclosure, visible keyboard focus and
native control semantics. This is a builder rubric, not a formal accessibility
certification or a new external benchmark; no external lookup was needed.

Fixed:flat inferred/measured prose; sentence-wide emphasis; duplicated visible
rule boilerplate; panel SHA dominating the phone head; fourth-level chart headings;
missing navigation; small fact collections styled as lists; export role/bullet
inconsistency; quoted-value false emphasis; fresh/loaded technical key ordering.
Actual desktop/phone heads and PDF/PPTX text were visually inspected after fixes.

Open:narrow fixed-page PDF and PowerPoint require zoom; broad tables require local
panning; the Brief still contains the existing volume of findings/conditional
measurements. No findings were removed/reordered and no boilerplate-reduction or
native-chart feature was added. Raw data/code/SVG labels remain literal rather than
acquiring inferred/verdict semantics from a matching word. No-script navigation is
expanded by design. Kate first; owner acceptance and independent review remain.

Reproduction:[build.py](build.py), [capture.py](capture.py),
[export_capture.py](export_capture.py); see ../quickstart.md. Review-only browser,
LibreOffice and PyMuPDF tools are not runtime dependencies.
