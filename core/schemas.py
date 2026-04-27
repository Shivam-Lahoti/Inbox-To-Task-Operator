from dataclasses import dataclass
from typing import Optional


@dataclass
class NormalizedMessage:
    id: str
    source: str
    person_name: str
    email: Optional[str]
    phone: Optional[str]
    handle: Optional[str]
    company: Optional[str]
    timestamp: str
    subject: Optional[str]
    text: str