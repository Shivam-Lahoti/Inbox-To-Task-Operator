def classify_email(email: dict, summary: str) -> dict:
    """
    Classify an email into priority, intent, action_required, and confidence.
    This is rule-based for the MVP and can later be replaced by an LLM.
    """
    subject = email.get("subject", "").lower()
    body = email.get("body", "").lower()
    sender = email.get("from", "").lower()
    text = f"{subject} {body} {summary.lower()}"

    priority = "MEDIUM"
    intent = "general"
    action_required = False
    confidence = 0.75

    # Newsletters / informational
    if "newsletter" in text or "weekly update" in text or "unsubscribe" in text:
        intent = "newsletter"
        priority = "LOW"
        action_required = False
        confidence = 0.95

    # Scheduling / recruiter
    elif (
        "interview" in text
        or "availability" in text
        or "schedule" in text
        or "calendar" in text
        or "recruiter" in sender
    ):
        intent = "scheduling"
        priority = "HIGH"
        action_required = True
        confidence = 0.92

    # Urgent / escalation
    elif "urgent" in text or "asap" in text or "today" in text or "immediately" in text:
        intent = "escalation"
        priority = "HIGH"
        action_required = True
        confidence = 0.90

    # Follow-up
    elif "follow up" in text or "following up" in text:
        intent = "follow_up"
        priority = "MEDIUM"
        action_required = True
        confidence = 0.85

    # Information / document request
    elif (
        "share" in text
        or "send" in text
        or "document" in text
        or "details" in text
        or "information" in text
    ):
        intent = "information_request"
        priority = "MEDIUM"
        action_required = True
        confidence = 0.82

    # FYI / passive notifications
    elif "for your information" in text or "fyi" in text:
        intent = "notification"
        priority = "LOW"
        action_required = False
        confidence = 0.88

    # Reduce confidence if content is too vague
    if len(body.strip()) < 10:
        confidence = min(confidence, 0.60)

    return {
        "priority": priority,
        "intent": intent,
        "action_required": action_required,
        "confidence": confidence,
    }