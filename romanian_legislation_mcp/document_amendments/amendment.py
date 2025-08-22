from dataclasses import dataclass
from typing import Optional

from romanian_legislation_mcp.api_client.legislation_document import LegislationDocument
from romanian_legislation_mcp.document_model.model import DocumentPartType


@dataclass
class Amendment:
    amendment_type: str
    source_str: str
    source_url: str
    target_element_type: DocumentPartType
    target_element_no: Optional[str] = None


@dataclass
class AmendmentData:
    amendments: list[Amendment]
    is_document_repealed: bool
    document: Optional[LegislationDocument] = None

    def has_amendments(self) -> bool:
        return self.amendments is not None and len(self.amendments) > 0

    def get_count(self) -> int:
        if self.has_amendments():
            return len(self.amendments)
        else:
            return 0
