from dataclasses import dataclass
from typing import Optional


@dataclass
class LegislationDocument:
    title: str
    number: str
    document_type: str
    issuer: str
    effective_date: str
    text: str
    publication: Optional[str] = None
    url: Optional[str] = None
