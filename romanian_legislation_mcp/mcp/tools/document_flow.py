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
        """"""
        return await document_service.get_document_data(document_type, number, year, issuer)


def register_get_json_structure(app, document_service: StructuredDocumentService):
    """Register text search tool."""

    @app.tool()
    async def get_json_structure(id: str) -> dict:
        """ """

        document = await document_service.get_document_by_id(id)
        if document is None:
            return {"error":"Document with {id} not found."}

        return document.get_json_structure()            
