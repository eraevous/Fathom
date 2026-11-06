# Report style

This is the shared presentation rule set for the Brief, profile, panel, Markdown,
and optional PDF/PowerPoint text. It renders the existing measured/inferred/declared
distinction; it does not establish a verdict, select an analysis or change a value.
Colors remain Fathom's spec008 palette. No remote assets, fonts or dependencies.

| Treatment | Meaning | Application |
| --- | --- | --- |
| **Bold** | Existing verdict token or deciding measured number | `marked`, `not marked`, `insufficient evidence`, `constant`, `strongly skewed`, `not estimable`; numeric gap/coefficient/zero in a verdict line. Never a sentence. |
| *Italic* | Inferred reading rather than a declared fact | Inferred identity/description, type/role readings, `(inferred)`, unknown meaning, hypothesis/interpretation prose. Declared descriptions stay plain. |
| Underline | A cross-reference | Native evidence, rule, dictionary and navigation links. Never an emphasis device. |
| `Monospace` | Literal text | Known column names, quoted example/category values, rule IDs and SHA prefixes. Literal data wins over a matching verdict word. |
| Bullets | Three or more parallel facts | Key findings, missing columns, exclusions/reasons. One or two facts remain paragraphs. |
| Numbers | Ordered steps | The two-stage flow or sequenced review instructions; never a ranking invented by the renderer. |

Headings use the existing hierarchy, at most h1/h2/h3. Chart titles are paragraph
labels, not extra heading levels. Heading and table-header weights express
structure; body `strong` expresses a verdict. **N=8 words** is the fixture guard
for a bold span, not a statistical threshold. A verdict is still readable as text
with all styling removed. The words and order remain those in the saved artifact.

Every finding leaves its verdict and inline gate visible; evidence, uncertainty,
generator and provenance stay together in a closed native disclosure. Repetitive
findings retain the existing summary/full switch. Full hashes and raw technical
objects stay behind disclosures. SVG labels/geometry, raw code/preformatted blocks,
configuration scripts, literal inputs and sample cells are not semantic prose;
text that happens to say `constant` or `(inferred)` is not thereby a new verdict
or an inferred assertion. Exact raw text remains available in the saved artifact.

The shared text-run classifier receives literal identifiers and explicit verdict
or inference context. Existing state tokens, numeric gate text and inferred labels
are emphasized; other numbers remain plain. Inferred identity and hypothesis or
interpretation context comes from the artifact, not a new semantic guess. Escaping
is retained. Optional serializers use the same roles: PDF bold/italic/Courier and
PowerPoint bold/italic/Courier New runs. Export navigation and disclosures have no
portable equivalent; retain existing summary/full policy and evidence pointers.

Brief and profile share a top navigation component. This preserves the full width
for plots and statistics instead of adding a sidebar. It lists only destinations
actually present and counts stored objects, independently of their disclosure
state. Counts mean headline items, dictionary columns, original findings, selected
relations, declared series (or Brief previews), ranked target candidates and
selection exclusions (or Brief limits), respectively. It never changes report order. A tiny local script reveals the toggle and
collapses the list initially at widths ≤600px. Native buttons/links support Tab,
Enter and Space with visible focus. If scripts are disabled or fail, the list
stays expanded and usable. Printing hides navigation. Narrow tables retain local
horizontal scrolling; the page itself should not overflow.

## Related quantities and summaries (spec020, proposed)

Two or more related quantities are an explicit exception to the minimum-three
bullet convention: the verdict stays in a parent line and each group/rest/gate
quantity gets a child bullet. Each prose line contains at most one comparison;
literal names/values are not comparison operators. Source-order facts and false
gates remain. HTML, Markdown and fixed exports share the same derived tree.

Per-type summary tables follow Key findings. Counts, missing shares and IQR use
stored values or disclosed display arithmetic; unavailable metrics stay explicit.
Tiny marks repeat stored values. Transpose changes only table orientation and is
hidden without scripts; fixed exports use the configured orientation and paginate.

Spec020 proposes replacing the earlier teal palette with the handoff's tool tokens;
that proposal supersedes the unchanged-palette sentence above for this slice only.
Low-contrast grid/soft-fill colors remain decorative; informative strokes/fills use
accent_faint and opaque markers. Every finding kind keeps its text label. Palette
acceptance remains Zach's; `fathom.palette` remains the single color source.

Summary text n and top-value share use stored nonmissing counts/frequencies; entropy and length retain the stored raw-lexeme basis including blanks, explicitly disclosed. Empty text columns show n=0 and no top-value share. PDF generated gate arrows are spelled out as "leads to" for the bundled font.
