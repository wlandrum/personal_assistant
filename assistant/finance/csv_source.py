import csv
import hashlib


class CsvSource:
    source_name = "csv"

    def __init__(self, path: str, date_col="Date", name_col="Description", amount_col="Amount"):
        self.path = path
        self.date_col = date_col
        self.name_col = name_col
        self.amount_col = amount_col

    def fetch(self) -> list[dict]:
        out = []
        with open(self.path, newline="") as f:
            for row in csv.DictReader(f):
                name = row[self.name_col].strip()
                date = row[self.date_col].strip()
                amount = float(row[self.amount_col])
                raw = f"{date}|{name}|{amount}"
                ext = hashlib.sha1(raw.encode()).hexdigest()
                out.append({"external_id": ext, "date": date, "name": name, "amount": amount})
        return out
