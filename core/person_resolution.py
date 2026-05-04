import re
from difflib import SequenceMatcher
from typing import List, Tuple, Optional
from core.schemas import NormalizedMessage


_contact_db = None


def extract_name_from_text(text: str) -> Optional[str]:
    """Extract name from phrases like 'This is John' or 'It's Sarah here'"""
    
    print(f"[NAME_EXTRACT] Trying to extract name from: '{text[:100]}'")
    print(f"[NAME_EXTRACT] Text repr: {repr(text[:100])}")  # See exact characters
    
    patterns = [
        r"(?:this|this)\s+is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"(?:it'?s|its)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"(?:i'?m|im)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"(?:my\s+name\s+is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+here",
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+from"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)  # Add case-insensitive flag
        if match:
            name = match.group(1).strip()
            # Capitalize properly
            name = ' '.join(word.capitalize() for word in name.split())
            
            if len(name) > 2 and name.lower() not in ["hey", "hello", "hi", "the", "this", "that"]:
                print(f"[NAME_EXTRACT] SUCCESS: Extracted '{name}' using pattern '{pattern}'")
                return name
    
    print(f"[NAME_EXTRACT] FAILED: No name found")
    return None


def reload_contact_db():
    """Force reload of contact database"""
    global _contact_db
    _contact_db = None
    return get_contact_db()


def get_contact_db():
    """Get or create contact database singleton"""
    global _contact_db
    if _contact_db is None:
        _contact_db = ContactDatabase()
    return _contact_db


class ContactDatabase:
    """Auto-learning contact database from message history"""
    
    def __init__(self):
        self.contacts = {}
        self._build_from_history()
    
    def _build_from_history(self):
        """Build contact database from existing message history"""
        from core.source_loader import load_all_sources
        from core.normalizer import normalize_all_sources
        
        try:
            raw_sources = load_all_sources()
            all_messages = normalize_all_sources(raw_sources)
            
            person_data = {}
            
            for msg in all_messages:
                key = msg.person_name.lower().strip()
                
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
            
            for person_info in person_data.values():
                identifiers = list(person_info["emails"]) + list(person_info["phones"])
                
                for identifier in identifiers:
                    self.contacts[identifier] = {
                        "name": person_info["name"],
                        "emails": list(person_info["emails"]),
                        "phones": list(person_info["phones"]),
                        "companies": list(person_info["companies"])
                    }
        
        except Exception as e:
            pass
    
    def enrich(self, message: NormalizedMessage) -> NormalizedMessage:
        """Enrich message with cross-channel contact data using multi-signal matching"""
        
        # Extract name from SMS text if needed
        if message.source in ["sms", "whatsapp"] and message.person_name == message.phone:
            print(f"[ENRICH] Attempting name extraction for {message.phone}")
            extracted_name = extract_name_from_text(message.text)
            if extracted_name:
                message.person_name = extracted_name
                print(f"[ENRICH] Updated person_name to: '{extracted_name}'")
            else:
                print(f"[ENRICH] No name extracted, keeping phone as name")
        
        # Try exact identifier match first (strongest signal)
        if message.email:
            lookup_key = message.email.lower()
            if lookup_key in self.contacts:
                contact = self.contacts[lookup_key]
                
                if not message.phone and contact["phones"]:
                    message.phone = contact["phones"][0]
                
                if message.person_name in [message.email, message.phone, lookup_key]:
                    message.person_name = contact["name"]
                
                print(f"[ENRICH] Matched by email: {message.person_name}")
                return message
        
        if message.phone:
            if message.phone in self.contacts:
                contact = self.contacts[message.phone]
                
                if not message.email and contact["emails"]:
                    message.email = contact["emails"][0]
                
                if message.person_name == message.phone:
                    message.person_name = contact["name"]
                
                print(f"[ENRICH] Matched by phone: {message.person_name}")
                return message
        
        # Fuzzy name match ONLY if exactly ONE match (prevents wrong-person linking)
        if message.person_name and message.person_name not in [message.email, message.phone]:
            matches = []
            
            for identifier, contact in self.contacts.items():
                msg_name_lower = message.person_name.lower()
                contact_name_lower = contact["name"].lower()
                
                # Check partial match
                is_partial = (
                    msg_name_lower in contact_name_lower or 
                    contact_name_lower in msg_name_lower
                )
                
                # Check similarity
                name_sim = similarity(message.person_name, contact["name"])
                
                if is_partial or name_sim > 0.70:
                    matches.append((identifier, contact, name_sim))
            
            # ONLY link if exactly ONE match found
            if len(matches) == 1:
                identifier, contact, score = matches[0]
                if not message.email and contact["emails"]:
                    message.email = contact["emails"][0]
                if not message.phone and contact["phones"]:
                    message.phone = contact["phones"][0]
                message.person_name = contact["name"]
                print(f"[CONTACT_MATCH] Linked '{message.person_name}' via name (confidence: {score:.2f})")
            
            elif len(matches) > 1:
                print(f"[CONTACT_MATCH] Multiple matches for '{message.person_name}' - skipping to avoid wrong-person link")
            
            elif len(matches) == 0:
                print(f"[ENRICH] No matches found for '{message.person_name}'")
        
        return message

def similarity(a: str, b: str) -> float:
    """Calculate string similarity ratio"""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def email_domain(email: str) -> str:
    """Extract domain from email"""
    if not email or "@" not in email:
        return None
    return email.split("@")[-1].lower()


def resolve_person(
    incoming: NormalizedMessage,
    all_messages: List[NormalizedMessage]
) -> List[Tuple[NormalizedMessage, float, List[str]]]:
    """Resolve which historical messages belong to the same person"""
    
    db = get_contact_db()
    incoming = db.enrich(incoming)
    all_messages = [db.enrich(msg) for msg in all_messages]
    
    matches = []
    
    for msg in all_messages:
        score = 0.0
        reasons = []
        
        if incoming.email and msg.email and incoming.email.lower() == msg.email.lower():
            score += 1.0
            reasons.append("same email")
        
        if incoming.phone and msg.phone and incoming.phone == msg.phone:
            score += 1.0
            reasons.append("same phone")
        
        if incoming.handle and msg.handle and incoming.handle.lower() == msg.handle.lower():
            score += 0.9
            reasons.append("same handle")
        
        if incoming.company and msg.company and incoming.company.lower() == msg.company.lower():
            score += 0.45
            reasons.append("same company")
        
        incoming_domain = email_domain(incoming.email)
        msg_domain = email_domain(msg.email)
        
        if incoming_domain and msg_domain and incoming_domain == msg_domain:
            score += 0.35
            reasons.append("same email domain")
        
        name_score = similarity(incoming.person_name, msg.person_name)
        
        if name_score >= 0.9:
            score += 0.25
            reasons.append("same or very similar name")
        elif name_score >= 0.65:
            score += 0.15
            reasons.append("partially similar name")
        
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