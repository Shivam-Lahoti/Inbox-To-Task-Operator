from difflib import SequenceMatcher
from typing import List, Tuple
from core.schemas import NormalizedMessage


# Auto-learning contact database
_contact_db = None


def get_contact_db():
    """Get or create contact database singleton"""
    global _contact_db
    if _contact_db is None:
        _contact_db = ContactDatabase()
    return _contact_db


class ContactDatabase:
    """Auto-learning contact database from message history"""
    
    def __init__(self):
        self.contacts = {}  # identifier -> contact info
        self._build_from_history()
    
    def _build_from_history(self):
        """Build contact database from existing message history"""
        from core.source_loader import load_all_sources
        from core.normalizer import normalize_all_sources
        
        try:
            raw_sources = load_all_sources()
            all_messages = normalize_all_sources(raw_sources)
            
            # Group messages by person name
            person_data = {}
            
            for msg in all_messages:
                key = msg.person_name.lower().strip()
                
                # Skip invalid keys
                if not key or key in ["", "unknown"]:
                    continue
                
                if key not in person_data:
                    person_data[key] = {
                        "name": msg.person_name,
                        "emails": set(),
                        "phones": set(),
                        "companies": set()
                    }
                
                if msg.email:
                    person_data[key]["emails"].add(msg.email.lower())
                if msg.phone:
                    person_data[key]["phones"].add(msg.phone)
                if msg.company:
                    person_data[key]["companies"].add(msg.company)
            
            # Build cross-reference lookup maps
            for person_info in person_data.values():
                identifiers = list(person_info["emails"]) + list(person_info["phones"])
                
                for identifier in identifiers:
                    self.contacts[identifier] = {
                        "name": person_info["name"],
                        "emails": list(person_info["emails"]),
                        "phones": list(person_info["phones"]),
                        "companies": list(person_info["companies"])
                    }
            
            print(f"✅ Contact database: {len(self.contacts)} identifiers linked")
        
        except Exception as e:
            print(f"⚠️  Contact database build failed: {e}")
    
    def enrich(self, message: NormalizedMessage) -> NormalizedMessage:
        """Enrich message with cross-channel contact data"""
        
        # Try lookup by email
        if message.email:
            lookup_key = message.email.lower()
            if lookup_key in self.contacts:
                contact = self.contacts[lookup_key]
                
                # Add phone if missing
                if not message.phone and contact["phones"]:
                    message.phone = contact["phones"][0]
                
                # Use proper name if currently using email/phone as name
                if message.person_name in [message.email, message.phone, lookup_key]:
                    message.person_name = contact["name"]
                
                return message
        
        # Try lookup by phone
        if message.phone:
            if message.phone in self.contacts:
                contact = self.contacts[message.phone]
                
                # Add email if missing
                if not message.email and contact["emails"]:
                    message.email = contact["emails"][0]
                
                # Use proper name if currently using phone as name
                if message.person_name == message.phone:
                    message.person_name = contact["name"]
                
                return message
        
        return message


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
    
    Auto-enriches messages with cross-channel contact data before matching.
    
    Returns: List of (message, confidence_score, reasons)
    """
    
    # Auto-enrich with contact database
    db = get_contact_db()
    incoming = db.enrich(incoming)
    all_messages = [db.enrich(msg) for msg in all_messages]
    
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