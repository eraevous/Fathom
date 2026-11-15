"""Spec 029: profile a pandas DataFrame from Python (notebooks), same artifacts as the CLI."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest

import fathom
from fathom import api
from fathom.api import dataframe_csv_bytes
from fathom.cli import main

ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "tests/fixtures"


def canonical_csv(tmp_path, source: Path) -> tuple[Path, pd.DataFrame]:
    """The fixture read as text, and a CSV file holding exactly the bytes the API serialises."""
    frame = pd.read_csv(source, dtype=str, keep_default_na=False)
    path = tmp_path / "data.csv"
    path.write_bytes(dataframe_csv_bytes(frame))
    return path, frame


def same_except_connector(api_text: str, cli_text: str) -> bool:
    """The only intended difference: the recorded connector ("dataframe" vs "csv").

    The CLI runs from tmp_path on the relative path "data.csv", and the API is given
    name="data.csv", so the origin is the same string in both.
    """
    assert "dataframe" not in cli_text
    return api_text.replace("dataframe", "csv") == cli_text


def run_cli(tmp_path, *args):
    here = os.getcwd()
    os.chdir(tmp_path)
    try:
        return main(list(args))
    finally:
        os.chdir(here)


@pytest.mark.parametrize("config", [None, FIXTURES / "review.yaml"])
def test_profile_matches_cli_bytes_except_source(tmp_path, config):
    path, frame = canonical_csv(tmp_path, FIXTURES / "review.csv")
    cli_out, api_out = tmp_path / "cli", tmp_path / "api"
    assert run_cli(tmp_path, "profile", "data.csv", "--out", str(cli_out), *(["--config", str(config)] if config else [])) == 0
    result = fathom.profile(frame, config=config, out=api_out, name="data.csv")
    for name in ("report.md", "report.html", "guide-profile.json"):
        cli_text = (cli_out / name).read_text(encoding="utf-8")
        api_text = (api_out / name).read_text(encoding="utf-8")
        assert api_text == result.files[name]
        assert same_except_connector(api_text, cli_text), name
    cli_doc = json.loads((cli_out / "guide-profile.json").read_text())
    assert result.document["source"] == {"connector": "dataframe", "origin": "data.csv", "sha256": cli_doc["source"]["sha256"]}


def test_dict_config_equals_yaml_file(tmp_path):
    import yaml
    _, frame = canonical_csv(tmp_path, FIXTURES / "review.csv")
    raw = yaml.safe_load((FIXTURES / "review.yaml").read_text())  # SafeLoader turns the ISO date into a date
    from_dict = fathom.profile(frame, config=raw)
    from_file = fathom.profile(frame, config=FIXTURES / "review.yaml")
    assert from_dict.to_json() == from_file.to_json()


def test_liftoff_matches_cli_bytes_except_source(tmp_path):
    path, frame = canonical_csv(tmp_path, FIXTURES / "review.csv")
    assert run_cli(tmp_path, "liftoff", "data.csv", "--out", str(tmp_path / "cli")) == 0
    result = api.liftoff(frame, out=tmp_path / "api", name="data.csv")
    for name in ("liftoff.html", "liftoff-profile.json"):
        assert same_except_connector(result.files[name], (tmp_path / "cli" / name).read_text(encoding="utf-8")), name


def test_content_hash_tracks_content_not_name(tmp_path):
    _, frame = canonical_csv(tmp_path, FIXTURES / "review.csv")
    a = fathom.profile(frame, name="a").document["source"]["sha256"]
    assert a == fathom.profile(frame, name="b").document["source"]["sha256"]
    changed = frame.copy()
    changed.iloc[0, 1] = "11"
    assert fathom.profile(changed).document["source"]["sha256"] != a


def test_typed_and_missing_values_are_profiled_as_their_text():
    frame = pd.DataFrame({"n": [1.5, None, 3.0], "s": ["x", pd.NA, " "], "t": pd.to_datetime(["2026-01-01", None, "2026-01-03"])})
    text = dataframe_csv_bytes(frame).decode()
    assert text == "n,s,t\n1.5,x,2026-01-01 00:00:00\n,,\n3.0, ,2026-01-03 00:00:00\n"
    doc = fathom.profile(frame).document
    assert {c["name"] for c in doc["columns"]} == {"n", "s", "t"}


def test_bad_inputs_raise_clear_errors():
    with pytest.raises(ValueError, match="pandas DataFrame"):
        fathom.profile([[1, 2]])
    with pytest.raises(ValueError, match="column names must be strings"):
        fathom.profile(pd.DataFrame({0: ["a"]}))
    with pytest.raises(ValueError, match="unique, nonblank"):
        fathom.profile(pd.DataFrame([["a", "b"]], columns=["x", "x"]))
    with pytest.raises(ValueError, match="config must be"):
        fathom.profile(pd.DataFrame({"x": ["a"]}), config=3)
    with pytest.raises(ValueError, match="name must be"):
        fathom.profile(pd.DataFrame({"x": ["a"]}), name=" ")


def test_inline_view_is_collapsed_and_self_contained(tmp_path):
    _, frame = canonical_csv(tmp_path, FIXTURES / "review.csv")
    result = fathom.profile(frame, config=FIXTURES / "review.yaml", out=tmp_path / "out")
    html = result.show()._repr_html_()
    assert html == result._repr_html_()
    assert "Key findings" in html and "Dataset summary" in html
    assert str(tmp_path / "out" / "report.html") in html
    lowered = html.lower()
    for forbidden in ("<script", "src=", "http://", "https://", "@import", 'href="#'):
        assert forbidden not in lowered, forbidden
    assert len(html) < len(result.files["report.html"]) / 2  # collapsed, not the full report
    unsaved = fathom.profile(frame)
    assert unsaved.out is None and "Pass out=" in unsaved._repr_html_()
    brief = api.liftoff(frame).show()._repr_html_()
    assert "<script" not in brief.lower() and "http" not in brief.lower()


def test_import_fathom_stays_light():
    code = "import sys, fathom; print('pandas' in sys.modules, 'fathom.api' in sys.modules, 'IPython' in sys.modules)"
    out = subprocess.run([sys.executable, "-c", code], env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
                         capture_output=True, text=True, check=True).stdout.split()
    assert out == ["False", "False", "False"]


def test_api_runs_with_all_sockets_blocked(tmp_path):
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "FATHOM_DENY_NETWORK": "1", "PYTHONHASHSEED": "19"}
    r = subprocess.run([sys.executable, str(ROOT / "tests/offline_runner.py"), "--api", str(FIXTURES / "review.csv"), str(tmp_path)],
                       env=env, capture_output=True)
    assert r.returncode == 0, r.stderr.decode()
    assert {p.name for p in tmp_path.iterdir()} >= {"report.html", "guide-profile.json", "liftoff.html"}
