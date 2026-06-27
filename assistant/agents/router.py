ROUTES = ("note", "calendar", "email", "research", "code", "critic", "finance", "chat")

CLASSIFY_PROMPT = (
    "Classify the user's message into exactly one label.\n"
    "Labels:\n"
    "- note: a brain dump, meeting notes, or things to remember.\n"
    "- calendar: a request to schedule, book, or add something to a calendar at a time or date.\n"
    "- email: a request to check, triage, summarize, organize, clean up, archive, or delete inbox mail.\n"
    "- research: a question that needs current information, a web lookup, or phrases like look up, research, or what is the latest on.\n"
    "- code: a request to write, review, explain, or debug code, or a question about programming.\n"
    "- critic: when the user wants to think through, pressure-test, or get pushback on an idea or decision.\n"
    "- finance: a request to sync, update, or ask about bank transactions and spending.\n"
    "- chat: a question or general conversation.\n"
    "Respond with only the single label word, nothing else.\n\n"
    "Message:\n"
)


def classify(router_provider, message: str) -> str:
    raw = router_provider.complete(CLASSIFY_PROMPT + message).strip().lower()
    for route in ROUTES:
        if route in raw:
            return route
    return "chat"
