from typing import Optional
from romanian_legislation_mcp.api_consumers.document_finder import DocumentFinder
from romanian_legislation_mcp.structured_document.builder import (
    StructuredDocumentBuilder,
)
from romanian_legislation_mcp.structured_document.structured_document import (
    StructuredDocument,
)


class StructuredDocumentService:
    """Class responsible for building and in-memory caching of `StructuredDocument` instances."""

    def __init__(self, document_finder: DocumentFinder):
        """:param document_finder: The `DocumentFinder` instance to search for and retrieve legal documents."""

        self.document_finder = document_finder
        self.built_documents: list[dict] = []

    async def get_document(
        self, document_type: str, number: int, year: int, issuer: str
    ):
        """Returns a structured form of a legal document."""
        
        document = self._get_from_cache(document_type, number, year, issuer)
        if document is None:
            document = await self._build_document(document_type, number, year, issuer)

        return document

    def _get_from_cache(
        self, document_type: str, number: int, year: int, issuer: str
    ) -> Optional[StructuredDocument]:
        for document_data in self.built_documents:
            if (
                document_data["type"] == document_type
                and document_data["number"] == number
                and document_data["year"] == year
                and document_data["issuer"] == issuer
            ):
                return document_data["document"]

        return None

    async def _build_document(
        self, document_type: str, number: int, year: int, issuer: str
    ) -> Optional[StructuredDocument]:
        base_document = await self.document_finder.get_document(
            document_type, number, year, issuer
        )
        if not base_document:
            return None

        builder = StructuredDocumentBuilder(base_document)
        document = builder.create_structured_document()

        if document is not None:
            document_data = {
                "type": document_type,
                "number": number,
                "year": year,
                "issuer": issuer,
                "document": document,
            }

            self.built_documents.append(document_data)

        return document
