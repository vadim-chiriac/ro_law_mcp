import logging
from typing import Optional
from mcp.server.fastmcp import FastMCP

from romanian_legislation_mcp.document_search.search_service import SearchService

logger = logging.getLogger(__name__)

search_service = None


def register_tools(app: FastMCP, service: SearchService):
    """Register available tools with the MCP server"""
    global search_service
    search_service = service

    register_health_check(app)
    register_content_search(app)
    register_title_search(app)
    register_number_search(app)
    register_document_search(app)

    logger.info("All MCP tools registered successfully.")


def register_health_check(app):
    """Register health check tool"""

    @app.tool()
    def health_check() -> dict:
        """Checks if the server is running and ready to serve requests

        :return: A dictionary with server status and availability
        """
        try:
            if search_service is None:
                return {
                    "status": "unhealthy",
                    "message": "Search service is not initialized",
                }

            return {
                "status": "healthy",
                "message": "Search service is ready",
            }

        except Exception as e:
            logger.error(f"Health check failed {e}")
            return {"status": "error", "message": str(e)}


def register_content_search(app):
    """Register text search tool."""

    @app.tool()
    async def search_content(query: str, max_results: Optional[int] = None) -> dict:
        """Search contents of legislation documents.

        Args:
            query: Search query
            max_results: Maximum number of results to return (optional, defaults to 10)
        """

        return await _execute_simple_search(
            search_service.search_content, query, max_results, "Text search"
        )


def register_title_search(app):
    """Register the title search tool."""

    @app.tool()
    async def title_search(query: str, max_results: Optional[int] = None) -> dict:
        """Search title of legislation documents.

        Args:
            query: Search query
            max_results: Maximum number of results to return (optional, defaults to 10)
        """

        return await _execute_simple_search(
            search_service.search_title, query, max_results, "Title search"
        )


def register_number_search(app):
    """Register the number search tool."""

    @app.tool()
    async def number_search(query: str, max_results: Optional[int] = None) -> dict:
        """Search the identification number of legislation documents.

        Args:
            query: Search query
            max_results: Maximum number of results to return (optional, defaults to 10)
        """

        return await _execute_simple_search(
            search_service.search_number, query, max_results, "Number search"
        )


def register_document_search(app):
    """Register the document search tool."""

    @app.tool()
    async def document_search(
        document_type: str, number: int, year: int, issuer: str
    ) -> dict:
        """Search for a specific document.

        Args:
            document_type: The type of the document (e.g. `lege`)
            number: The number of the document (e.g. 95)
            year: The year the document was issued
            (this might be different than the year of publication and/or entry into force)
            issuer: The issuing authority of the document (e.g. `guvernul`)
        """

        if search_service is None:
            return {"results": [], "error": "Search service not initialized"}

        if document_type.strip() == "":
            return {"results": [], "error": "Document type cannot be empty."}

        if (
            number < 0
        ):  # Some documents actually have 0 as number in the SOAP API database
            return {"results": [], "error": "Document number cannot be less than 0."}

        if year < 0:
            return {"results": [], "error": "Document year cannot be less than 0."}

        if issuer.strip() == "":
            return {"results": [], "error": "Document issuer cannot be empty."}

        try:
            result = await search_service.try_get_exact_match(
                document_type, number, year, issuer
            )

            if not result:
                return {"results": [], "total": 0}

            return {"results": [result.__dict__], "total": 1}
        except Exception as e:
            return {"results": [], "error": str(e)}


async def _execute_simple_search(
    search_method, query: str, max_results: Optional[int], operation_name: str
) -> dict:
    """Common search execution logic for all search tools.

    Args:
        search_method: The search service method to call
        query: Search query string
        max_results: Optional maximum results limit
        operation_name: Name of operation for logging (e.g., "Text search", "Title search")
    """
    if search_service is None:
        return {"results": [], "error": "Search service not initialized"}

    if not query or query.strip() == "":
        return {"results": [], "error": "Query cannot be empty."}

    if max_results is not None and max_results <= 0:
        return {"results": [], "error": "Max results must be positive."}

    try:
        if max_results is None:
            results = await search_method(query)
        else:
            results = await search_method(query, max_results)

        if not results:
            return {"results": [], "total": 0}

        dict_results = []
        for r in results:
            result_dict = r.__dict__
            dict_results.append(result_dict)

        return {"results": dict_results, "total": len(dict_results)}
    except Exception as e:
        logger.error(f"{operation_name} MCP tool failed: {e}")
        return {"results": [], "error": str(e)}
