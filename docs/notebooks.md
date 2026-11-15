# Fathom in a notebook

Fathom runs inside a Jupyter notebook, including a hosted one, with nothing that needs admin rights. It opens no network connection: the install step is the only one that downloads anything.

## Install into the notebook's own kernel

Run this in a cell, so the package lands in the environment the kernel uses (not the system Python):

```python
%pip install "fathom-guide @ git+https://github.com/eraevous/Fathom.git"
```

Fathom accepts `pandas>=2.0,<3` and `PyYAML>=6.0,<7`, so it installs beside the versions a managed image already has. Python 3.11 or newer. Restart the kernel if pip asks you to.

## Profile a DataFrame

```python
import pandas as pd
import fathom

df = pd.read_csv("data.csv", dtype=str, keep_default_na=False)   # read as text: see the note below
result = fathom.profile(df, config="review.yaml", out="fathom-out", name="data.csv")
result            # shows Key findings and the dataset summary in the cell
```

- `config` can be a YAML path, a dict with the same keys, or left out.
- `out` is a folder; Fathom writes `report.html`, `report.md` and `guide-profile.json` there, exactly as `guide profile` does. Without `out`, nothing is written and `result.files` holds the texts.
- `name` is recorded as the source origin. The source hash is the SHA-256 of the table's content.
- `result.document` is the machine-readable profile; `result.show()` gives the inline view again.

Liftoff (no config):

```python
from fathom.api import liftoff
liftoff(df, out="fathom-out", name="data.csv")
```

## Text in, text profiled

Fathom profiles what the table says as text. A DataFrame read with `dtype=str, keep_default_na=False` gives the same results as `guide profile` on the file. Typed columns still work: each value is written with `str()` (`1.0`, `2026-01-01 00:00:00`) and missing values (None, NaN, NaT) become empty fields, so the profile describes that text. The index is dropped; call `df.reset_index()` first to keep it. Column names must be unique, nonblank strings.

## Saving to the notebook's storage

`out` is an ordinary local path, so use a folder the notebook service keeps (for example the workspace or home folder it shows in its file browser). Open `report.html` from there for the full report; the cell shows only the collapsed view, because notebook outputs often block scripts.
