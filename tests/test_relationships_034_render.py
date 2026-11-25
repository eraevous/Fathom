"""Spec 034 slice 1b (A1): declared sets in HTML, Markdown and the tidy CSV. FT-REL34-R1/R3/R5."""
import csv
import io
import re

from fathom.connectors import CSVConnector
from fathom.profiler import profile
from fathom.renderers import render_html, render_markdown
from fathom.tidy import tidy_files

BANNED = re.compile(r"\b(significant|significance|causes?|drives?|important)\b", re.I)
HEADER = ["set", "row_kind", "left", "right", "type_pair", "semantics", "n", "excluded_rows", "reason",
          "measure.cramers_v_corrected", "measure.eta", "measure.pearson_r", "measure.spearman_rho"]


def data(tmp_path):
    path = tmp_path / "t.csv"
    rows = [["x", "y", "g", "k", "sparse", "w"]]
    for i in range(40):  # y and w never overlap, so y x w has no complete cases (an undefined pair)
        rows.append([str(i), str((i * 7) % 11 + i // 4) if i % 5 else "", "abc"[i % 3], "1",
                     str(i) if i < 2 else "", str(i * i % 13) if i % 5 == 0 else ""])
    path.write_text("\n".join(",".join(r) for r in rows) + "\n")
    return CSVConnector(path).load()


CFG = {"relationships": {"sets": [{"name": "core", "columns": ["x", "y", "g", "k", "sparse", "w"]}]}}


def section(text, start, end):
    i = text.index(start)
    return text[i:text.index(end, i)]


def test_no_set_adds_nothing_to_reports_or_csv(tmp_path):
    result = profile(data(tmp_path))
    assert "relationship-sets" not in render_html(result)
    assert "relationship-sets" not in render_markdown(result)
    assert "relationships.csv" not in tidy_files(result.document)


def test_each_measured_pair_and_skip_is_a_row_in_html_and_markdown(tmp_path):
    result = profile(data(tmp_path), CFG)
    item = result.document["relationships"]["sets"][0]
    md = section(render_markdown(result), "### Declared relationship sets", "<details id=\"report-exclusions\"")
    html = section(render_html(result), '<div id="report-relationship-sets"', '<details id="report-exclusions"')
    for p in item["pairs"]:
        assert f"| {p['left']} | {p['right']} | {p['type_pair']} |" in md
        assert f"<td><code>{p['left']}</code></td><td><code>{p['right']}</code></td>" in html  # column names render as code
    for s in item["skipped"]:
        assert f"| {s['column']} | {s['reason']} |" in md and f"<td>{s['reason']}</td>" in html
    assert md.count("\n| ") == len(item["pairs"]) + len(item["skipped"]) + 2 * (1 + bool(item["skipped"]))
    assert 'href="#report-relationship-sets"' in render_html(result)


def test_undefined_pair_names_its_reason_instead_of_a_value(tmp_path):
    result = profile(data(tmp_path), CFG)
    pairs = {(p["left"], p["right"]): p for p in result.document["relationships"]["sets"][0]["pairs"]}
    assert pairs["y", "w"]["measures"] is None
    md, html = render_markdown(result), render_html(result)
    reason = "undefined: " + pairs["y", "w"]["undefined"]
    assert f"| y | w | numeric×numeric | {reason} |" in md and f"<td>{reason}</td>" in html
    rows = list(csv.DictReader(io.StringIO(tidy_files(result.document)["relationships.csv"])))
    row = next(r for r in rows if (r["left"], r["right"]) == ("y", "w"))
    assert row["reason"] == pairs["y", "w"]["undefined"] and row["measure.pearson_r"] == ""


def test_csv_rows_reconcile_and_header_is_fixed(tmp_path):
    result = profile(data(tmp_path), CFG)
    item = result.document["relationships"]["sets"][0]
    text = tidy_files(result.document)["relationships.csv"]
    rows = list(csv.DictReader(io.StringIO(text)))
    assert text.splitlines()[0].split(",") == HEADER
    pairs = [r for r in rows if r["row_kind"] == "pair"]
    skips = [r for r in rows if r["row_kind"] == "skipped_column"]
    assert len(pairs) == item["pairs_computed"] and len(skips) == len(item["skipped"])
    assert all(int(r["n"]) + int(r["excluded_rows"]) == 40 for r in pairs)
    assert {r["left"]: r["reason"] for r in skips} == {s["column"]: s["reason"] for s in item["skipped"]}
    stored = {(p["left"], p["right"]): p["measures"] for p in item["pairs"]}
    for r in pairs:
        for key, value in (stored[r["left"], r["right"]] or {}).items():
            assert float(r["measure." + key]) == value


def test_r5_no_banned_wording_in_rendered_section_or_csv(tmp_path):
    result = profile(data(tmp_path), CFG)
    md = section(render_markdown(result), "### Declared relationship sets", "<details id=\"report-exclusions\"")
    html = section(render_html(result), '<div id="report-relationship-sets"', '<details id="report-exclusions"')
    assert not BANNED.search(md) and not BANNED.search(html)
    assert not BANNED.search(tidy_files(result.document)["relationships.csv"])
    assert "not causation" in md
