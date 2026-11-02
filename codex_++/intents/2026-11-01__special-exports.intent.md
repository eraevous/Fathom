# Intent: special types and exports (HO-20261102-001)

1. Recognize phone/email/URL by explicit column-name cues or >=80% valid lexical
   values (>=3). Latitude/longitude use explicit names or overrides, never a guess
   from arbitrary numbers. Human overrides win and original inference remains.
2. Phone policy: optional leading plus, common punctuation, 7..15 digits, no extension
   grammar; repeated identical digits are placeholder candidates. No allocation,
   reachability, ownership, PHI/PII classification or network check.
3. Email policy: practical unquoted ASCII local part and dotted hostname; reject
   leading/trailing/repeated local dots. Count domains case-insensitively. Test/dummy/
   sample local labels and test.com are candidates, never confirmed fake accounts.
4. URLs: local HTTP(S) structure, host and port policy only; IPv4/IPv6 allowed.
   No DNS, requests, redirect, deliverability or content lookup. Other schemes and
   internationalized/quoted-email edge syntax are limitations, not universal invalidity.
5. Latitude/longitude are independent degree-range checks ±90/±180; no coordinate
   pairing, geocoding, coordinate-system conversion or spatial/bivariate analysis.
6. Export CLI also writes core HTML/Markdown and status JSON; each optional binary
   is independently available/unavailable. Source CSV is not needed or reopened.
7. PDF uses ReportLab's bundled Vera font (no OS/font/network dependency), replaces
   unsupported glyphs explicitly, summarizes repeated findings, includes all three
   sample windows, dictionary, provenance, summary, findings and relations. Very
   wide samples paginate columns in batches; no table values are invented.
8. PowerPoint uses python-pptx native charts/shapes, one summary/findings/chart topic
   per slide. Full dictionary/sample detail stays in HTML/Markdown/PDF; key findings
   may span multiple slides, with no hidden truncation. Box view uses native shapes.
9. PDF metadata and PPTX core/ZIP/nested-workbook timestamps are fixed; dependency
   versions affect bytes and are recorded. Exports do not change the profile artifact.
10. No new analysis or quality score. Builders use synthetic/clean/late tables and
    disclose misses. The export extra introduces serializers, not an analysis,
    rendering-service or narrative subsystem. PR004 depends on PR003; both target main.
