def aggregate_context(
    incoming_message,
    resolved_matches: list[tuple],
    rag_results: list[dict]
) -> dict:
    resolved_messages = [match[0] for match in resolved_matches]

    sources = sorted(set(msg.source for msg in resolved_messages))

    timeline = sorted(
        resolved_messages,
        key=lambda msg: msg.timestamp
    )

    relationship_history = []

    for msg in timeline:
        relationship_history.append({
            "source": msg.source,
            "timestamp": msg.timestamp,
            "person_name": msg.person_name,
            "subject": msg.subject,
            "text": msg.text
        })

    open_commitments = extract_open_commitments(relationship_history)

    return {
        "person": incoming_message.person_name,
        "sources_found": sources,
        "relationship_history": relationship_history,
        "rag_context": rag_results,
        "open_commitments": open_commitments
    }


def extract_open_commitments(history: list[dict]) -> list[str]:
    commitments = []

    keywords = [
        "available",
        "call",
        "tomorrow",
        "confirming",
        "discuss",
        "intro"
    ]

    for item in history:
        text = item["text"].lower()

        if any(keyword in text for keyword in keywords):
            commitments.append(item["text"])

    return commitments