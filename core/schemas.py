from dataclasses import dataclass
from typing import Optional


@dataclass
class NormalizedMessage:
    """Common schema for messages across all platforms"""
    id: str
    source: str  # email, linkedin, whatsapp, sms
    person_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    handle: Optional[str] = None
    company: Optional[str] = None
    timestamp: str = ""
    subject: Optional[str] = None
    text: str = ""

    def __repr__(self):
        return (
            f"NormalizedMessage(id={self.id}, source={self.source}, "
            f"person={self.person_name}, email={self.email})"
        )