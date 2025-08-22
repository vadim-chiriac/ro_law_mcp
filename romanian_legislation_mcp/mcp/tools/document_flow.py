import logging
from typing import Dict

from romanian_legislation_mcp.structured_document.service import (
    StructuredDocumentService,
)

logger = logging.getLogger(__name__)


def register_get_document_data(app, document_service: StructuredDocumentService):
    @app.tool()
    async def get_document_data(
        document_type: str, number: int, year: int, issuer: str
    ) -> Dict | None:
        pass


def register_get_json_structure(app, document_service: StructuredDocumentService):
    """Register text search tool."""

    @app.tool()
    async def content_search(
        document_type: str,
        number: int,
        year: int,
        issuer: str,
    ) -> dict:
        """ """

        document = await document_service.get_document(
            document_type, number, year, issuer
        )
        if document is None:
            pass
