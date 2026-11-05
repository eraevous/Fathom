"""Spec 008 (DEC-043): significant-figure storage, missingness-by-group test, palette and dark mode.

Every behaviour has a violating fixture and a clean decoy (DG-RF)."""

import copy
import json
import math
from pathlib import Path
import random
import re
import subprocess
import sys

import pytest

from fathom.connectors import CSVConnector
from fathom.models import ProfilingResult
from fathom.profiler import profile
from fathom.renderers import render_html, render_markdown

S = Path(__file__).parent / "fixtures" / "salvage"
SRC = Path(__file__).parents[1] / "src" / "fathom"


def run(name, config=None):
    return profile(CSVConnector(S / name).load(), config).document


def column(d, name):
    return next(c for c in d["columns"] if c["name"] == name)


# --- US1: significant-figure storage -------------------------------------------------

def exact_values(name):
    return [float(line) for line in (S / name).read_text().splitlines()[1:]]


def test_tiny_scale_statistics_survive_storage():
    """Violating fixture: on main every percentile of this sd~1e-12 column is stored as 0.0."""
    d = run("tiny.csv"); c = column(d, "signal"); nums = sorted(exact_values("tiny.csv"))
    pct = c["univariate"]["statistics"]["percentiles"]
    assert all(v != 0 for v in pct.values())
    position = (len(nums) - 1) * .5
    assert math.isclose(pct["50"], (nums[int(position)] + nums[int(position) + 1]) / 2, rel_tol=5e-6)
    import statistics
    s = c["statistics"]
    for key, exact in (("min", nums[0]), ("max", nums[-1]), ("mean", statistics.mean(nums)),
                       ("median", statistics.median(nums)), ("population_std", statistics.pstdev(nums))):
        assert s[key] != 0 and math.isclose(s[key], exact, rel_tol=5e-6), key
    assert 5e-13 < s["population_std"] < 2e-12
    # Geometry keeps the shape: distinct, ordered histogram edges and a non-degenerate box.
    hist = next(ch for ch in c["univariate"]["charts"] if ch["kind"] == "histogram")
    edges = [b["low"] for b in hist["data"]] + [hist["data"][-1]["high"]]
    assert edges == sorted(edges) and len(set(edges)) == len(edges)
    box = next(ch for ch in c["univariate"]["charts"] if ch["kind"] == "box")["box"]
    assert box["min"] < box["q1"] < box["median"] < box["q3"] < box["max"]
    html = render_html(ProfilingResult(d))
    assert "e-12" in html or "e-13" in html


def test_stored_rule_is_six_figures_with_ten_decimal_floor():
    from fathom.univariate import stored, geometry, percentile, safe
    assert safe is stored or safe(1.2345678e-12) == stored(1.2345678e-12)
    assert stored(1.23456789e-12) == 1.23457e-12 and stored(-9.87654321e-9) == -9.87654e-9
    assert stored(54.58333333333333) == 54.5833333333           # unchanged at normal scale
    assert stored(1730000133.67) == 1730000133.67                 # offset values never collapse
    assert stored(0.0) == 0.0 and stored(None) is None and stored(float("inf")) is None and stored(float("nan")) is None
    assert stored(5e-320) == 5e-320
    assert geometry(1.234567890123456e-12) == 1.23456789012e-12 and geometry(33.75000000000001) == 33.75
    assert percentile([1e-12] * 9, 50) == 1e-12
    from fathom.univariate import coefficient
    assert coefficient(2.96059e-16) == 0 and coefficient(-7.12986e-10) == -7e-10   # dimensionless noise stays noise


def test_symmetric_column_skewness_is_not_float_noise(make_profile):
    """Decoy: evenly spaced values have zero skew; a 6-figure rule must not surface 1e-16 noise."""
    d = make_profile("x\n" + "".join(f"{1730000123 + 97 * i}\n" for i in range(12))).document
    assert abs(d["columns"][0]["univariate"]["statistics"]["skewness"]) < 1e-9
    d = make_profile("x\n" + "".join(f"{i / 10}\n" for i in range(1, 12))).document
    assert d["columns"][0]["univariate"]["statistics"]["skewness"] == 0


@pytest.mark.parametrize("name", ["normal.csv", "offset.csv"])
def test_normal_and_offset_decoys_do_not_change(name):
    """Decoys: main's saved artifacts must be reproduced apart from the version and the additive test block."""
    main = json.loads((S / name.replace(".csv", ".main-profile.json")).read_text())
    now = json.loads(ProfilingResult(run(name)).to_json())
    assert main["schema_version"] == 1 and now["schema_version"] == 2
    for doc in (main, now):
        doc.pop("schema_version"); doc["source"].pop("origin")
        doc["quality"].pop("missingness_tests", None); doc["quality"]["rules"].pop("missingness_varies_with", None)
        # spec012 (configurator) adds disclosure-only fields: the report settings block and each histogram's bin rule.
        doc.pop("report", None)
        for col in doc["columns"]:
            for ch in col.get("univariate", {}).get("charts", []):
                ch.pop("bin_rule", None)
    assert now == main  # equal artifacts imply equal chart geometry, so normal-scale SVGs are unchanged


def test_artifact_validator_accepts_versions_one_and_two_only():
    d = run("normal.csv")
    for version in (1, 2):
        ProfilingResult({**d, "schema_version": version})
    for version in (0, 3, "2", 2.0, True):
        with pytest.raises(ValueError, match="schema_version"):
            ProfilingResult({**d, "schema_version": version})
    legacy = json.loads((S / "normal.main-profile.json").read_text())
    assert "Distribution of amount" in render_html(ProfilingResult(legacy))


def test_comparison_artifacts_are_version_two():
    from fathom.profiler import compare
    a = ProfilingResult(run("normal.csv"))
    legacy = ProfilingResult(json.loads((S / "normal.main-profile.json").read_text()))
    assert compare(legacy, a).document["schema_version"] == 2


# --- US2: missingness-by-group test --------------------------------------------------

def reported_by(d, rule="missingness_varies_with"):
    return [f for f in d["findings"] if f.get("rule") == rule]


def test_chi_square_tail_matches_known_values():
    from fathom.quality import chi_square_sf
    for x in (0.5, 3, 9.21034, 40):
        assert math.isclose(chi_square_sf(x, 2), math.exp(-x / 2), rel_tol=1e-12)
    assert math.isclose(chi_square_sf(3.841458820694124, 1), .05, rel_tol=1e-9)
    assert math.isclose(chi_square_sf(11.344866730144373, 3), .01, rel_tol=1e-9)
    assert chi_square_sf(0, 4) == 1 and 0 < chi_square_sf(400, 3) < 1e-80


def test_chi_square_tail_agrees_with_scipy_when_installed():
    stats = pytest.importorskip("scipy.stats")
    from fathom.quality import chi_square_sf
    for df in (1, 2, 3, 7, 19):
        for x in (0.01, 0.7, df, df + 3.3, 4 * df + 10, 120):
            assert math.isclose(chi_square_sf(x, df), float(stats.chi2.sf(x, df)), rel_tol=1e-9, abs_tol=1e-300)


def test_planted_group_missingness_is_one_observation_and_never_an_action():
    d = run("planted-missingness.csv")
    found = reported_by(d)
    assert [(f["kind"], f["columns"]) for f in found] == [("observation", ["income", "region"])]
    f = found[0]
    assert f["generator"] == "rule:missingness-test-v1" and "varies with region" in f["message"]
    assert f["message"].startswith("Missingness in income varies with region")
    block = d["quality"]["missingness_tests"]
    assert block["family_alpha"] == .01 and block["correction"] == "Bonferroni"
    assert block["min_cramers_v"] == .15 and block["min_group_size"] == 10
    result = block["results"][0]
    assert result["p_value"] < block["per_test_alpha"] == pytest.approx(.01 / block["tests"], rel=1e-5)
    assert result["cramers_v"] >= .15 and {g["value"]: g["missing"] for g in result["groups"]}["West"] == 30
    assert f["evidence"] == [{"path": "quality.missingness_tests.results.0", "value": result}]
    # Reconciliation: nothing cites the test to suggest an action, and it does not select pairs.
    ids = {x["id"] for x in found}
    for other in d["findings"]:
        if other["kind"] != "observation":
            assert not any(e.get("finding") in ids for e in other["evidence"])
            assert other.get("rule") != "missingness_varies_with"
    assert all(p["method"] != "missingness_test" for p in d["bivariate"])
    assert "missingness_varies_with" not in json.dumps(d["selection"])


def null_table(seed):
    r = random.Random(seed); rows = ["region,segment,flag,score,a,b,c"]
    for _ in range(300):
        cells = [r.choice("NSEW"), r.choice(["x", "y", "z"]), r.choice(["true", "false"]), str(r.randint(1, 1000))]
        cells += ["" if r.random() < .15 else str(r.randint(1, 99)) for _ in range(3)]
        rows.append(",".join(cells))
    return "\n".join(rows) + "\n"


def test_null_data_yields_zero_findings_in_twenty_of_twenty(tmp_path):
    """Data-Guide lesson: the naive version fired on this kind of noise 20 of 20 times."""
    unadjusted_hits = 0
    for seed in range(20):
        path = tmp_path / f"null-{seed}.csv"; path.write_text(null_table(seed))
        d = profile(CSVConnector(path).load()).document
        assert reported_by(d) == [] and reported_by(d, "conditional_missingness") == [], seed
        block = d["quality"]["missingness_tests"]
        assert block["tests"] >= 12 and block["results"] == [] and block["reported"] == 0
        unadjusted_hits += block["unadjusted_below_0_05"] > 0
    # The fixture is real noise, not trivially empty: unadjusted p<0.05 occurs in several tables.
    assert unadjusted_hits >= 5


def test_effect_size_gate_decoy():
    """Significant after Bonferroni but Cramer's V far below 0.15: not reported."""
    from fathom.quality import missingness_table_test, scan_missingness
    r = missingness_table_test([{"value": "A", "n": 5000, "missing": 500}, {"value": "B", "n": 5000, "missing": 650}])
    assert r["p_value"] < 1e-5 and r["cramers_v"] < .05
    block, _ = scan_missingness([{"column": "x", "group_column": "g", "grouping": "observed labels",
                                  "groups": [{"value": "A", "n": 5000, "missing": 500}, {"value": "B", "n": 5000, "missing": 650}]}])
    assert block["tests"] == 1 and block["reported"] == 0


def test_group_size_gate_decoy(make_profile):
    """A large gap between tiny groups is skipped by the test (the descriptive spread rule may still speak)."""
    rows = ["a,group"] + [("" if i < 5 else str(i)) + ",A" for i in range(6)] + [str(i) + ",B" for i in range(6)]
    d = make_profile("\n".join(rows) + "\n").document
    assert reported_by(d) == []
    assert d["quality"]["missingness_tests"]["skipped"].get("group below minimum size", 0) >= 1


def test_missingness_test_bytes_are_stable():
    one = ProfilingResult(run("planted-missingness.csv")).to_json()
    two = ProfilingResult(run("planted-missingness.csv")).to_json()
    assert one == two


# --- US3: palette, kind tags, dark mode ----------------------------------------------

def test_palette_is_the_single_colour_source():
    from fathom import palette
    for module in ("renderers.py", "charts.py", "target_marks.py", "exports.py", "temporal_view.py"):
        text = (SRC / module).read_text()
        assert not re.findall(r"#[0-9a-fA-F]{6}\b", text), module
    assert "white" not in re.findall(r"background:(\w+)", (SRC / "renderers.py").read_text())
    assert set(palette.KIND_COLOURS) == {"light", "dark"}
    from fathom.renderers import KINDS
    for theme in ("light", "dark"):
        assert set(palette.KIND_COLOURS[theme]) == {k for k, _ in KINDS}
        assert set(palette.THEMES[theme]) == set(palette.THEMES["light"])


def test_kind_colours_meet_aa_and_contrast_check_rejects_a_failing_colour():
    from fathom.palette import THEMES, KIND_COLOURS, contrast
    assert contrast("#b7791f", "#ffffff") < 4.5            # violating case: the memo's raw amber on white
    for theme in ("light", "dark"):
        t = THEMES[theme]
        assert contrast(t["ink"], t["surface"]) >= 7 and contrast(t["ink"], t["panel"]) >= 7
        assert contrast(t["muted"], t["panel"]) >= 4.5 and contrast(t["link"], t["panel"]) >= 4.5
        for kind, colour in KIND_COLOURS[theme].items():
            assert contrast(colour, t["panel"]) >= 4.5, (theme, kind)


def test_dark_mode_overrides_kind_tags_and_no_script():
    d = run("planted-missingness.csv")
    html = render_html(ProfilingResult(d))
    assert "@media (prefers-color-scheme:dark){:root:not([data-theme=light]){" in html
    assert ":root[data-theme=dark]{" in html and "color-scheme:light dark" in html
    assert "@media print{:root," in html and "<script" not in html.lower()
    assert re.search(r'<article id="q-missing-test-0" class="finding kind-observation"><p><span class="kind-tag">Observation</span>', html)
    for kind in ("observation", "interpretation", "hypothesis", "action", "question"):
        assert f"--kind-{kind}:" in html and f'class="kind-heading kind-{kind}"' in html
    # SVG marks keep light attributes (portable Markdown) and HTML maps them to tokens.
    from fathom.palette import THEMES
    assert f'[fill="{THEMES["light"]["accent"]}"]{{fill:var(--accent)}}' in html
    md = render_markdown(ProfilingResult(d))
    assert "kind-tag" not in md and "prefers-color-scheme" not in md


def test_light_decoy_body_uses_tokens_not_literals():
    html = render_html(ProfilingResult(run("normal.csv")))
    style = html.split("<style>")[1].split("</style>")[0]
    rules_without_tokens = style.split(":root{")[0]
    assert rules_without_tokens == ""                       # the stylesheet starts with the token block
    body_rules = style.split("@media print")[-1]
    assert not re.findall(r"#[0-9a-fA-F]{6}", body_rules.split("}}", 1)[-1])


def test_fresh_process_html_bytes(tmp_path):
    outputs = []
    for name in ("one", "two"):
        out = tmp_path / name
        r = subprocess.run([sys.executable, "-m", "fathom", "profile", str(S / "planted-missingness.csv"), "--out", str(out)],
                           capture_output=True, text=True, env={"PYTHONPATH": str(SRC.parent), "PATH": ""})
        assert r.returncode == 0, r.stderr
        outputs.append({p.name: p.read_bytes() for p in sorted(out.iterdir())})
    assert outputs[0] == outputs[1]
