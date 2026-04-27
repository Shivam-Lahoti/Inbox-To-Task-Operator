from core.schemas import NormalizedMessage


def normalize_email(raw: dict) -> NormalizedMessage:
    return NormalizedMessage(
        id=raw["email_id"],
        source="email",
        person_name=raw["from_name"],
        email=raw.get("from_email"),
        phone=None,
        handle=None,
        company=None,
        timestamp=raw["timestamp"],
        subject=raw.get("subject"),
        text=raw["body"]
    )


def normalize_linkedin(raw: dict) -> NormalizedMessage:
    return NormalizedMessage(
        id=raw["linkedin_id"],
        source="linkedin",
        person_name=raw["profile_name"],
        email=None,
        phone=None,
        handle=raw.get("profile_handle"),
        company=raw.get("company"),
        timestamp=raw["timestamp"],
        subject=None,
        text=raw["message"]
    )


def normalize_whatsapp(raw: dict) -> NormalizedMessage:
    return NormalizedMessage(
        id=raw["whatsapp_id"],
        source="whatsapp",
        person_name=raw["contact_name"],
        email=None,
        phone=raw.get("phone"),
        handle=None,
        company=None,
        timestamp=raw["timestamp"],
        subject=None,
        text=raw["message"]
    )


def normalize_sms(raw: dict) -> NormalizedMessage:
    return NormalizedMessage(
        id=raw["sms_id"],
        source="sms",
        person_name=raw["contact_name"],
        email=None,
        phone=raw.get("phone"),
        handle=None,
        company=None,
        timestamp=raw["timestamp"],
        subject=None,
        text=raw["message"]
    )


def normalize_all_sources(raw_sources: dict[str, list[dict]]) -> list[NormalizedMessage]:
    normalized = []

    for item in raw_sources.get("email", []):
        normalized.append(normalize_email(item))

    for item in raw_sources.get("linkedin", []):
        normalized.append(normalize_linkedin(item))

    for item in raw_sources.get("whatsapp", []):
        normalized.append(normalize_whatsapp(item))

    for item in raw_sources.get("sms", []):
        normalized.append(normalize_sms(item))

    return normalized


def normalize_incoming(source: str, raw: dict) -> NormalizedMessage:
    if source == "email":
        return normalize_email(raw)

    if source == "linkedin":
        return normalize_linkedin(raw)

    if source == "whatsapp":
        return normalize_whatsapp(raw)

    if source == "sms":
        return normalize_sms(raw)

    raise ValueError(f"Unsupported incoming source: {source}")