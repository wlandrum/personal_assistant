import os
import tempfile
from assistant.finance.charts import category_bar


def test_category_bar_writes_file():
    path = os.path.join(tempfile.gettempdir(), "chart_test.png")
    if os.path.exists(path):
        os.remove(path)
    out = category_bar(
        [{"category": "dining", "total": 15.0}, {"category": "gas", "total": 40.0}],
        path,
    )
    assert out == path
    assert os.path.exists(path)
    assert os.path.getsize(path) > 0
