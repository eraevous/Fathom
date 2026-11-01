import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

F = Path(__file__).parent / "fixtures"


def run(*args, seed="1"):
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).parents[1] / "src"), "PYTHONHASHSEED": seed}
    return subprocess.run([sys.executable, "-m", "fathom", *map(str, args)], env=env, text=True, capture_output=True)


def test_cli_roundtrip_compare_validate_and_reproducibility(tmp_path):
    before, after, rendered, second = [tmp_path / s for s in ("before", "after", "rendered", "second")]
    for path, seed in ((before, "1"), (second, "987")):
        r = run("profile", F / "review.csv", "--config", F / "review.yaml", "--out", path, seed=seed)
        assert r.returncode == 0, r.stderr
    for name in ("guide-profile.json", "report.md", "report.html"):
        assert (before / name).read_bytes() == (second / name).read_bytes()
    assert run("render", before / "guide-profile.json", "--out", rendered).returncode == 0
    for name in ("report.md", "report.html"):
        assert (before / name).read_bytes() == (rendered / name).read_bytes()
    assert run("profile", F / "revised.csv", "--config", F / "revised.yaml", "--out", after).returncode == 0
    comp = tmp_path / "compare"
    r = run("compare", before / "guide-profile.json", after / "guide-profile.json", "--out", comp)
    assert r.returncode == 0, r.stderr
    doc = json.loads((comp / "guide-comparison.json").read_text())
    assert doc["deltas"]["rows"] == -2
    assert doc["deltas"]["duplicate_rows"] == -1
    r = run("validate", F / "review.csv", "--config", F / "review.yaml")
    assert r.returncode == 0 and json.loads(r.stdout)["mode"] == "wide"
    assert run("--version").stdout.strip() == "guide 0.1.0"


@pytest.mark.parametrize("command", ["profile", "render", "compare"])
def test_cli_errors_before_writing(command, tmp_path):
    out = tmp_path / "absent"
    args = [command, tmp_path / "missing"]
    if command == "compare":
        args.append(tmp_path / "also-missing")
    r = run(*args, "--out", out)
    assert r.returncode == 2
    assert "Traceback" not in r.stderr and "guide:" in r.stderr
    assert not out.exists()


def test_cli_unsafe_yaml_and_unknown_target(tmp_path):
    for config in ("!!python/object/apply:os.system ['echo bad']", "target: nonexistent"):
        p = tmp_path / "bad.yaml"; p.write_text(config)
        out = tmp_path / "out"
        r = run("profile", F / "clean.csv", "--config", p, "--out", out)
        assert r.returncode == 2 and not out.exists()
        assert "Traceback" not in r.stderr


def test_cli_unknown_artifact_version(tmp_path):
    p = tmp_path / "bad.json"; p.write_text('{"schema_version":99,"kind":"profile"}')
    r = run("render", p, "--out", tmp_path / "out")
    assert r.returncode == 2 and "schema_version" in r.stderr
