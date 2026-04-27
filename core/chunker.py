from core.schemas import NormalizedMessage


def chunk_message(message: NormalizedMessage) -> dict:
    return {
        "chunk_id": f"{message.source}_{message.id}",
        "source": message.source,
        "person_name": message.person_name,
        "email": message.email,
        "phone": message.phone,
        "handle": message.handle,
        "company": message.company,
        "timestamp": message.timestamp,
        "subject": message.subject,
        "text": message.text,
        "search_text": build_search_text(message)
    }


def build_search_text(message: NormalizedMessage) -> str:
    parts = [
        message.person_name or "",
        message.company or "",
        message.subject or "",
        message.text or "",
        message.source or ""
    ]

    return " ".join(parts)


def build_chunks(messages: list[NormalizedMessage]) -> list[dict]:
    return [chunk_message(message) for message in messages]