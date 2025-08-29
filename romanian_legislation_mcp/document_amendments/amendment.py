from dataclasses import dataclass
from typing import Optional

from romanian_legislation_mcp.structured_document.element import DocumentElementType


@dataclass
class Amendment:
    """Represents metadata about a further amendment made to a legal document."""
    
    amendment_type: str
    source_str: str
    source_url: str
    target_element_type: DocumentElementType
    target_element_no: Optional[str] = None


@dataclass
class AmendmentData:
    """Represents metadata about all amendments made to a legal document."""
    
    amendments: list[Amendment]
    is_document_repealed: bool
