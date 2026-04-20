def extract_task(email: dict, summary: str, classification: dict) -> dict:
    """
    Convert an email into a structured task representation.
    """
    subject = email.get("subject", "").lower()
    body = email.get("body", "").lower()
    text = f"{subject} {body} {summary.lower()}"

    intent = classification.get("intent", "general")
    action_required = classification.get("action_required", False)

    task_type = "no_action"
    action = "none"
    context = summary
    deadline = None

    if not action_required:
        return {
            "task_type": task_type,
            "action": action,
            "context": context,
            "deadline": deadline,
        }

    if intent == "scheduling":
        task_type = "reply"
        action = "provide_availability"
        context = "meeting or interview scheduling"

    elif intent == "information_request":
        task_type = "reply"
        action = "send_information"
        context = "sender is requesting details or documents"

    elif intent == "follow_up":
        task_type = "reply"
        action = "respond_to_follow_up"
        context = "sender is following up on an earlier thread"

    elif intent == "escalation":
        task_type = "review_and_reply"
        action = "prepare_status_update"
        context = "urgent or high-priority request requiring careful response"

    else:
        task_type = "reply"
        action = "respond"
        context = "general response required"

    # deadline detection
    if "today" in text:
        deadline = "today"
    elif "tomorrow" in text:
        deadline = "tomorrow"
    elif "asap" in text:
        deadline = "asap"

    return {
        "task_type": task_type,
        "action": action,
        "context": context,
        "deadline": deadline,
    }