from llm.llm_utils import generate_with_llm


def build_reply_prompt(
    incoming_message,
    aggregated_context: dict,
    tone_profile: dict
) -> str:
    relationship_history = format_relationship_history(
        aggregated_context["relationship_history"]
    )

    rag_context = format_rag_context(
        aggregated_context["rag_context"]
    )

    open_commitments = "\n".join(
        f"- {item}" for item in aggregated_context["open_commitments"]
    )

    return f"""
You are a cross-channel relationship-aware reply operator.

Your job:
Generate a reply to the incoming message using relationship context from email, LinkedIn, WhatsApp, and SMS.

Incoming message:
Source: {incoming_message.source}
From: {incoming_message.person_name}
Text: {incoming_message.text}

Resolved sources:
{aggregated_context["sources_found"]}

Relationship history:
{relationship_history}

RAG retrieved context:
{rag_context}

Open commitments:
{open_commitments}

Tone profile:
Style: {tone_profile["style"]}
Avoid: {tone_profile["avoid"]}

Rules:
- Do not hallucinate facts.
- Use only provided context.
- Keep reply concise.
- Match user's professional tone.
- Do not auto-send.
"""


def format_relationship_history(history: list[dict]) -> str:
    lines = []

    for item in history:
        lines.append(
            f"- [{item['timestamp']}] {item['source']} | {item['person_name']}: {item['text']}"
        )

    return "\n".join(lines)


def format_rag_context(results: list[dict]) -> str:
    lines = []

    for item in results:
        lines.append(
            f"- Score {item['rag_score']} | {item['source']} | {item['timestamp']}: {item['text']}"
        )

    return "\n".join(lines)


def generate_reply(
    incoming_message,
    aggregated_context: dict,
    tone_profile: dict
) -> str:
    prompt = build_reply_prompt(
        incoming_message,
        aggregated_context,
        tone_profile
    )

    return generate_with_llm(
        prompt=prompt,
        person_name=incoming_message.person_name
     person_name=incoming_message.person_name
)