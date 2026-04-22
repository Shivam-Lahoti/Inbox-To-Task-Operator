import os

from dotenv import load_dotenv

load_dotenv()

USE_REAL_LLM = os.getenv("USE_REAL_LLM", "false").lower() == "true"


def summarize_email(email: dict) -> str:
    """
    Use a real LLM if enabled, otherwise fall back to a rule-based summarizer.
    """
    if USE_REAL_LLM:
        try:
            return _summarize_with_llm(email)
        except Exception as e:
            print(f"[LLM fallback] Failed to use real LLM: {e}")
            return _summarize_rule_based(email)

    return _summarize_rule_based(email)


def _summarize_with_llm(email: dict) -> str:
    """
    Real LLM-based summarization using OpenAI.
    """
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in environment variables.")

    client = OpenAI(api_key=api_key)

    subject = email.get("subject", "").strip()
    body = email.get("body", "").strip()

    prompt = f"""
Summarize the following email in one concise sentence.
Focus on the sender's intent and any action requested.

Subject: {subject}
Body: {body}
""".strip()

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a concise assistant that summarizes emails clearly."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()


def _summarize_rule_based(email: dict) -> str:
    """
    Lightweight rule-based summarizer for fallback / deterministic testing.
    """
    subject = email.get("subject", "").strip()
    body = email.get("body", "").strip()

    combined = f"{subject}. {body}".strip()

    if not combined:
        return "No meaningful content found."

    text = combined.lower()

    if "interview" in text or "availability" in text or "schedule" in text:
        return "Sender is asking to coordinate availability or schedule a meeting."
    if "newsletter" in text or "weekly update" in text or "shipped this week" in text:
        return "This is an informational newsletter or product update."
    if "urgent" in text or "asap" in text or "today" in text:
        return "Sender is requesting an urgent update or action."
    if "follow up" in text or "following up" in text:
        return "Sender is following up on a previous conversation."
    if "document" in text or "send" in text or "share" in text:
        return "Sender is requesting information or a document."

    trimmed = combined[:180].strip()
    return trimmed + ("..." if len(combined) > 180 else "")


def generate_reply(email: dict, summary: str, task: dict) -> str:
    """
    Generate a simple contextual reply draft.
    """
    action = task.get("action", "respond")
    context = task.get("context", "").lower()

    if action == "provide_availability":
        return (
            "Hi,\n\n"
            "Thanks for reaching out. I'm available Thursday between 2–5 PM PST "
            "and Friday between 10 AM–1 PM PST. Please let me know what works best.\n\n"
            "Best,\nShivam"
        )

    if action == "send_information":
        return (
            "Hi,\n\n"
            "Thanks for your email. I’m sharing the requested information shortly.\n\n"
            "Best,\nShivam"
        )

    if "urgent" in summary.lower() or "urgent" in context or "project update" in context:
        return (
            "Hi,\n\n"
            "Thanks for flagging this. I’m reviewing the current status and will send "
            "a clear update with timeline shortly.\n\n"
            "Best,\nShivam"
        )

    if "follow up" in summary.lower():
        return (
            "Hi,\n\n"
            "Thanks for following up. I’ve reviewed your message and will get back to you shortly.\n\n"
            "Best,\nShivam"
        )

    return (
        "Hi,\n\n"
        "Thanks for your email. I’ve reviewed your message and will get back to you shortly.\n\n"
        "Best,\nShivam"
    )