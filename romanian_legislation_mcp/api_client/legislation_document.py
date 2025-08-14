from datetime import datetime
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
    changes: Optional[dict] = None
    publication: Optional[str] = None
    url: Optional[str] = None