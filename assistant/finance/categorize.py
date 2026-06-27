import json
from assistant.llm.factory import get_provider

CATEGORIES = (
    "groceries", "dining", "transportation", "shopping", "bills_utilities",
    "entertainment", "health", "travel", "income", "transfer", "other",
)


def normalize(name: str) -> str:
    return " ".join(name.lower().split())


def _parse_array(raw: str):
    cleaned = raw.strip().strip("`")
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start != -1 and end != -1:
        cleaned = cleaned[start:end + 1]
    return json.loads(cleaned)


def categorize(store, settings, rows: list[dict]) -> list[tuple]:
    results = []
    unknown = []
    for r in rows:
        key = normalize(r["name"])
        cat = store.get_merchant_rule(key)
        if cat:
            results.append((r["id"], cat))
        else:
            unknown.append((key, r))

    if unknown:
        listing = "\n".join(f"{i}. {r['name']}" for i, (_k, r) in enumerate(unknown))
        prompt = (
            "Categorize each merchant into one of: " + ", ".join(CATEGORIES) + ". "
            "Return a JSON array only, one object per line, shape: "
            '[{"index": 0, "category": "groceries"}].\n\n' + listing
        )
        small = get_provider(settings, "router")
        try:
            labels = _parse_array(small.complete(prompt))
            by_index = {x["index"]: x["category"] for x in labels if "index" in x}
        except Exception:
            by_index = {}
        for i, (key, r) in enumerate(unknown):
            cat = by_index.get(i, "other")
            if cat not in CATEGORIES:
                cat = "other"
            store.add_merchant_rule(key, cat)
            results.append((r["id"], cat))

    return results
