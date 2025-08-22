from typing import Dict
from romanian_legislation_mcp.api_consumers.document_finder import DocumentFinder
from romanian_legislation_mcp.structured_document.builder import StructuredDocumentBuilder
from romanian_legislation_mcp.structured_document.structured_document import StructuredDocument


class StructuredDocumentService:
    def __init__(self, document_finder: DocumentFinder):
        self.document_finder = document_finder
        self.documents: Dict[str, StructuredDocument] = {}

    async def get_document(self, document_type: str, number: int, year: int, issuer: str):
        id = f"{document_type} {number}/{year} {issuer}"
        if self.documents.get(id, None) is not None:
            return self.documents[id]
        
        base_document = await self.document_finder.get_document(document_type, number, year, issuer)
        if not base_document:
            return None
        
        builder = StructuredDocumentBuilder(base_document)
        document = builder.create_structured_document()
        
        self.documents[id] = document
        return document
