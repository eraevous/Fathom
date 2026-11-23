"""Spec 039: declared long<->wide reshape before profiling (FT-RSH39-R1)."""
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

import fathom
from fathom.config import validate_config
from fathom.connectors import CSVConnector
from fathom.profiler import profile
from fathom.reshape import apply

ROOT = Path(__file__).parents[1]
LONG = "site,date,metric,value,note\nA,2024-01,temp,10,x\nA,2024-01,rain,3,x\nB,2024-01,temp,12,y\nB,2024-02,rain,0,y\nA,2024-02,temp,11,x\n"
PIVOT = {"reshape": {"pivot": {"index": ["site", "date"], "columns": "metric", "values": "value"}}}


def load(tmp_path, text, name="t.csv"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return CSVConnector(path).load()


def run(tmp_path, text, cfg):
    cfg = validate_config(cfg)
    data = apply(load(tmp_path, text), cfg)
    return data, profile(data, validate_config(cfg, list(data.frame.columns)))


def test_pivot_long_to_wide_shape_order_and_absent_cells(tmp_path):
    data, result = run(tmp_path, LONG, PIVOT)
    assert list(data.frame.columns) == ["site", "date", "temp", "rain"]
    assert data.raw_rows == [["A", "2024-01", "10", "3"], ["B", "2024-01", "12", ""], ["B", "2024-02", "", "0"], ["A", "2024-02", "11", ""]]
    s = result.document["source"]["reshape"]
    assert (s["rows_in"], s["rows_out"], s["columns_out"], s["new_columns"], s["cells_absent"], s["cells_combined"]) == (5, 4, 4, 2, 3, 0)
    assert s["dropped_columns"] == ["note"]
    kinds = {f["id"]: f["kind"] for f in result.document["findings"] if f.get("rule") == "declared_reshape"}
    assert kinds == {"reshape": "observation", "reshape-absent": "question"}
    absent = next(f for f in result.document["findings"] if f["id"] == "reshape-absent")
    assert "3 cells" in absent["message"] and "not recorded" in absent["message"]
    assert "note" in next(f for f in result.document["findings"] if f["id"] == "reshape")["message"]
    # Provenance keeps the hash of the file as read.
    assert result.document["source"]["sha256"] == load(tmp_path, LONG, "again.csv").source["sha256"]


def test_duplicates_stop_unless_an_aggregate_is_declared(tmp_path):
    dup = LONG + "A,2024-01,temp,14,x\n"
    with pytest.raises(ValueError, match=r"1 cells have more than one row .*declare reshape.pivot.aggregate"):
        run(tmp_path, dup, PIVOT)
    expected = {"first": "10", "last": "14", "count": "2", "sum": "24", "mean": "12"}
    for how, value in expected.items():
        cfg = {"reshape": {"pivot": {**PIVOT["reshape"]["pivot"], "aggregate": how}}}
        data, result = run(tmp_path, dup, cfg)
        assert data.raw_rows[0][2] == value, how
        assert result.document["source"]["reshape"]["cells_combined"] == 1
        assert "(" + how + ", as declared)" in next(f for f in result.document["findings"] if f["id"] == "reshape")["message"]


def test_numeric_aggregate_refuses_text(tmp_path):
    bad = LONG + "A,2024-01,temp,warm,x\n"
    with pytest.raises(ValueError, match="not one"):
        run(tmp_path, bad, {"reshape": {"pivot": {**PIVOT["reshape"]["pivot"], "aggregate": "mean"}}})
    for spelled in ("$14", "(14)", "1_4", "1,400"):
        with pytest.raises(ValueError, match="not one"):
            run(tmp_path, LONG + f'A,2024-01,temp,"{spelled}",x\n', {"reshape": {"pivot": {**PIVOT["reshape"]["pivot"], "aggregate": "sum"}}})


def test_aggregates_are_exact_and_leave_single_cells_as_written(tmp_path):
    long = "k,m,v\na,x,9007199254740993\na,x,0\nb,x,0.1\nb,x,0.2\nc,x,007\nd,x, \nd,x,5\n"
    pivot = {"index": ["k"], "columns": "m", "values": "v"}
    sums, _ = run(tmp_path, long, {"reshape": {"pivot": {**pivot, "aggregate": "sum"}}})
    assert [r[1] for r in sums.raw_rows] == ["9007199254740993", "0.3", "007", "5"]
    means, _ = run(tmp_path, long, {"reshape": {"pivot": {**pivot, "aggregate": "mean"}}})
    assert [r[1] for r in means.raw_rows] == ["4503599627370496.5", "0.15", "007", "5"]
    big = "k,m,v\na,x,1e34\na,x,1\na,x,-1e34\nb,x,12345678901234567890123456789012345\nb,x,0\n"
    exact, _ = run(tmp_path, big, {"reshape": {"pivot": {**pivot, "aggregate": "sum"}}})
    assert [r[1] for r in exact.raw_rows] == ["1", "12345678901234567890123456789012345"]  # Codex on #78
    for value in ("1e-1001", "1e1001"):
        with pytest.raises(ValueError, match="exponents from -1000 to 1000"):
            run(tmp_path, f"k,m,v\na,x,{value}\na,x,{value}\n", {"reshape": {"pivot": {**pivot, "aggregate": "sum"}}})
    edge, _ = run(tmp_path, "k,m,v\na,x,1e-1000\na,x,1e-1000\nb,x,1e1000\nb,x,1e1000\n", {"reshape": {"pivot": {**pivot, "aggregate": "sum"}}})
    assert [r[1] for r in edge.raw_rows] == ["0." + "0" * 999 + "2", "2" + "0" * 1000]
    # The caller's decimal context does not leak in (Copilot on #78).
    import decimal
    with decimal.localcontext() as caller:
        caller.rounding, caller.traps[decimal.Inexact] = decimal.ROUND_UP, True
        third, _ = run(tmp_path, "k,m,v\na,x,1\na,x,0\na,x,0\n", {"reshape": {"pivot": {**pivot, "aggregate": "mean"}}})
    assert third.raw_rows[0][1] == "0." + "3" * 34
    first, _ = run(tmp_path, long, {"reshape": {"pivot": {**pivot, "aggregate": "first"}}})
    assert first.raw_rows[3][1] == "5"  # blank rows are skipped by first/last
    counts, result = run(tmp_path, long, {"reshape": {"pivot": {**pivot, "aggregate": "count"}}})
    assert [r[1] for r in counts.raw_rows] == ["2", "2", "1", "2"]
    assert "number of rows, not a value" in next(f for f in result.document["findings"] if f["id"] == "reshape")["message"]


def test_pivot_refusals(tmp_path):
    with pytest.raises(ValueError, match="blank 'metric'"):
        run(tmp_path, LONG + "A,2024-03,,5,x\n", PIVOT)
    with pytest.raises(ValueError, match="repeat an index column name"):
        run(tmp_path, LONG + "A,2024-03,site,5,x\n", PIVOT)
    with pytest.raises(ValueError, match="repeat an index column name"):
        run(tmp_path, LONG + "A,2024-03,site ,5,x\n", PIVOT)
    with pytest.raises(ValueError, match="not in the table: nope"):
        run(tmp_path, LONG, {"reshape": {"pivot": {"index": ["nope"], "columns": "metric", "values": "value"}}})
    with pytest.raises(ValueError, match="blank index value"):
        run(tmp_path, LONG + ",2024-03,temp,5,x\n", PIVOT)
    with pytest.raises(ValueError, match="differ only by surrounding spaces"):
        run(tmp_path, LONG + "A,2024-03,temp ,5,x\n", PIVOT)
    with pytest.raises(ValueError, match="differ only by surrounding spaces"):
        run(tmp_path, LONG + " A,2024-01,temp,5,x\n", PIVOT)
    many = "k,m,v\n" + "".join(f"1,c{i},1\n" for i in range(501))
    with pytest.raises(ValueError, match="at most 500 new columns"):
        run(tmp_path, many, {"reshape": {"pivot": {"index": ["k"], "columns": "m", "values": "v"}}})


def test_config_shape_is_checked_before_data(tmp_path):
    for bad, match in [({"pivot": {}, "melt": {}}, "exactly one"), ({"pivot": {"index": ["a"], "columns": "b"}}, "needs index, columns and values"),
                       ({"pivot": {"index": ["a"], "columns": "a", "values": "c"}}, "different columns"),
                       ({"pivot": {"index": ["a"], "columns": "b", "values": "c", "aggregate": "median"}}, "aggregate must be one of"),
                       ({"melt": {"value_columns": ["a"]}}, "needs id"), ({"melt": {"id": ["a"], "value_name": "a"}}, "must differ"),
                       ({"melt": {"id": []}}, "1 to 20"), ({"melt": {"id": [[]]}}, "distinct column names"),
                       ({"pivot": {"index": [{}], "columns": "b", "values": "c"}}, "distinct column names"),
                       ({"melt": {"id": ["a"], "value_columns": [["b"]]}}, "distinct column names")]:
        with pytest.raises(ValueError, match=match):
            validate_config({"reshape": bad})


def test_melt_wide_to_long_row_major(tmp_path):
    wide = "site,jan,feb,mar\nA,1,2,\nB,4,,6\n"
    data, result = run(tmp_path, wide, {"reshape": {"melt": {"id": ["site"], "value_columns": ["jan", "feb"], "variable_name": "month"}}})
    assert list(data.frame.columns) == ["site", "month", "value"]
    assert data.raw_rows == [["A", "jan", "1"], ["A", "feb", "2"], ["B", "jan", "4"], ["B", "feb", ""]]
    s = result.document["source"]["reshape"]
    assert (s["rows_out"], s["blank_values"], s["dropped_columns"]) == (4, 1, ["mar"])
    msg = next(f for f in result.document["findings"] if f["id"] == "reshape")["message"]
    assert "wide to long" in msg and "mar" in msg and "read across all of them" in msg
    with pytest.raises(ValueError, match="repeat a column of the table: mar"):
        run(tmp_path, wide, {"reshape": {"melt": {"id": ["site"], "value_columns": ["jan"], "variable_name": "mar"}}})
    transforms = result.document["context"]["transformations"]
    assert transforms[-1]["type"] == "reshape melt (applied by Fathom)" and transforms[-1]["description"] == msg
    # Default value_columns: every non-id column.
    data, _ = run(tmp_path, wide, {"reshape": {"melt": {"id": ["site"]}}})
    assert len(data.raw_rows) == 6 and list(data.frame.columns) == ["site", "variable", "value"]


def test_pivot_then_melt_round_trips(tmp_path):
    data, _ = run(tmp_path, LONG, PIVOT)
    wide_csv = ",".join(data.frame.columns) + "\n" + "".join(",".join(r) + "\n" for r in data.raw_rows)
    back, _ = run(tmp_path, wide_csv, {"reshape": {"melt": {"id": ["site", "date"], "variable_name": "metric"}}})
    kept = sorted(tuple(r) for r in back.raw_rows if r[-1])
    assert kept == sorted(tuple(r.split(",")[:4]) for r in LONG.strip().split("\n")[1:])


def test_no_reshape_block_changes_nothing(tmp_path):
    data = load(tmp_path, LONG)
    assert apply(data, validate_config({})) is data
    assert "reshape" not in validate_config({})
    doc = profile(data, validate_config({}, list(data.frame.columns))).document
    assert "reshape" not in doc["source"] and not any(f.get("rule") == "declared_reshape" for f in doc["findings"])


def test_cli_and_api_agree_and_columns_config_targets_new_columns(tmp_path):
    csv = tmp_path / "long.csv"
    csv.write_text(LONG, encoding="utf-8")
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("reshape:\n  pivot:\n    index: [site, date]\n    columns: metric\n    values: value\n"
                   "columns:\n  temp:\n    units: degC\n", encoding="utf-8")
    out = tmp_path / "out"
    r = subprocess.run([sys.executable, "-m", "fathom", "profile", str(csv), "--config", str(cfg), "--out", str(out)],
                       cwd=ROOT, capture_output=True, text=True, env={"PYTHONPATH": str(ROOT / "src"), "PATH": "/usr/bin:/bin"})
    assert r.returncode == 0, r.stderr
    doc = json.loads((out / "guide-profile.json").read_text())
    assert [c["name"] for c in doc["columns"]] == ["site", "date", "temp", "rain"]
    assert "Reshaped long to wide" in (out / "report.html").read_text()
    api = fathom.profile(pd.read_csv(csv, dtype=str, keep_default_na=False), str(cfg))
    assert [c["name"] for c in api.document["columns"]] == ["site", "date", "temp", "rain"]
    assert api.document["source"]["reshape"] == doc["source"]["reshape"]
