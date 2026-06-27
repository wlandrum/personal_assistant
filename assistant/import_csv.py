import sys
from assistant.config import load_settings
from assistant.data.db import connect
from assistant.finance.csv_source import CsvSource
from assistant.agents.finance import FinanceSubagent


def main():
    if len(sys.argv) < 3:
        print("usage: python -m assistant.import_csv <owner_id> <path_to_csv>")
        return
    owner_id, path = sys.argv[1], sys.argv[2]
    settings = load_settings()
    conn = connect()
    agent = FinanceSubagent(conn, settings)
    print(agent._ingest(owner_id, CsvSource(path)))


if __name__ == "__main__":
    main()
