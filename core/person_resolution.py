from difflib import SequenceMatcher
from typing import List, Tuple
from core.schemas import NormalizedMessage


def similarity(a: str | None, b: str | None) -> float:
    """Calculate string similarity ratio"""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def email_domain(email: str | None) -> str | None:
    """Extract domain from email"""
    if not email or "@" not in email:
        return None
    return email.split("@")[-1].lower()


def resolve_person(
    incoming: NormalizedMessage,
    all_messages: List[NormalizedMessage]
) -> List[Tuple[NormalizedMessage, float, List[str]]]:
    """
    Resolve which historical messages belong to the same person as incoming message.
    
    Returns: List of (message, confidence_score, reasons)
    """
    matches = []
    
    for msg in all_messages:
        score = 0.0
        reasons = []
        
        # Strong identity signals
        if incoming.email and msg.email and incoming.email.lower() == msg.email.lower():
            score += 1.0
            reasons.append("same email")
        
        if incoming.phone and msg.phone and incoming.phone == msg.phone:
            score += 1.0
            reasons.append("same phone")
        
        if incoming.handle and msg.handle and incoming.handle.lower() == msg.handle.lower():
            score += 0.9
            reasons.append("same handle")
        
        # Medium signals
        if incoming.company and msg.company and incoming.company.lower() == msg.company.lower():
            score += 0.45
            reasons.append("same company")
        
        incoming_domain = email_domain(incoming.email)
        msg_domain = email_domain(msg.email)
        
        if incoming_domain and msg_domain and incoming_domain == msg_domain:
            score += 0.35
            reasons.append("same email domain")
        
        # Weak signal - name similarity
        name_score = similarity(incoming.person_name, msg.person_name)
        
        if name_score >= 0.9:
            score += 0.25
            reasons.append("same or very similar name")
        elif name_score >= 0.65:
            score += 0.15
            reasons.append("partially similar name")
        
        # Only include if we have strong identity signal
        strong_identity_signal = any(
            reason in reasons
            for reason in [
                "same email",
                "same phone",
                "same handle",
                "same company",
                "same email domain"
            ]
        )
        
        if score >= 0.55 and strong_identity_signal:
            matches.append((msg, round(score, 2), reasons))
    
    return sorted(matches, key=lambda x: x[1], reverse=True)