ROUTES = ("note", "calendar", "email", "chat")

CLASSIFY_PROMPT = (
    "Classify the user's message into exactly one label.\n"
    "Labels:\n"
    "- note: a brain dump, meeting notes, or things to remember.\n"
    "- calendar: a request to schedule, book, or add something to a calendar at a time or date.\n"
    "- email: a request to check, triage, or summarize the inbox or recent emails.\n"
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
