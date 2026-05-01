from typing import List, Dict
from core.schemas import NormalizedMessage


def build_search_text(message: NormalizedMessage) -> str:
    """Build searchable text from message"""
    parts = [message.text]
    
    if message.subject:
        parts.append(message.subject)
    
    if message.company:
        parts.append(message.company)
    
    return " ".join(parts)


def chunk_message(message: NormalizedMessage) -> Dict:
    """Convert message into a searchable chunk"""
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


def build_chunks(messages: List[NormalizedMessage]) -> List[Dict]:
    """Build chunks from list of messages"""
    return [chunk_message(msg) for msg in messages]