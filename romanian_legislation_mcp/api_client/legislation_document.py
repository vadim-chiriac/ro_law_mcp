from datetime import datetime
from dataclasses import dataclass
from typing import Optional

@dataclass
class LegislationDocument:
    title: str
    number: str
    document_type: str
    issuer: str
    effective_date: datetime
    text: str
    status: dict
    publication: Optional[str] = None
    url: Optional[str] = None