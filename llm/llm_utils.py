import os
from dotenv import load_dotenv

load_dotenv()


def fallback_reply(prompt: str, person_name: str | None = None) -> str:
    """
    Deterministic fallback so the demo never breaks.
    Uses dynamic person name if available.
    """

    name = person_name.split()[0] if person_name else "there"

    return (
        f"Hi {name},\n\n"
        "Thanks for reaching out. Yes, that works for me. "
        "The role sounds aligned with my backend and AI systems experience.\n\n"
        "Happy to connect and discuss further.\n\n"
        "Best,\n"
        "Shivam"
    )


def generate_with_provider(prompt: str) -> str:
    """
    Generic LLM provider call.
    Currently uses OpenAI under the hood,
    but intentionally abstracted for extensibility.
    """

    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    if not api_key:
        raise ValueError("Missing API key")

    client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": (
                    "You are a relationship-aware reply operator. "
                    "Generate concise, professional replies using only provided context. "
                    "Do not hallucinate. Do not auto-send."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
        max_output_tokens=350
    )

    return response.output_text.strip()


def generate_with_llm(prompt: str, person_name: str | None = None) -> str:
    try:
        return generate_with_provider(prompt)

    except Exception as error:
        print(f"[LLM fallback activated] {type(error).__name__}: {error}")
        return fallback_reply(prompt, person_name)