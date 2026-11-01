from pathlib import Path

import pytest

from fathom.connectors import CSVConnector
from fathom.profiler import profile


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def make_profile(tmp_path):
    def make(csv_text, config=None):
        path = tmp_path / "input.csv"
        path.write_text(csv_text, encoding="utf-8")
        return profile(CSVConnector(path).load(), config)
    return make
