import logging
import json
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
    register_guidance_tool(app)

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
    async def content_search(query: str, max_results: Optional[int] = None) -> dict:
        """Search contents of legislation documents. Do not use if user is looking for a specific document.
        Use document_search in this case.

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
        """Search title of legislation documents. Do not use if user is looking for a specific document.
        Use document_search in this case.

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
        """Search the identification number of legislation documents. Do not use if user is looking for a specific document.
        Use document_search in this case.

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


def register_guidance_tool(app):
    """Register the search guidance tool."""

    @app.tool()
    async def generic_document_guidance(description: str) -> str:
        """
        Guides you to find a SPECIFIC document when you have incomplete identification details.

        Use this tool ONLY when:
        - User wants to find ONE specific document (not explore a topic)
        - You're missing one or more required details: document type, number, year, or issuer
        
        Do NOT use this tool for topic exploration or when you already have all required details
        for document_search (type, number, year, issuer).
        
        Do NOT use this tool is you have the type, number and year, if the type (in Romanian) is "Lege"
        or "Ordonanta de Urgenta"/"OUG". In this case, use the document_search tool, as the issuer
        for "Lege" is always "Parlamentul", and the issuer for "OUG" is always "Guvernul".

        Args:
            description: Generic description of the specific document (e.g., "Romanian Mountain Law", "Corporate Tax Code")

        Returns:
            Step-by-step guidance to identify the missing details and use document_search
        """

        guidance = {
            "target_document": description,
            "goal": "Find exact identification details to use document_search (the most reliable method)",
            "required_details": {
                "document_type": "Examples: 'lege', 'ordonanta de urgenta', 'ordonanta', 'cod'",
                "number": "The document number (e.g., 197)",
                "year": "The year the document was issued",
                "issuer": "For laws: always 'Parlamentul' | For emergency ordinances: always 'Guvernul' | For others: varies"
            },
            "identification_steps": [
                {
                    "step": 1,
                    "action": "Extract what you already know",
                    "instruction": f"""From '{description}', identify what you already have:
                    - Is it a law/emergency ordinance/ordinance/code?
                    - Any numbers mentioned?
                    - Any years mentioned?
                    - If it's a law → issuer is 'Parlamentul'
                    - If it's emergency ordinance → issuer is 'Guvernul'"""
                },
                {
                    "step": 2,
                    "action": "Web search for missing details",
                    "searches": [
                        f"Romania \"{description}\" law number year",
                        f"\"{description}\" Romanian legislation number",
                        f"Legea \"{description}\" România număr an",
                        f"\"{description}\" site:legislatie.just.ro"
                    ],
                    "instruction": "Search specifically for the EXACT law number and year"
                },
                {
                    "step": 3,
                    "action": "Use title_search if web search fails",
                    "instruction": f"If web search doesn't give clear results, try title_search('{description}') to find candidate documents and extract their details"
                },
                {
                    "step": 4,
                    "action": "Use document_search with found details",
                    "instruction": "Once you have all details, use document_search - this is the MOST RELIABLE method",
                    "example": "document_search(document_type='lege', number=197, year=2018, issuer='Parlamentul')"
                }
            ],
            "quick_reference": {
                "common_types": {
                    "Law": "document_type='lege', issuer='Parlamentul'",
                    "Emergency Ordinance": "document_type='ordonanta de urgenta', issuer='Guvernul'",
                    "Ordinance": "document_type='ordonanta', issuer='Guvernul'",
                    "Code": "document_type='cod', issuer=(varies)"
                },
                "success_pattern": f"'{description}' → Web search → Find exact details → document_search()"
            }
        }

        return json.dumps(guidance, indent=2, ensure_ascii=False)


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
