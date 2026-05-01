from typing import Dict, List
from core.schemas import NormalizedMessage


def normalize_email(raw: Dict) -> NormalizedMessage:
    """Convert email JSON to NormalizedMessage"""
    return NormalizedMessage(
        id=raw.get("id", ""),
        source="email",
        person_name=raw.get("from_name", ""),
        email=raw.get("from_email"),
        company=raw.get("company"),
        timestamp=raw.get("timestamp", ""),
        subject=raw.get("subject"),
        text=raw.get("body", "")
    )


def normalize_linkedin(raw: Dict) -> NormalizedMessage:
    """Convert LinkedIn JSON to NormalizedMessage"""
    return NormalizedMessage(
        id=raw.get("id", ""),
        source="linkedin",
        person_name=raw.get("from_name", ""),
        email=raw.get("email"),
        handle=raw.get("handle"),
        company=raw.get("company"),
        timestamp=raw.get("timestamp", ""),
        subject=None,
        text=raw.get("message", "")
    )


def normalize_whatsapp(raw: Dict) -> NormalizedMessage:
    """Convert WhatsApp JSON to NormalizedMessage"""
    return NormalizedMessage(
        id=raw.get("id", ""),
        source="whatsapp",
        person_name=raw.get("from_name", ""),
        phone=raw.get("phone"),
        timestamp=raw.get("timestamp", ""),
        subject=None,
        text=raw.get("message", "")
    )


def normalize_sms(raw: Dict) -> NormalizedMessage:
    """Convert SMS JSON to NormalizedMessage"""
    return NormalizedMessage(
        id=raw.get("id", ""),
        source="sms",
        person_name=raw.get("from_name", ""),
        phone=raw.get("phone"),
        timestamp=raw.get("timestamp", ""),
        subject=None,
        text=raw.get("body", raw.get("message", ""))  
    )


def normalize_all_sources(raw_sources: Dict[str, List[Dict]]) -> List[NormalizedMessage]:
    """Normalize all messages from all sources"""
    normalized = []
    
    for msg in raw_sources.get("email", []):
        normalized.append(normalize_email(msg))
    
    for msg in raw_sources.get("linkedin", []):
        normalized.append(normalize_linkedin(msg))
    
    for msg in raw_sources.get("whatsapp", []):
        normalized.append(normalize_whatsapp(msg))
    
    for msg in raw_sources.get("sms", []):
        normalized.append(normalize_sms(msg))
    
    return normalized


def normalize_incoming(source: str, raw: Dict) -> NormalizedMessage:
    """Normalize a single incoming message based on source"""
    normalizers = {
        "email": normalize_email,
        "linkedin": normalize_linkedin,
        "whatsapp": normalize_whatsapp,
        "sms": normalize_sms
    }
    
    normalizer = normalizers.get(source)
    if not normalizer:
        raise ValueError(f"Unknown source: {source}")
    
    return normalizer(raw)