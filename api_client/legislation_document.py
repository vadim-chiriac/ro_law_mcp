from datetime import datetime
from dataclasses import dataclass
from typing import Optional

@dataclass
class LegislationDocument:
    title: str
    number: str
    type: str
    emitter: str
    effective_date: datetime
    text: str
    publication: Optional[str] = None

doc = LegislationDocument(
    title="Some law about contracts", 
    number="123",
    type="LEGE",
    emitter="Parlament", 
    effective_date=datetime(2023, 1, 15),
    text="Article 1. This law says...",
    publication="Monitorul Oficial"
)

print(doc)
print(f"Title: {doc.title}")
print(f"Date: {doc.effective_date}")