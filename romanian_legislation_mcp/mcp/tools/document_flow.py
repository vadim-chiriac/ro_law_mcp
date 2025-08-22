import logging

from romanian_legislation_mcp.structured_document.service import (
    StructuredDocumentService,
)

logger = logging.getLogger(__name__)


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

        return await _execute_simple_search(
            search_service.search_content, query, max_results, "Text search"
        )
