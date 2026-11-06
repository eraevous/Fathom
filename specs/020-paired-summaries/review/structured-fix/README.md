# PR34 structured-findings correction

Review input: public Vega movies fixture already committed at `tests/fixtures/polish/movies.csv`; source URL/hash and null/header normalization in its `sources.json`. Config: `tests/fixtures/target/movies.yaml`, target Worldwide Gross. No network lookup or private fixture.

The independent review was correct: headline selection dropped structured evidence, concatenated two relationships and then nested punctuation fragments. The Adventure group mean ended up beside the rest label. This is fixed by passing the actual source finding through and rendering only typed fields; there is no prose-splitting fallback, including raw evidence/rule strings.

## Corrected values and behavior

- US Gross × Worldwide Gross: selected, inferred; Pearson r0.940 (stored0.9397421939), complete3194.
- US DVD Sales × Worldwide Gross: separate selected parent, inferred; Pearson r0.702 (stored0.7022713573), complete564.
- Adventure: group274rows/274valid, mean241171386; rest2652rows/2651valid, mean76434662. The valid/total distinction comes directly from saved fields. Rounded mean gap164736723 >= overall SD154722206 is marked; failed missing-share gate remains explicit.
- One relationship per headline consumes its own slot under the existing five-item cap and ranked order. Underlying selection, findings/order, measurements and JSON are untouched. Later presentation slots can fall beyond the cap.
- Unstructured/legacy findings remain intact single lines. No comma/semicolon/full-stop parsing. Coefficients have three displayed decimals in structured findings; saved precision remains unchanged. One structured tree feeds HTML, Markdown and fixed-export topics.

## Regression evidence

`tests/test_structured_findings.py` has five checks. Against old head53e64d6: **4failed, 1passed** ([before output](before-tests.txt)); the clean group/rest role decoy passes before and after. Exact public-film regression checks independently parsed headline parents/children, Adventure role values/counts, separate relationships, three decimals and no full stop followed by further child text. A swapped-value/stale-prose decoy proves roles follow structured fields; unstructured/literal and raw-evidence controls reject splitting. Export-topic controls verify the same facts for all formats.

Final full suite with test/stats/export extras after ledger appends: **446passed, 2skipped**, one dependency warning ([output](tests.txt)). AEC pinned b0e202fa4b20: **0errors, 100inherited warnings** ([check](aec-check.txt)); regenerated6830edges; [code impact vs old PR head](code-impact.txt). Structural checks do not establish acceptance.

[Identity checks](identity.json): public-film profile JSON unchanged byte for byte (SHA256a420b0b388c7c293df083b380863fa9bf5bf4b0633bc1cdb1ddd72c696c44971); HTML/Markdown identical on rerun. Authored mixed fixture's nine JSON/HTML/Markdown/PDF/full-PPTX/CSV outputs also byte-identical, with actual optional exporters required written. The full suite's offline all-command/export harness passes.

## Visual review

Actual offline Chromium,1280x900 viewport, both light and dark. Eight full-viewport screenshots cover the two requested findings. [Browser checks](browser-checks.json): zero requests, no document overflow. Reviewed the real images: distinct relationship parents, complete labelled values, no fragments or group/rest misattribution, source gates readable. Palette, summaries and transpose unchanged. Existing fixed-page phone zoom limitation remains.

| Finding/theme | Before53e64d6 | After |
| --- | --- | --- |
| Relationships/light | [image](before-relationships-light-1280.png) | [image](after-relationships-light-1280.png) |
| Adventure/light | [image](before-adventure-light-1280.png) | [image](after-adventure-light-1280.png) |
| Relationships/dark | [image](before-relationships-dark-1280.png) | [image](after-relationships-dark-1280.png) |
| Adventure/dark | [image](before-adventure-dark-1280.png) | [image](after-adventure-dark-1280.png) |

Reproduce: capture old head's HTML at `/tmp/fix34-before/report.html` with the stated fixture/config; then run `PYTHONPATH=src python specs/020-paired-summaries/review/structured-fix/build.py` and `python specs/020-paired-summaries/review/structured-fix/capture.py`. Browser contexts explicitly offline. No new dependency. Updated provisional requirement/claim/evidence:FT-VIEW20-R1@2,FT-VIEW20-C1@2,FT-VIEW20-E1@2; append-only, current relation convention. Kate first, Zach merges, CLA unticked.
