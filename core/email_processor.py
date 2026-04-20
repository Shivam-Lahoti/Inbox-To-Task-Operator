from llm.llm_utils import summarize_email, generate_reply
from core.classifier import classify_email
from core.task_extractor import extract_task
from core.policy_engine import decide_action
from core.executor import execute_action
from utils.helpers import print_kv_block


def process_email(email: dict) -> dict:
    """
    Full pipeline for processing a single email.
    """

    email_id = email.get("id", "unknown")

    summary = summarize_email(email)

    classification = classify_email(email, summary)

    task = extract_task(email, summary, classification)

    mode = decide_action(classification)

    draft = None
    if mode in ["DRAFT", "ESCALATE"]:
        draft = generate_reply(email, summary, task)

    status = execute_action(
        email=email,
        summary=summary,
        classification=classification,
        task=task,
        mode=mode,
        draft=draft,
    )

    #output
    print_kv_block({
        "Email ID": email_id,
        "Summary": summary,
        "Priority": classification.get("priority"),
        "Intent": classification.get("intent"),
        "Action Required": classification.get("action_required"),
        "Mode": mode,
        "Task": task.get("action"),
        "Status": status,
    })

    return {
        "email_id": email_id,
        "summary": summary,
        "priority": classification.get("priority"),
        "intent": classification.get("intent"),
        "task": task,
        "mode": mode,
        "status": status,
    }