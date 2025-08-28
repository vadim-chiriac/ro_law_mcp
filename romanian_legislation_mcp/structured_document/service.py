import json
from typing import Dict
import uuid
from romanian_legislation_mcp.api_consumers.document_finder import DocumentFinder
from romanian_legislation_mcp.structured_document.builder import (
    StructuredDocumentBuilder,
)
from romanian_legislation_mcp.structured_document.structured_document import (
    StructuredDocument,
)


class StructuredDocumentService:
    def __init__(self, document_finder: DocumentFinder):
        self.document_finder = document_finder
        self.documents: Dict[str, StructuredDocument] = {}

    async def get_document_data(
        self, document_type: str, number: int, year: int, issuer: str
    ):
        document = await self._get_document(document_type, number, year, issuer)
        if document is None:
            print(f"Found none!")
            return None
        
        id = str(document.top_element.id)
        print(f"Id: {id}")
        self.documents[id] = document
        data = {
            "id": id,
            "document_type": document.base_document.document_type,
            "title": document.base_document.title,
            "issuer": document.base_document.issuer,
            "content_length": len(document.base_document.text),
            "article_count": len(document.articles),
            "max_depth": document.top_element.max_depth,
            "top_level_structure": document.get_element_structure(id),
            "structural_amendment_data": document.get_structural_amendment_data(),
        }
        structure = json.dumps(data).replace("'", "\"")
    
        with open("example.json", "w") as f:
            f.write(structure)
        
        return data
    
    async def get_document_by_id(self, id: str):
        print(f"Getting by id {id}")
        return self.documents.get(id, None)

    async def _get_document(
        self, document_type: str, number: int, year: int, issuer: str
    ):
        base_document = await self.document_finder.get_document(
            document_type, number, year, issuer
        )
        if not base_document:
            return None

        builder = StructuredDocumentBuilder(base_document)
        document = builder.create_structured_document()

        return document
