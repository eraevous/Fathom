"""spec012: `guide configure` page, shared control schema, Python/JS YAML parity, escaping."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from fathom.config import load_config, validate_config
from fathom.configure import config_yaml, loader_knows, schema_from_page, yaml_digest, yaml_js_from_page

EVIL = '</script><img src=x onerror=alert(1)>'
QUOTED = 'say "hi"\nthere \'now\' é😀'


def run(*args, seed="1"):
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).parents[1] / "src"), "PYTHONHASHSEED": seed}
    return subprocess.run([sys.executable, "-m", "fathom", *map(str, args)], env=env, text=True, capture_output=True)


def unseen_csv(path: Path) -> Path:
    """Synthetic: `logged` holds DD/MM/YYYY dates plus two 'pending' cells, so it is not inferred temporal."""
    lines = ["trip,logged,fare,zone,started,ended"]
    for i in range(30):
        logged = "pending" if i in (4, 17) else f"{(i % 16) + 13:02d}/{(i % 12) + 1:02d}/2021"
        lines.append(f"t{i},{logged},{5 + (i * 7) % 23}.5,{'ABC'[i % 3]},2021-03-{i % 28 + 1:02d} 08:00,2021-03-{i % 28 + 1:02d} 08:{10 + i % 40:02d}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def page_for(tmp_path, csv_path, *extra):
    out = tmp_path / "configure"
    r = run("configure", csv_path, *extra, "--out", out)
    assert r.returncode == 0, r.stderr
    return out, (out / "configure.html").read_text(encoding="utf-8")


def roundtrip(tmp_path, schema, sel, columns):
    path = tmp_path / "generated.yaml"
    path.write_text(config_yaml(schema, sel), encoding="utf-8")
    return validate_config(load_config(path), columns)


def test_page_and_profile_are_deterministic(tmp_path):
    csv_path = unseen_csv(tmp_path / "unseen.csv")
    a, b = tmp_path / "a", tmp_path / "b"
    for out, seed in ((a, "1"), (b, "777")):
        assert run("configure", csv_path, "--out", out, seed=seed).returncode == 0
    for name in ("configure.html", "configure-profile.json"):
        assert (a / name).read_bytes() == (b / name).read_bytes()
    page = (a / "configure.html").read_text()
    assert "http://" not in page and "https://" not in page and "src=" not in page.split("<script")[0]
    assert json.loads((a / "configure-profile.json").read_text())["kind"] == "profile"


def test_schema_suggests_with_observable_reasons_and_nothing_preselected(tmp_path):
    _, page = page_for(tmp_path, unseen_csv(tmp_path / "unseen.csv"))
    schema = schema_from_page(page)
    logged = next(c for c in schema["columns"] if c["name"] == "logged")
    assert logged["effective_type"] != "temporal"
    assert {(s["key"], s["value"]) for s in logged["suggestions"]} == {("type", "temporal"), ("date_format", "DMY")}
    assert "28 of 30 nonmissing values (93.3%) parse as DMY" in logged["suggestions"][0]["reason"]
    fare = next(c for c in schema["target_candidates"] if c["column"] == "fare")
    assert fare["reason"].startswith("numeric; 100% populated;") and "relevan" not in json.dumps(schema["target_candidates"])
    assert {(i["start"], i["end"]) for i in schema["interval_suggestions"]} == {("started", "ended"), ("ended", "started")}
    # Suggestions are not selections: the untouched page emits an empty config.
    assert config_yaml(schema, schema["initial"]) == "{}\n"
    assert 'data-accept="col:1:type"> suggested' in page and "checked" not in page.split('data-interval="0"')[1][:20]
    assert all(r["source"].startswith("FT-") for r in schema["fixed_rules"])
    assert not any(e["key"] == "time_series" for e in schema["extension_points"])  # offered now (spec011 merged)


def test_python_generator_round_trips_through_config_loader(tmp_path):
    csv_path = unseen_csv(tmp_path / "unseen.csv")
    _, page = page_for(tmp_path, csv_path)
    schema = schema_from_page(page)
    names = [c["name"] for c in schema["columns"]]
    sel = {"question": "  Which zones have long trips?\n", "row_unit": "one trip", "target": "fare", "bins": 7,
           "pair_budget": 3, "sample_rows": 999, "sections": {"samples": False, "missingness_patterns": True},
           "intervals": [["started", "ended"]],
           "columns": {"logged": {"type": "temporal", "date_format": "DMY"}, "trip": {"exclude_from_target": True}, "zone": {"type": "bogus"}}}
    cfg = roundtrip(tmp_path, schema, sel, names)
    assert cfg["question"] == "Which zones have long trips?" and cfg["row_unit"] == "one trip" and cfg["target"] == "fare"
    assert cfg["bins"] == 7 and cfg["pair_budget"] == 3 and cfg["sample_rows"] == 20  # out-of-range knob not emitted
    assert cfg["sections"] == {"missingness_patterns": True, "samples": False}
    assert cfg["intervals"] == [{"start": "started", "end": "ended"}]
    assert cfg["columns"] == {"trip": {"exclude_from_target": True}, "logged": {"type": "temporal", "date_format": "DMY"}}
    assert "sha256" not in config_yaml(schema, sel) and "suggested" not in config_yaml(schema, sel)


def test_existing_config_prefills_and_passthrough_survives(tmp_path):
    csv_path = unseen_csv(tmp_path / "unseen.csv")
    existing = tmp_path / "existing.yaml"
    existing.write_text('title: Trips\ncolumns:\n  fare: {meaning: "Charged amount", units: USD, exclude_from_target: true}\nbins: 4\n'
                        'context: {source: synthetic}\nsections: {missingness_patterns: false}\n', encoding="utf-8")
    _, page = page_for(tmp_path, csv_path, "--config", existing)
    schema = schema_from_page(page)
    assert schema["initial"]["bins"] == 4 and schema["initial"]["columns"]["fare"] == {"exclude_from_target": True}
    cfg = roundtrip(tmp_path, schema, schema["initial"], [c["name"] for c in schema["columns"]])
    assert cfg["title"] == "Trips" and cfg["bins"] == 4 and cfg["context"]["source"] == "synthetic"
    assert cfg["columns"]["fare"] == {"exclude_from_target": True, "meaning": "Charged amount", "units": "USD"}
    assert cfg["sections"]["missingness_patterns"] is False


node = shutil.which("node")


@pytest.mark.skipif(node is None, reason="node not installed; Python generator is still tested")
def test_embedded_javascript_generator_matches_python(tmp_path):
    csv_path = tmp_path / "evil.csv"
    csv_path.write_text('"' + EVIL + '","' + QUOTED.replace('"', '""') + '",on,plain,__proto__,constructor,prototype\n'
                        + "".join(f"{i},v{i % 3},{i % 2},x{i},p{i % 2},c{i % 3},{i}\n" for i in range(12)), encoding="utf-8")
    _, page = page_for(tmp_path, csv_path)
    schema = schema_from_page(page)
    selections = [
        schema["initial"],
        {"question": "q: \"x\" \\ é", "target": EVIL, "bins": 12, "sections": {"samples": False},
         "columns": {QUOTED: {"type": "categorical"}, "on": {"exclude_from_target": True, "date_format": "ISO"}}},
        {"row_unit": "   ", "pair_budget": 0, "sample_rows": 100, "intervals": [[EVIL, "on"], ["on", "on"]], "columns": {"plain": {"type": "string"}}},
        {"target": "constructor", "columns": {"__proto__": {"type": "string", "exclude_from_target": True}, "prototype": {"type": "categorical"}}},
        {"time_series": [{"time": "on", "value": None, "by": EVIL, "granularities": ["month", "auto", "bogus"]},
                         {"time": QUOTED, "value": "__proto__", "by": "nope", "granularities": [], "max_lag": 7, "top_n": True},
                         {"time": "on", "value": "on"}, {"time": "constructor"}]},
    ]
    script = yaml_js_from_page(page) + "\nconst QUOTED_TEXT = " + json.dumps(QUOTED * 9) + ";\nconst [schema, sels] = JSON.parse(require('fs').readFileSync(0, 'utf8'));\nprocess.stdout.write(JSON.stringify(sels.map(s => [configYaml(schema, s), sha256Hex(configYaml(schema, s))]).concat([[QUOTED_TEXT, sha256Hex(QUOTED_TEXT)]])));"
    out = subprocess.run([node, "-e", script], input=json.dumps([schema, selections]), text=True, capture_output=True)
    assert out.returncode == 0, out.stderr
    assert json.loads(out.stdout) == [[config_yaml(schema, s), yaml_digest(config_yaml(schema, s))] for s in selections] + [[QUOTED * 9, yaml_digest(QUOTED * 9)]]
    names = [c["name"] for c in schema["columns"]]
    cfg = roundtrip(tmp_path, schema, selections[1], names)
    assert cfg["target"] == EVIL and cfg["columns"][QUOTED] == {"type": "categorical"} and cfg["columns"]["on"]["exclude_from_target"] is True
    cfg = roundtrip(tmp_path, schema, selections[3], names)
    assert cfg["target"] == "constructor" and "type" not in cfg
    assert cfg["columns"] == {"__proto__": {"type": "string", "exclude_from_target": True}, "prototype": {"type": "categorical"}}
    assert "plain" not in cfg["columns"]


def test_hostile_column_names_are_escaped(tmp_path):
    csv_path = tmp_path / "evil.csv"
    csv_path.write_text('"' + EVIL + '","' + QUOTED.replace('"', '""') + '",amount\n' + "".join(f"{i},w{i % 4},{i}\n" for i in range(10)), encoding="utf-8")
    _, page = page_for(tmp_path, csv_path)
    assert "<img" not in page and "onerror=alert(1)>" not in page
    assert page.count("</script>") == 3 and page.count("<script") == 3
    assert "&lt;/script&gt;&lt;img src=x onerror=alert(1)&gt;" in page
    schema = schema_from_page(page)
    assert [c["name"] for c in schema["columns"]][:2] == [EVIL, QUOTED]
    cfg = roundtrip(tmp_path, schema, {"target": "amount", "columns": {EVIL: {"exclude_from_target": True}, QUOTED: {"type": "string"}}}, [c["name"] for c in schema["columns"]])
    assert cfg["columns"] == {EVIL: {"exclude_from_target": True}, QUOTED: {"type": "string"}}


def test_kate_acceptance_unseen_csv_configure_then_profile(tmp_path):
    csv_path = unseen_csv(tmp_path / "unseen.csv")
    _, page = page_for(tmp_path, csv_path)
    schema = schema_from_page(page)
    logged = next(c for c in schema["columns"] if c["name"] == "logged")
    picks = {s["key"]: s["value"] for s in logged["suggestions"]}  # the user ticks both suggestions
    sel = {"target": "fare", "bins": 4, "sections": {"samples": False}, "columns": {"logged": picks}}
    cfg_path = tmp_path / "fathom.yaml"
    cfg_path.write_text(config_yaml(schema, sel), encoding="utf-8")
    report = tmp_path / "report"
    r = run("profile", csv_path, "--config", cfg_path, "--out", report)
    assert r.returncode == 0, r.stderr
    doc = json.loads((report / "guide-profile.json").read_text())
    col = next(c for c in doc["columns"] if c["name"] == "logged")
    assert col["effective_type"] == "temporal" and col["univariate"]["statistics"]["parse_formats"] == {"DMY": 28}
    assert col["univariate"]["statistics"]["earliest"] == "2021-01-13"
    fare = next(c for c in doc["columns"] if c["name"] == "fare")
    hist = next(ch for ch in fare["univariate"]["charts"] if ch["kind"] == "histogram")
    assert len(hist["data"]) == 4 and hist["bin_rule"].startswith("4 equal-width bins")
    assert doc["target_analysis"]["target"] == "fare"
    for name in ("report.html", "report.md"):
        text = (report / name).read_text()
        cannot = text.split("What the data cannot tell")[1][:2000]
        assert "Sample rows section omitted by configuration" in cannot and "sections.samples: false" in cannot.replace("\\", "")
        assert "Random rows" not in text and "Histogram bins: 4 equal-width bins" in text
    assert "<script" not in (report / "report.html").read_text()
    assert doc["samples"]["first"]  # omitted from the views only, still in the artifact


def test_bins_and_sections_validation_and_default_disclosure(make_profile):
    for bad in ({"bins": 0}, {"bins": 51}, {"bins": True}, {"sections": {"findings": False}}, {"sections": {"samples": "no"}}):
        with pytest.raises(ValueError):
            validate_config(bad)
    doc = make_profile("x\n" + "".join(f"{i}\n" for i in range(50))).document
    hist = next(ch for ch in doc["columns"][0]["univariate"]["charts"] if ch["kind"] == "histogram")
    assert len(hist["data"]) == 8 and hist["bin_rule"].startswith("sqrt(n)")
    assert doc["report"] == {"generator": "system default", "bins": None, "bin_rule": hist["bin_rule"], "omitted_sections": []}


def test_validate_echoes_bins_and_sections(tmp_path):
    cfg = tmp_path / "c.yaml"
    cfg.write_text("bins: 6\nsections: {samples: false}\n", encoding="utf-8")
    r = run("validate", unseen_csv(tmp_path / "u.csv"), "--config", cfg)
    resolved = json.loads(r.stdout)["resolved"]
    assert resolved["bins"] == 6 and resolved["sections"] == {"missingness_patterns": True, "samples": False}


def test_time_series_status_is_detected_not_assumed(tmp_path):
    """Kept name (FT-CFG-E1@3 cites it): loader keys are detected, and the page now names what it does not offer."""
    assert loader_knows("bins") and loader_knows("time_series") and loader_knows("intervals") and not loader_knows("no_such_key")
    out, page = page_for(tmp_path, unseen_csv(tmp_path / "u.csv"))
    points = {e["key"]: e["status"] for e in schema_from_page(page)["extension_points"]}
    assert points["time_series.max_lag, time_series.top_n"].startswith("Not offered") and "Not offered by this page" in page
    assert "not an audit certificate" in page and "yaml_sha256" in page


# --- time_series knob (spec011 merged from main) ---------------------------------------

def hourly_csv(path: Path, hours=48) -> Path:
    """Synthetic: 48 hourly event timestamps, a numeric amount, an integer id (identifier-like) and a zone."""
    lines = ["id,at,amount,zone,short"]
    for i in range(hours):
        lines.append(f"{i},2021-03-{1 + i // 24:02d} {i % 24:02d}:15:00,{(i * 7) % 11}.5,{'NS'[i % 2]},2021-03-0{1 + i % 3}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_time_series_suggestions_are_unticked_with_observable_reasons(tmp_path):
    _, page = page_for(tmp_path, hourly_csv(tmp_path / "h.csv"))
    schema = schema_from_page(page)
    got = [(o["time"], o["value"]) for o in schema["series_suggestions"]]
    assert got == [("at", None), ("at", "amount")]          # id is identifier-like; `short` has 3 days (< 30 periods)
    assert schema["series_suggestions"][0]["reason"].startswith("at is temporal with 48 distinct hours (at least 30")
    assert "zone" in schema["by_options"] and schema["ts_granularities"] == ["auto", "hour", "day", "week", "month"]
    assert config_yaml(schema, schema["initial"]) == "{}\n"  # nothing preselected
    assert 'data-series="0" data-key' in page and "checked" not in page.split('data-series="0"')[1][:20]


def test_time_series_decoy_without_enough_periods_offers_nothing(tmp_path):
    _, page = page_for(tmp_path, unseen_csv(tmp_path / "u.csv"))      # 28 distinct hours: below the rule
    assert schema_from_page(page)["series_suggestions"] == [] and "No temporal column with at least 30 distinct periods" in page


def test_time_series_round_trips_and_profiles(tmp_path):
    csv_path = hourly_csv(tmp_path / "h.csv")
    _, page = page_for(tmp_path, csv_path)
    schema = schema_from_page(page)
    names = [c["name"] for c in schema["columns"]]
    sel = {"time_series": [{"time": "at", "value": None, "by": None, "granularities": ["day", "hour"]},
                           {"time": "at", "value": "amount", "by": "zone", "granularities": []},
                           {"time": "at", "value": "at", "granularities": []},              # same column twice: dropped
                           {"time": "nope", "value": None}]}                                  # unknown column: dropped
    text = config_yaml(schema, sel)
    assert text == ('time_series:\n  - time: "at"\n    value: null\n    granularities:\n      - "hour"\n      - "day"\n'
                    '  - time: "at"\n    value: "amount"\n    by: "zone"\n')
    cfg = roundtrip(tmp_path, schema, sel, names)
    assert cfg["time_series"][0]["granularities"] == ["hour", "day"] and cfg["time_series"][1]["by"] == "zone"
    (tmp_path / "f.yaml").write_text(text, encoding="utf-8")
    r = run("profile", csv_path, "--config", tmp_path / "f.yaml", "--out", tmp_path / "rep")
    assert r.returncode == 0, r.stderr
    doc = json.loads((tmp_path / "rep" / "guide-profile.json").read_text())
    assert [s["time"] for s in doc["time_series"]["series"]] == ["at", "at"] and doc["time_series"]["series"][1]["by"] == "zone"


def test_existing_time_series_and_intervals_prefill_and_keep_passthrough(tmp_path):
    csv_path = hourly_csv(tmp_path / "h.csv")
    existing = tmp_path / "e.yaml"
    existing.write_text("time_series:\n  - {time: at, value: null, by: zone, granularities: [day], max_lag: 10, top_n: 2}\n"
                        "  - {time: short, value: null}\nintervals:\n  - {start: short, end: at}\n", encoding="utf-8")
    _, page = page_for(tmp_path, csv_path, "--config", existing)
    schema = schema_from_page(page)
    cfg = roundtrip(tmp_path, schema, schema["initial"], [c["name"] for c in schema["columns"]])
    assert cfg["time_series"] == [{"time": "at", "value": None, "by": "zone", "granularities": ["day"], "max_lag": 10, "top_n": 2},
                                  {"time": "short", "value": None, "by": None, "granularities": ["auto"], "max_lag": None}]
    assert cfg["intervals"] == [{"start": "short", "end": "at"}]
    assert "kept from --config: max_lag 10, top_n 2" in page and "declared in the existing configuration" in page
