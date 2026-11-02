"""Local CSV → GuideDataFrame. No semantic conversions or null-token guessing."""

import csv
from hashlib import sha256
import io
from pathlib import Path

import pandas as pd

from .models import GuideDataFrame, SchemaContract


class CSVConnector:
    def __init__(self, path: str | Path, schema: SchemaContract | None = None):
        self.path = Path(path)
        self.schema = schema or SchemaContract()

    def connect(self) -> None:
        if not self.path.is_file():
            raise ValueError(f"CSV file not found: {self.path}")

    def load(self) -> GuideDataFrame:
        self.connect()
        raw = self.path.read_bytes()
        reader = csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline=""), strict=True)
        columns = next(reader, None)
        if not columns or any(not c.strip() for c in columns) or len(columns) != len(set(columns)):
            raise ValueError("CSV requires unique, nonblank column headers")
        rows, raw_rows = [], []
        for row in reader:
            if len(row) != len(columns):
                raise ValueError(f"CSV record ending at line {reader.line_num} has {len(row)} fields; expected {len(columns)}")
            raw_rows.append(row)
            rows.append([s if s.strip() else None for s in row])
        schema = self.schema.resolve(columns)
        return GuideDataFrame(pd.DataFrame(rows, columns=columns, dtype=object), schema,
                              {"connector": "csv", "origin": str(self.path), "sha256": sha256(raw).hexdigest()}, raw_rows)
