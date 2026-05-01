import os
from dotenv import load_dotenv

load_dotenv()


def fallback_reply(prompt: str, person_name: str | None = None) -> str:
    """Fallback reply if LLM fails"""
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
    """Generate reply using Anthropic Claude"""
    import anthropic
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    
    if not api_key:
        raise ValueError("Missing ANTHROPIC_API_KEY in .env file")
    
    client = anthropic.Anthropic(api_key=api_key)
    
    response = client.messages.create(
        model=model,
        max_tokens=300,
        temperature=0.3,
        messages=[
            {
                "role": "user",
                "content": (
                    "You are a relationship-aware reply operator. "
                    "Generate concise, professional replies using only provided context. "
                    "Do not hallucinate. Do not auto-send.\n\n"
                    f"{prompt}"
                )
            }
        ]
    )
    
    return response.content[0].text.strip()


def generate_with_llm(prompt: str, person_name: str | None = None) -> str:
    """Generate reply with fallback"""
    try:
        return generate_with_provider(prompt)
    
    except Exception as error:
        print(f"\n⚠️  [LLM fallback activated] {type(error).__name__}: {error}")
        return fallback_reply(prompt, person_name)