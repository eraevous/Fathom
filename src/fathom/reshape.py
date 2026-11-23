"""Declared long<->wide reshape before profiling (spec 039; FT-RSH39-R1).

The configuration names every column the reshape uses, so nothing is guessed. A pivot never
combines values silently: two rows for the same cell stop the run unless an aggregation is
declared. The reshape is recorded in `source.reshape`, and the profile reports what it created
(rows, columns, cells absent from the long table), so the reader can tell the reshaped table
from the file on disk. The source hash stays the hash of the file as read.
"""

import re
from decimal import Decimal, localcontext

import pandas as pd

from .models import GuideDataFrame

AGGREGATES = ("none", "first", "last", "count", "sum", "mean")
MAX_INDEX, MAX_NEW_COLUMNS, MAX_ROWS_OUT, MAX_CELLS_OUT = 20, 500, 2_000_000, 20_000_000
# sum/mean take plain decimal numbers only: no currency, grouping commas, parentheses or underscores.
PLAIN = re.compile(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?')
PIVOT_KEYS, MELT_KEYS = {"index", "columns", "values", "aggregate"}, {"id", "value_columns", "variable_name", "value_name"}


def _names(value, name, low=1, high=MAX_INDEX):
    if (not isinstance(value, list) or not low <= len(value) <= high or len(set(value)) != len(value)
            or any(not isinstance(c, str) or not c.strip() for c in value)):
        raise ValueError(f"{name} must list {low} to {high} distinct column names")
    return list(value)


def _name(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a column name")
    return value


def validate(raw):
    """Shape only (column names are checked against the table in `apply`). None when absent."""
    if raw is None:
        return None
    if not isinstance(raw, dict) or len(raw) != 1 or set(raw) - {"pivot", "melt"}:
        raise ValueError("reshape must have exactly one of: pivot (long to wide), melt (wide to long)")
    (op, spec), = raw.items()
    if not isinstance(spec, dict):
        raise ValueError(f"reshape.{op} must be a mapping")
    if op == "pivot":
        if set(spec) - PIVOT_KEYS or not {"index", "columns", "values"} <= set(spec):
            raise ValueError("reshape.pivot needs index, columns and values (aggregate is optional)")
        out = {"index": _names(spec["index"], "reshape.pivot.index"),
               "columns": _name(spec["columns"], "reshape.pivot.columns"),
               "values": _name(spec["values"], "reshape.pivot.values"),
               "aggregate": spec.get("aggregate", "none")}
        if out["aggregate"] not in AGGREGATES:
            raise ValueError("reshape.pivot.aggregate must be one of: " + ", ".join(AGGREGATES))
        used = out["index"] + [out["columns"], out["values"]]
        if len(set(used)) != len(used):
            raise ValueError("reshape.pivot index, columns and values must be different columns")
        return {"pivot": out}
    if set(spec) - MELT_KEYS or "id" not in spec:
        raise ValueError("reshape.melt needs id (value_columns, variable_name and value_name are optional)")
    out = {"id": _names(spec["id"], "reshape.melt.id"),
           "value_columns": None if spec.get("value_columns") is None else _names(spec["value_columns"], "reshape.melt.value_columns", 1, 10_000),
           "variable_name": _name(spec.get("variable_name", "variable"), "reshape.melt.variable_name"),
           "value_name": _name(spec.get("value_name", "value"), "reshape.melt.value_name")}
    if out["value_columns"] is not None and set(out["value_columns"]) & set(out["id"]):
        raise ValueError("reshape.melt.value_columns must not repeat an id column")
    new = out["id"] + [out["variable_name"], out["value_name"]]
    if len(set(new)) != len(new):
        raise ValueError("reshape.melt variable_name and value_name must differ from each other and from the id columns")
    return {"melt": out}


def _unknown(names, columns, name):
    missing = [c for c in names if c not in columns]
    if missing:
        raise ValueError(f"{name} names columns not in the table: " + ", ".join(missing))


def _decimal_text(d):
    text = format(d, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _aggregate(how, raws):
    """raws: the lexical cells of one (key, column) cell, in file order, two or more of them.

    first/last skip blank cells; count counts rows; sum/mean use exact decimal arithmetic on
    plain numbers. Returns None when sum/mean meet a non-blank value that is not a plain number.
    """
    present = [r for r in raws if r.strip()]
    if how == "count":
        return str(len(raws))
    if how in ("first", "last"):
        return (present[0] if how == "first" else present[-1]) if present else ""
    if not present:
        return ""
    if any(not PLAIN.fullmatch(r.strip()) for r in present):
        return None
    with localcontext() as ctx:
        ctx.prec = 34
        total = sum((Decimal(r.strip()) for r in present), Decimal(0))
        return _decimal_text(total if how == "sum" else total / len(present))


def _pivot(columns, raw_rows, spec):
    index, col, val, how = spec["index"], spec["columns"], spec["values"], spec["aggregate"]
    _unknown(index + [col, val], columns, "reshape.pivot")
    at = {c: i for i, c in enumerate(columns)}
    blank = sum(1 for r in raw_rows if not r[at[col]].strip())
    if blank:
        raise ValueError(f"reshape.pivot: {blank:,} rows have a blank '{col}', which would be a column name; fill or filter them first")
    blank = sum(1 for r in raw_rows if any(not r[at[c]].strip() for c in index))
    if blank:
        raise ValueError(f"reshape.pivot: {blank:,} rows have a blank index value, so they cannot be told apart; fill or filter them first")
    keys, names, cells = {}, {}, {}
    for r in raw_rows:
        key = tuple(r[at[c]] for c in index)
        keys.setdefault(key, len(keys))
        names.setdefault(r[at[col]], len(names))
        cells.setdefault((key, r[at[col]]), []).append(r[at[val]])
    new = list(names)
    for label, values in (("column names from '" + col + "'", new), ("index keys", list(keys))):
        seen = {}
        for v in values:
            norm = tuple(x.strip() for x in v) if isinstance(v, tuple) else v.strip()
            if norm in seen and seen[norm] != v:
                raise ValueError(f"reshape.pivot: {label} differ only by surrounding spaces ({seen[norm]!r} and {v!r}); clean them first")
            seen.setdefault(norm, v)
    clash = [n for n in new if n in index]
    if clash:
        raise ValueError(f"reshape.pivot: values of '{col}' repeat an index column name: " + ", ".join(clash))
    if len(new) > MAX_NEW_COLUMNS:
        raise ValueError(f"reshape.pivot: '{col}' has {len(new):,} distinct values; at most {MAX_NEW_COLUMNS} new columns")
    if len(keys) * (len(index) + len(new)) > MAX_CELLS_OUT:
        raise ValueError(f"reshape.pivot would produce {len(keys) * (len(index) + len(new)):,} cells; the limit is {MAX_CELLS_OUT:,}")
    repeated = [(k, n) for (k, n), v in cells.items() if len(v) > 1]
    if repeated and how == "none":
        (k, n) = repeated[0]
        raise ValueError(f"reshape.pivot: {len(repeated):,} cells have more than one row (first: {dict(zip(index, k))}, {col}={n!r}); "
                         "declare reshape.pivot.aggregate (first, last, count, sum or mean) to combine them")
    out, unparsed = [], 0
    for key in keys:
        row = list(key)
        for n in new:
            raws = cells.get((key, n))
            if raws is None:
                row.append("")
                continue
            # A cell from one row keeps its value as written, except under count (which counts rows).
            value = (raws[0] if how != "count" else "1") if len(raws) == 1 else _aggregate(how, raws)
            if value is None:
                unparsed += 1
                value = ""
            row.append(value)
        out.append(row)
    if unparsed:
        raise ValueError(f"reshape.pivot: aggregate {how} needs plain numbers, but {unparsed:,} combined cells have a value of '{val}' that is not one (no currency, grouping commas or parentheses)")
    absent = len(keys) * len(new) - len(cells)
    dropped = [c for c in columns if c not in index + [col, val]]
    summary = {"operation": "pivot", "direction": "long to wide", "index": index, "columns": col, "values": val, "aggregate": how,
               "rows_in": len(raw_rows), "rows_out": len(out), "columns_in": len(columns), "columns_out": len(index) + len(new),
               "new_columns": len(new), "cells_absent": absent, "cells_combined": len(repeated), "dropped_columns": dropped}
    return index + new, out, summary


def _melt(columns, raw_rows, spec):
    ids, var, value = spec["id"], spec["variable_name"], spec["value_name"]
    _unknown(ids, columns, "reshape.melt.id")
    measured = spec["value_columns"] if spec["value_columns"] is not None else [c for c in columns if c not in ids]
    _unknown(measured, columns, "reshape.melt.value_columns")
    if not measured:
        raise ValueError("reshape.melt: no value columns left after the id columns")
    clash = [n for n in (var, value) if n in columns]
    if clash:
        raise ValueError("reshape.melt: variable_name/value_name repeat a column of the table: " + ", ".join(clash) + "; choose another name")
    if len(raw_rows) * len(measured) > MAX_ROWS_OUT:
        raise ValueError(f"reshape.melt would produce {len(raw_rows) * len(measured):,} rows; the limit is {MAX_ROWS_OUT:,}")
    at = {c: i for i, c in enumerate(columns)}
    # Row-major: each input row's measurements stay together, in the declared column order.
    out = [[r[at[c]] for c in ids] + [m, r[at[m]]] for r in raw_rows for m in measured]
    dropped = [c for c in columns if c not in ids and c not in measured]
    summary = {"operation": "melt", "direction": "wide to long", "id": ids, "value_columns": measured,
               "variable_name": var, "value_name": value, "rows_in": len(raw_rows), "rows_out": len(out),
               "columns_in": len(columns), "columns_out": len(ids) + 2,
               "blank_values": sum(1 for row in out if not row[-1].strip()), "dropped_columns": dropped}
    return ids + [var, value], out, summary


def apply(data: GuideDataFrame, cfg: dict | None) -> GuideDataFrame:
    """Return `data` unchanged without a reshape block; otherwise the reshaped table, recorded in source."""
    block = (cfg or {}).get("reshape")
    if not block:
        return data
    columns = list(data.frame.columns)
    raw_rows = data.raw_rows if data.raw_rows is not None else [["" if v is None else v for v in row] for row in data.frame.values.tolist()]
    names, rows, summary = (_pivot if "pivot" in block else _melt)(columns, raw_rows, block.get("pivot") or block.get("melt"))
    frame = pd.DataFrame([[s if s.strip() else None for s in row] for row in rows], columns=names, dtype=object)
    return GuideDataFrame(frame, data.schema.resolve(names), {**data.source, "reshape": summary}, rows)


def findings(summary: dict) -> list[tuple[str, str, str]]:
    """(id suffix, kind, message) for the profile: what the reshape made, and what it cannot tell."""
    if summary["operation"] == "pivot":
        text = (f"Reshaped long to wide before profiling: {summary['rows_in']:,} rows × {summary['columns_in']:,} columns became "
                f"{summary['rows_out']:,} rows × {summary['columns_out']:,} columns, one row per {', '.join(summary['index'])} "
                f"and one new column per value of {summary['columns']} ({summary['new_columns']:,}), filled from {summary['values']}.")
        if summary["cells_combined"]:
            text += f" {summary['cells_combined']:,} cells combine more than one row ({summary['aggregate']}, as declared)."
        if summary["aggregate"] == "count":
            text += " Under count, every filled cell holds a number of rows, not a value."
        if summary["dropped_columns"]:
            text += f" Not carried into the wide table: {', '.join(summary['dropped_columns'])}."
        out = [("", "observation", text)]
        if summary["cells_absent"]:
            out.append(("-absent", "question",
                        f"{summary['cells_absent']:,} cells of the wide table are missing only because the long table had no row for them. "
                        "Whether that means not measured, zero or not applicable is not recorded in the data."))
        return out
    text = (f"Reshaped wide to long before profiling: {summary['rows_in']:,} rows × {summary['columns_in']:,} columns became "
            f"{summary['rows_out']:,} rows × {summary['columns_out']:,} columns; {len(summary['value_columns']):,} columns were stacked "
            f"into {summary['variable_name']} (their names) and {summary['value_name']} (their values).")
    if summary["dropped_columns"]:
        text += f" Not carried into the long table: {', '.join(summary['dropped_columns'])}."
    text += (f" {summary['value_name']} holds values from all {len(summary['value_columns']):,} stacked columns, "
             "so its inferred type is read across all of them.")
    return [("", "observation", text)]
