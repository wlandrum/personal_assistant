def build_context(store, embedder, message: str, k: int = 5) -> str:
    facts = store.get_active_facts()
    query_vec = embedder.embed(message)
    episodes = store.search_episodes(query_vec, k=k)

    lines = [
        "You are a personal assistant for one specific user.",
        "Use the memory below to ground your answer. If the memory does not cover something, say so rather than guessing.",
    ]
    if facts:
        lines.append("")
        lines.append("Known facts about this user:")
        for f in facts:
            lines.append(f"- {f['key']}: {f['value']}")
    if episodes:
        lines.append("")
        lines.append("Relevant notes from past conversations:")
        for e in episodes:
            lines.append(f"- {e['summary']}")
    return "\n".join(lines)
