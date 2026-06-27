import tempfile
import os
from assistant.finance.csv_source import CsvSource


def test_csv_parses_and_makes_stable_ids():
    content = "Date,Description,Amount\n2026-06-01,Sweetgreen,12.50\n2026-06-02,Shell Gas,40.00\n"
    path = os.path.join(tempfile.gettempdir(), "tx.csv")
    with open(path, "w") as f:
        f.write(content)
    rows = CsvSource(path).fetch()
    assert len(rows) == 2
    assert rows[0]["name"] == "Sweetgreen"
    assert rows[0]["amount"] == 12.5
    again = CsvSource(path).fetch()
    assert rows[0]["external_id"] == again[0]["external_id"]
