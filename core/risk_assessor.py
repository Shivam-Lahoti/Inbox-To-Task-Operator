"""
Risk assessment for incoming messages to determine auto-send safety
"""

from typing import Dict, Tuple
from core.schemas import NormalizedMessage


# High-risk keywords that require manual review
HIGH_RISK_KEYWORDS = [
    # Financial
    "salary", "compensation", "offer letter", "contract", "payment", "invoice",
    "wire transfer", "account number", "routing number", "ssn", "social security",
    
    # Legal
    "legal", "lawsuit", "attorney", "lawyer", "court", "litigation", "terminate",
    "termination", "resign", "resignation", "nda", "non-disclosure",
    
    # Critical business
    "urgent", "immediate action", "final notice", "deadline today", "expires",
    "account suspended", "verify your account", "reset password",
    
    # Interview/Job
    "job offer", "offer letter", "background check", "start date", "onboarding",
    "equity", "stock options", "benefits package"
]

# Medium-risk keywords that need buffer time
MEDIUM_RISK_KEYWORDS = [
    "meeting", "schedule", "calendar", "interview", "call", "zoom",
    "available", "availability", "free", "busy", "appointment"
]

# High-risk domains
HIGH_RISK_DOMAINS = [
    "bank.com", "chase.com", "wellsfargo.com", "bofa.com",
    "irs.gov", "gov", "court", "legal"
]


def assess_message_risk(
    message: NormalizedMessage,
    identity_confidence: float,
    sources_found: list
) -> Tuple[str, list]:
    """
    Assess risk level of a message
    
    Returns:
        Tuple of (risk_level, reasons)
        risk_level: "LOW", "MEDIUM", or "HIGH"
        reasons: List of reasons for the risk level
    """
    
    risk_score = 0
    reasons = []
    
    # Factor 1: Identity confidence
    if identity_confidence < 0.6:
        risk_score += 30
        reasons.append("Unknown sender (low confidence)")
    elif identity_confidence < 0.8:
        risk_score += 15
        reasons.append("New contact (medium confidence)")
    else:
        reasons.append("Known contact (high confidence)")
    
    # Factor 2: Check for high-risk keywords
    text_lower = message.text.lower()
    subject_lower = (message.subject or "").lower()
    combined_text = f"{text_lower} {subject_lower}"
    
    high_risk_found = []
    for keyword in HIGH_RISK_KEYWORDS:
        if keyword in combined_text:
            high_risk_found.append(keyword)
    
    if high_risk_found:
        risk_score += 50
        reasons.append(f"High-risk keywords: {', '.join(high_risk_found[:3])}")
    
    # Factor 3: Check for medium-risk keywords
    medium_risk_found = []
    for keyword in MEDIUM_RISK_KEYWORDS:
        if keyword in combined_text and not high_risk_found:
            medium_risk_found.append(keyword)
    
    if medium_risk_found:
        risk_score += 20
        reasons.append(f"Scheduling/meeting keywords: {', '.join(medium_risk_found[:2])}")
    
    # Factor 4: Email domain check
    if message.email:
        domain = message.email.split('@')[-1].lower()
        for risky_domain in HIGH_RISK_DOMAINS:
            if risky_domain in domain:
                risk_score += 40
                reasons.append(f"High-risk domain: {domain}")
                break
    
    # Factor 5: No conversation history
    if len(sources_found) <= 1:
        risk_score += 10
        reasons.append("No prior conversation history")
    
    # Factor 6: Message length (very short = likely simple, low risk)
    if len(message.text.split()) < 15 and risk_score < 30:
        risk_score -= 10
        reasons.append("Short casual message")
    
    # Determine final risk level
    if risk_score >= 50:
        return "HIGH", reasons
    elif risk_score >= 25:
        return "MEDIUM", reasons
    else:
        return "LOW", reasons


def should_auto_send(risk_level: str) -> Tuple[bool, int]:
    """
    Determine if message should auto-send and buffer time
    
    Returns:
        Tuple of (should_send, buffer_seconds)
    """
    
    if risk_level == "LOW":
        return True, 0  # Send immediately
    elif risk_level == "MEDIUM":
        return True, 10  # Send after 10 second buffer
    else:  # HIGH
        return False, 0  # Don't auto-send, create draft only


def format_risk_summary(risk_level: str, reasons: list) -> str:
    """Format risk assessment for display"""
    
    emoji_map = {
        "LOW": "🟢",
        "MEDIUM": "🟡",
        "HIGH": "🔴"
    }
    
    summary = f"{emoji_map[risk_level]} Risk Level: {risk_level}\n"
    summary += "Reasons:\n"
    for reason in reasons:
        summary += f"  • {reason}\n"
    
    return summary