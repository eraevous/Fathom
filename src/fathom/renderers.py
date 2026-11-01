"""Offline views derived entirely from a saved ProfilingResult."""

from html import escape
import re

from .models import ProfilingResult, canonical_json


def md_text(value: object) -> str:
    s = escape(str(value), quote=False)
    return re.sub(r"([\\`*_{}\[\]()#+.!|>-])", r"\\\1", s).replace("\n", " ")


def sections(result: ProfilingResult) -> list[tuple[str, object]]:
    d = result.document
    if d["kind"] == "comparison":
        return [("Contexts", d["contexts"]), ("Context differences", d["context_differences"]),
                ("Measured deltas", d["deltas"]), ("Limitations", d["limitations"])]
    return [("Source and context", {"source": d["source"], "context": d["context"]}),
            ("Purpose", d["purpose"]), ("Overview", d["overview"]),
            ("Working record (human declarations)", d["working_record"]),
            ("Selection and exclusions", d["selection"]), ("Requested relationships", d["bivariate"]),
            ("Dependencies", d["dependencies"])]


def render_markdown(result: ProfilingResult) -> str:
    d = result.document
    lines = ["# Fathom — " + d["kind"], "", "Evidence for review; human decisions remain human.", ""]
    for title, value in sections(result):
        lines.extend(["## " + title, ""])
        # An indented block keeps arbitrary text inert without a closable fence.
        lines.extend("    " + escape(line, quote=False) for line in canonical_json(value).rstrip().splitlines())
        lines.append("")
    if d["kind"] == "profile":
        lines += ["## Dictionary", ""]
        for c in d["columns"]:
            lines += ["### " + md_text(c["name"]), "", f"Effective type: {c['effective_type']}; inferred reading retained.", ""]
            lines.extend("    " + escape(line, quote=False) for line in canonical_json(c).rstrip().splitlines())
            lines.append("")
        lines += ["## Findings", ""]
        for f in d["findings"]:
            lines += [f"### {md_text(f['id'])} — {f['kind']}", "", md_text(f["message"]), "",
                      "Generator: " + md_text(f["generator"]), "", "Uncertainty: " + md_text(f["uncertainty"]), ""]
            lines.extend("    " + escape(line, quote=False) for line in canonical_json({"evidence": f["evidence"], "provenance": f["provenance"]}).rstrip().splitlines())
            lines.append("")
    if d.get("annotations"):
        lines += ["## Labelled annotations", ""]
        lines.extend("    " + escape(line, quote=False) for line in canonical_json(d["annotations"]).rstrip().splitlines())
    return "\n".join(lines).rstrip() + "\n"


def json_block(value: object) -> str:
    return "<pre>" + escape(canonical_json(value)) + "</pre>"


def bars(items: list[tuple[str, int]], title: str) -> str:
    """Embedded SVG: bounded visual evidence, with the same values in text."""
    if not items:
        return ""
    maximum = max((v for _, v in items), default=0) or 1
    out = [f'<svg role="img" aria-label="{escape(title, quote=True)}" viewBox="0 0 640 {len(items) * 30 + 12}"><title>{escape(title)}</title>']
    for i, (label, value) in enumerate(items):
        y = 10 + i * 30
        out += [f'<text x="0" y="{y + 14}">{escape(label[:28])}</text>',
                f'<rect x="230" y="{y}" width="{round(value / maximum * 330, 3)}" height="20" fill="#247a83"/>',
                f'<text x="575" y="{y + 14}">{value}</text>']
    return "".join(out) + "</svg>"


def render_html(result: ProfilingResult) -> str:
    d = result.document
    body = ['<h1>Fathom</h1><p class="lede">Evidence for review. Human decisions remain human.</p>',
            '<p>Artifact schema 1 · ' + escape(d["kind"]) + '</p>']
    for title, value in sections(result):
        body += ["<section><h2>" + escape(title) + "</h2>", json_block(value), "</section>"]
    if d["kind"] == "profile":
        body += ['<section><h2>Dictionary</h2>', '<p>Inferred readings are lexical, uncalibrated interpretations. Human overrides retain the original inference.</p>',
                 bars([(c["name"], c["missing"]) for c in d["columns"][:20]], "Missing cells by column (first 20)"),
                 '<table><thead><tr><th>Column</th><th>Effective type</th><th>Basis</th><th>Missing</th><th>Distinct</th></tr></thead><tbody>']
        for i, c in enumerate(d["columns"]):
            basis = "human override" if c["override"] else "inferred"
            body += [f'<tr><td><a href="#c-{i}">{escape(c["name"])}</a></td><td>{c["effective_type"]}</td><td>{basis}</td><td>{c["missing"]}/{c["count"]}</td><td>{c["distinct"]}</td></tr>']
        body += ['</tbody></table>']
        for i, c in enumerate(d["columns"]):
            body += [f'<article id="c-{i}"><h3>{escape(c["name"])}</h3>',
                     '<p>Meaning: ' + (escape(c["meaning"]["value"]) + ' (human)' if c["meaning"] else 'unknown — ask the data owner') + '</p>',
                     f'<p>Observed storage: {escape(c["observed_type"])}; effective: {c["effective_type"]}; inferred: {escape(c["inference"]["type"])}.</p>',
                     json_block({"inference": c["inference"], "override": c["override"], "statistics": c["statistics"], "examples": c["examples"]}),
                     bars([(v["value"], v["count"]) for v in c["frequencies"]], "Top value counts"),
                     json_block({"frequencies_top_10": c["frequencies"]}), '</article>']
        body += ['</section><section><h2>Findings</h2><p>Actions are conditional review suggestions; observations do not establish domain causes.</p>']
        for kind in ("action", "question", "observation", "interpretation", "hypothesis"):
            found = [f for f in d["findings"] if f["kind"] == kind]
            if not found:
                continue
            body += ['<h3>' + kind.title() + 's</h3>']
            for f in found:
                body += [f'<article id="{escape(f["id"], quote=True)}"><h4>{escape(f["message"])}</h4>',
                         '<p>Generator: ' + escape(f["generator"]) + '</p>',
                         '<p>Uncertainty: ' + escape(f["uncertainty"]) + '</p>']
                for evidence in f["evidence"]:
                    if "finding" in evidence:
                        target = escape(evidence["finding"], quote=True)
                        body += [f'<p>Evidence: <a href="#{target}">{target}</a></p>']
                body += [json_block({"evidence": f["evidence"], "provenance": f["provenance"]}), '</article>']
        body += ['</section>']
    if d.get("annotations"):
        body += ['<section><h2>Labelled annotations</h2>', json_block(d["annotations"]), '</section>']
    css = """body{font:16px/1.55 system-ui,sans-serif;color:#18383c;background:#f7faf8;margin:0 auto;max-width:1100px;padding:32px}h1{font-size:48px;margin-bottom:0}h2{border-bottom:2px solid #247a83;padding-bottom:8px}.lede{font-size:21px}section{margin:32px 0}article{background:white;border:1px solid #d2e0dc;border-radius:8px;padding:20px;margin:16px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.5 ui-monospace,monospace;background:#edf3f0;padding:14px;border-radius:4px}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:10px;border-bottom:1px solid #d2e0dc}a{color:#096772}svg{display:block;width:100%;max-width:760px}svg text{font:13px system-ui,sans-serif}@media print{body{padding:0}article{break-inside:avoid}}"""
    return '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fathom — ' + escape(d["kind"]) + '</title><style>' + css + '</style></head><body>' + "\n".join(body) + '</body></html>\n'
