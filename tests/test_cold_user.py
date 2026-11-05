"""Spec 009: cold-user fixes. Each check has a violating case and a clean decoy."""

import builtins
import json
from pathlib import Path

import pytest

from fathom.cli import main
from fathom.config import validate_config
from fathom.parsing import parse_date

ROWS = ["2019-03-01 08:00:00", "2019-03-02 09:15:30", "2019-03-03 10:30", "2019-03-04T11:45:00",
        "2019-03-05 12:00:00", "2019-03-06 13:00:00"]


def table(tmp_path, rows=ROWS, header="pickup,tip"):
    path = tmp_path / "trips.csv"
    path.write_text(header + "\n" + "\n".join(f"{v},{i % 3}.5" for i, v in enumerate(rows)) + "\n", encoding="utf-8")
    return path


def config(tmp_path, text):
    path = tmp_path / "trips.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_iso_datetime_parses_to_calendar_date():
    assert parse_date("2019-03-23 20:21:09") == {"date": "2019-03-23", "format": "ISO_DATETIME", "two_digit_year": False, "alternatives": []}
    assert parse_date("2019-03-23T20:21")["format"] == "ISO_DATETIME"
    assert parse_date("2019-03-23")["format"] == "ISO"  # decoy: plain ISO date keeps its format
    for bad in ("2019-03-23 24:00:00", "2019-03-23 20:60", "2019-02-30 10:00:00", "20:21:09", "2019-03-23 20:21:09+05:00", "2019-03-23 8:21"):
        assert parse_date(bad) is None, bad
    assert parse_date("2019-03-23 20:21:09", "ISO") is None  # an explicit ISO hint stays date-only
    assert parse_date("2019-03-23", "ISO_DATETIME") is None


def run(argv, capsys):
    code = main([str(a) for a in argv])
    out = capsys.readouterr()
    return code, out.out, out.err


def test_datetime_column_gets_date_profile_not_identifier_exclusion(tmp_path, capsys):
    cfg = config(tmp_path, "target: tip\nrow_unit: one trip\n")
    code, out, err = run(["profile", table(tmp_path), "--config", cfg, "--out", tmp_path / "out"], capsys)
    assert code == 0, err
    d = json.loads((tmp_path / "out" / "guide-profile.json").read_text())
    col = d["columns"][0]
    assert col["effective_type"] == "temporal"
    stats = col["univariate"]["statistics"]
    assert (stats["earliest"], stats["latest"], stats["span_days"]) == ("2019-03-01", "2019-03-06", 5)
    assert stats["parse_formats"] == {"ISO_DATETIME": 6} and "time of day is not analysed" in stats["parse_basis"]
    md = (tmp_path / "out" / "report.md").read_text()
    html = (tmp_path / "out" / "report.html").read_text()
    note = "analysed by calendar date only; time of day excluded"
    assert md.count(note) == 2 and html.count(note) == 2  # column line + "What the data cannot tell"
    assert "Date-time columns \\(pickup\\) are " + note in md
    reason = {e["column"]: e["reason"] for e in d["target_analysis"]["excluded"]}["pickup"]
    assert "identifier" not in reason and "temporal" in reason


def test_text_decoy_stays_string(tmp_path, capsys):
    rows = [f"trip {i:02d} at 20:21" for i in range(6)]
    code, _, err = run(["profile", table(tmp_path, rows), "--out", tmp_path / "out"], capsys)
    assert code == 0, err
    d = json.loads((tmp_path / "out" / "guide-profile.json").read_text())
    assert d["columns"][0]["effective_type"] == "string"
    assert "time of day excluded" not in (tmp_path / "out" / "report.md").read_text()  # decoy


def test_date_format_override_counts_invalid(tmp_path, capsys):
    rows = ROWS[:5] + ["2019-02-30 10:00:00"]
    cfg = config(tmp_path, "columns:\n  pickup:\n    date_format: ISO_DATETIME\n")
    code, _, err = run(["profile", table(tmp_path, rows), "--config", cfg, "--out", tmp_path / "out"], capsys)
    assert code == 0, err
    stats = json.loads((tmp_path / "out" / "guide-profile.json").read_text())["columns"][0]["univariate"]["statistics"]
    assert stats["invalid"] == 1 and stats["invalid_examples"] == ["2019-02-30 10:00:00"]
    assert stats["parse_basis"].startswith("human format override")
    code, out, _ = run(["validate", table(tmp_path, rows), "--config", cfg], capsys)
    assert json.loads(out)["resolved"]["column_override_values"] == {"pickup": {"date_format": "ISO_DATETIME"}}


def test_override_errors_name_accepted_values():
    with pytest.raises(ValueError, match=r"temporal \(dates are temporal\)|dates are temporal"):
        validate_config({"columns": {"x": {"type": "date"}}}, ["x"])
    with pytest.raises(ValueError, match="ISO_DATETIME.*not strftime"):
        validate_config({"columns": {"x": {"date_format": "%Y-%m-%d %H:%M:%S"}}}, ["x"])
    assert validate_config({"columns": {"x": {"type": "temporal", "date_format": "ISO_DATETIME"}}}, ["x"])  # decoy


def test_declared_row_unit_is_not_called_unknown(tmp_path, capsys):
    for text, expected, absent in (("row_unit: one trip\n", "row unit declared", "row unit are unknown"),
                                   ("question: what?\n", "row unit are unknown", "row unit declared")):
        out = tmp_path / ("a" if "row_unit" in text else "b")
        code, _, err = run(["profile", table(tmp_path), "--config", config(tmp_path, text), "--out", out], capsys)
        assert code == 0, err
        report = (out / "report.md").read_text()
        assert expected in report and absent not in report


def test_profile_and_validate_echo_resolved_settings(tmp_path, capsys):
    cfg = config(tmp_path, "question: What drives tip?\ntarget: tip\nrow_unit: one trip\n")
    code, out, err = run(["profile", table(tmp_path), "--config", cfg, "--out", tmp_path / "out"], capsys)
    assert code == 0
    lines = out.splitlines()
    assert len(lines) == 1 and "guide-profile.json" in lines[0] and "report.html" in lines[0]
    assert err.strip() == "guide: question: What drives tip?; target: tip; excluded from target by config: none; unsupported type: pickup (unsupported type pair: temporal × numeric); budget: none; other eligibility: none; row unit: one trip"
    _, quiet, quiet_err = run(["profile", table(tmp_path), "--out", tmp_path / "none"], capsys)
    assert quiet_err.strip() == "guide: question: none declared; target: not declared; row unit: unknown (not declared)"
    code2, out2, _ = run(["profile", table(tmp_path), "--config", cfg, "--out", tmp_path / "out"], capsys)
    assert out2 == out  # deterministic, no timestamp
    code, out, _ = run(["validate", table(tmp_path), "--config", cfg], capsys)
    resolved = json.loads(out)
    assert code == 0 and resolved["mode"] == "wide"
    assert {k: resolved["resolved"][k] for k in ("question", "target", "row_unit", "rows")} == {
        "question": "What drives tip?", "target": "tip", "row_unit": "one trip", "rows": 6}


def test_export_without_extras_names_missing_extra(tmp_path, capsys, monkeypatch):
    cfg = config(tmp_path, "target: tip\n")
    assert run(["profile", table(tmp_path), "--config", cfg, "--out", tmp_path / "p"], capsys)[0] == 0
    real = builtins.__import__

    def no_extras(name, *args, **kwargs):
        if name.startswith(("reportlab", "pptx")):
            raise ImportError("synthetic absent extra")
        return real(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_extras)
    code, out, err = run(["export", tmp_path / "p" / "guide-profile.json", "--out", tmp_path / "e"], capsys)
    assert code == 0  # FT-R13 / spec004 FR-005: degraded, not failed
    assert err.count("pip install -e '.[exports]'") == 2 and "pdf not written" in err and "pptx not written" in err
    assert not (tmp_path / "e" / "report.pdf").exists()
    monkeypatch.setattr(builtins, "__import__", real)
    import fathom.exports
    monkeypatch.setattr(fathom.exports, "export_bundle", lambda result, formats, deck: (
        {"report.pdf": b"%PDF"}, {"artifact_sha256": "x", "formats": {"pdf": {"status": "written"}}}))
    code, out, err = run(["export", tmp_path / "p" / "guide-profile.json", "--out", tmp_path / "w", "--formats", "pdf"], capsys)
    assert code == 0 and err == ""  # decoy: a written format produces no notice
