def decide_action(classification: dict) -> str:
    """
    Decide how the system should handle an email.

    Returns one of:
    - AUTO
    - DRAFT
    - ESCALATE
    """
    priority = classification.get("priority", "MEDIUM")
    action_required = classification.get("action_required", False)
    confidence = classification.get("confidence", 0.0)
    intent = classification.get("intent", "general")

    # Low confidence should always go to human review
    if confidence < 0.65:
        return "ESCALATE"

    # Low priority and no action needed can be automated
    if priority == "LOW" and not action_required:
        return "AUTO"

    # High priority scheduling/recruiter type emails can be drafted for approval
    if priority == "HIGH" and intent == "scheduling":
        return "DRAFT"

    # High priority escalations should go to human
    if priority == "HIGH":
        return "ESCALATE"

    # Medium priority emails that need action get a draft
    if priority == "MEDIUM" and action_required:
        return "DRAFT"

    # Default fallback (fail-safe approach)
    return "ESCALATE"