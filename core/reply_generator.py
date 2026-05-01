from typing import Dict


def build_prompt(
    incoming_message: str,
    context: Dict,
    tone_profile: Dict
) -> str:
    """Build LLM prompt with all context"""
    
    prompt_parts = []
    
    # Incoming message
    prompt_parts.append("## INCOMING MESSAGE")
    prompt_parts.append(incoming_message)
    prompt_parts.append("")
    
    # Resolved sources
    prompt_parts.append(f"## RELATIONSHIP CONTEXT")
    prompt_parts.append(f"Person: {context['person']}")
    prompt_parts.append(f"Sources found: {', '.join(context['sources_found'])}")
    prompt_parts.append(f"Total messages: {context['total_messages']}")
    prompt_parts.append("")
    
    # Relationship history
    if context.get("relationship_history"):
        prompt_parts.append("## CONVERSATION HISTORY")
        for item in context["relationship_history"][:5]:
            prompt_parts.append(
                f"[{item['source']}] {item['timestamp']} (confidence: {item['confidence']})"
            )
            if item.get("subject"):
                prompt_parts.append(f"Subject: {item['subject']}")
            prompt_parts.append(f"{item['preview']}")
            prompt_parts.append("")
    
    # RAG context
    if context.get("rag_context"):
        prompt_parts.append("## RELEVANT CONTEXT (RAG)")
        for item in context["rag_context"][:3]:
            prompt_parts.append(
                f"[{item['source']}] {item['timestamp']} (relevance: {item['relevance']})"
            )
            prompt_parts.append(item["text"])
            prompt_parts.append("")
    
    # Open commitments
    if context.get("open_commitments"):
        prompt_parts.append("## OPEN COMMITMENTS")
        for commitment in context["open_commitments"]:
            prompt_parts.append(f"- {commitment}")
        prompt_parts.append("")
    
    # Tone profile
    prompt_parts.append("## TONE GUIDELINES")
    prompt_parts.append(f"Style: {tone_profile['style']}")
    prompt_parts.append(f"Avoid: {tone_profile['avoid']}")
    prompt_parts.append("")
    
    # Rules
    prompt_parts.append("## RULES")
    prompt_parts.append("1. Use ONLY the context provided above")
    prompt_parts.append("2. Do NOT hallucinate facts or events")
    prompt_parts.append("3. Keep reply concise (2-4 sentences)")
    prompt_parts.append("4. Match professional but warm tone")
    prompt_parts.append("5. Reference specific past conversations when relevant")
    prompt_parts.append("6. This is a DRAFT - human will review before sending")
    prompt_parts.append("")
    prompt_parts.append("Generate a reply:")
    
    return "\n".join(prompt_parts)


def generate_reply(
    incoming_message: str,
    context: Dict,
    tone_profile: Dict,
    llm_function
) -> str:
    """Generate reply using LLM"""
    from llm.llm_utils import generate_with_llm
    
    prompt = build_prompt(incoming_message, context, tone_profile)
    
    return generate_with_llm(prompt, person_name=context["person"])