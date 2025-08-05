from datetime import datetime
from dataclasses import dataclass
from typing import Optional

from romanian_legislation_mcp.document_search.document_status_parser import DocumentStatus

@dataclass
class LegislationDocument:
    title: str
    number: str
    document_type: str
    issuer: str
    effective_date: datetime
    text: str
    publication: Optional[str] = None
    url: Optional[str] = None
    status: DocumentStatus = DocumentStatus.UNKNOWN