# Spec 039: reshape long ↔ wide before profiling

**Serves:** P0@2, DG-RD@1 (the reshape travels with the profile as a transformation), DG-RE@1, DG-RF@1.
**Requested by Zach, 2026-11-23 (live):** "Fathom should have a Configuration option to convert 'Long' to 'Wide' or vice-versa. Pivot, melt, reshape, etc." His answers to three questions:
- Pivot duplicates: **"Stop unless declared"**. Two rows for one cell stop the run unless the config declares an aggregation.
- Where it lives first: **"Config file + API first"**. Browser configurator controls are a later slice.
- (Spec 038's question on collapsing isn't relevant here.)

**Records:** `FT-RSH39-R1` (requirement, provisional, written by the implementer), `FT-RSH39-C1`, `FT-RSH39-E1`.

## Configuration

Exactly one of the following:

```yaml
reshape:
  pivot:                    # long to wide
    index: [site, date]     # 1-20 columns; one output row per distinct combination
    columns: metric         # each distinct value becomes a new column (at most 500)
    values: value           # fills those columns
    aggregate: none         # none (default) | first | last | count | sum | mean
```

```yaml
reshape:
  melt:                     # wide to long
    id: [site]              # 1-20 columns repeated on every output row
    value_columns: [jan, feb, mar]   # optional; default: every non-id column
    variable_name: variable # optional; holds the stacked column's name
    value_name: value       # optional; holds its value
```

The block's shape is checked with the rest of the config, before any data is read. Column names are checked against the table when it's loaded. Every other config key (`columns`, `target`, `time_series`, `relationships` …) refers to the **reshaped** table's columns.

## Rules

**Pivot**
- Rows and new columns keep the order of first appearance.
- Combinations missing from the long table become missing cells.
- If one (index, column) cell has more than one row and `aggregate` is `none`, the run stops. The error gives the count and the first example and tells you how to declare an aggregate.
- With a declared aggregate:
  - `first`/`last` take the first or last non-blank value.
  - `count` counts rows.
  - `sum`/`mean` use exact decimal arithmetic on plain numbers: the sum keeps every digit, and a mean is that exact sum divided and rounded to 34 significant digits. Currency, grouping commas, parentheses or underscores stop the run, because combining "$5" with "€5" would hide a unit.
  - A cell that came from a single row keeps its value as written. Under `count` it becomes 1.
- Refused, with a named count:
  - blank `columns` values (they'd become column names);
  - blank index values (unrelated rows would merge);
  - names or keys that differ only by surrounding spaces;
  - a new column name that repeats an index column;
  - more than 500 new columns or 20 million cells.

**Melt**
- Output is row-major: each input row's values stay together, in the declared column order.
- Blank values stay as missing rows. They aren't dropped.
- `variable_name`/`value_name` must not repeat any column of the input table.
- At most 2 million output rows.

Both drop columns that aren't named in the block and say so.

## What the profile says

- `source.reshape`: the block as applied, with rows and columns in and out, new columns, absent cells, combined cells, blank values and dropped columns. `source.sha256` stays the hash of the file as read.
- `context.transformations` gains `{type: "reshape pivot (applied by Fathom)", description: …}`. `guide compare` therefore states it with the other transformations, before any delta (DG-RD).
- Findings (`rule: declared_reshape`):
  - an observation of what changed;
  - for a pivot with absent cells, an open **question**: "N cells of the wide table are missing only because the long table had no row for them. Whether that means not measured, zero or not applicable is not recorded in the data." (Unknowns stay unknown.)
  - For melt, the observation notes that the value column's inferred type is read across all the stacked columns.

Without a `reshape` block nothing changes. JSON, HTML and Markdown are byte-identical to main on all 45 CSVs under `tests/`.

## Where it applies

`guide profile`, `guide validate`, `guide configure`, `guide serve` reruns, the SQL source, `fathom.profile` and `fathom.profile_query`. The configurator keeps the `reshape` block verbatim in the YAML it writes. Panels and liftoff take no reshape; panel config rejects the key as before.

## Not in this slice (for Zach)

1. Configurator controls for reshape (your "later" answer). Today the page shows the reshaped table without saying a reshape was applied; a one-line notice is the first thing to add.
2. Long-schema roles (`schema.mode: long`, `key`/`context`/`metric`/`value`) are still rejected. They could later drive a pivot by default. Today `schema` roles must name columns that exist both before and after the reshape (in practice the index columns).
3. `guide compare` lists the reshape as a transformation, but it doesn't yet warn that the row unit changed between two profiles.

## Drift (AGENTS.md): dissent review

A fresh-context reviewer read the code before the fixes listed above. In summary:
1. **Might violate:**
   - design.md's "no forced pivoting". The pivot is declared, not forced.
   - The existing long-schema vocabulary: a second vocabulary now sits beside it (item 2 above).
   - DG-RD: fixed by adding the transformation to `context`.
   - "Unknowns stay unknown": fixed by refusing blank index values and strict number parsing, plus the absent-cells question.
2. **Evidence:** the reviewer reproduced nine defects. Merged blank keys, currency summed across symbols, float precision loss, single cells rewritten under sum/mean, inconsistent count, whitespace-only first, melt names reusing dropped columns, space-variant keys, and an uncapped pivot are all fixed and tested. Schema roles across the reshape remain item 2.
3. **Counter-evidence:** Zach asked for the option and chose duplicates-stop. Nothing is inferred, the file hash is unchanged, the single CSV parse is respected (the reshape runs on `raw_rows` after `load_csv_bytes`), and the bounds are fixed before profiling.
4. **If the concern is right:** profiles would present combined or rewritten values as data, and comparisons across a reshape would look like-for-like. The findings and `context` entry are the guard.
5. **Escalate:** items 1–3 above.
