from datetime import datetime
from dataclasses import dataclass
from typing import Optional

@dataclass
class LegislationDocument:
    title: str
    number: str
    type: str
    issuer: str
    effective_date: datetime
    text: str
    publication: Optional[str] = None