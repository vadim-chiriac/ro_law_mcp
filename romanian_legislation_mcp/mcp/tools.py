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
    register_search_guidance(app)

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


def register_search_guidance(app):
    """Register the search guidance tool."""

    @app.tool()
    async def search_guidance(description: str) -> str:
        """
        Provides step-by-step guidance for identifying a specific document from a generic description.

        This tool helps when you have a generic reference like "Romanian Mountain Law" and need to
        find the exact legal document. It guides you through a process using your own LLM capabilities
        and web search to identify the precise document.

        Args:
            description: Generic description of the document (e.g., "Romanian Mountain Law", "Corporate Tax Code")

        Returns:
            Structured guidance with specific steps and search queries to identify the document
        """

        guidance = {
            "description_received": description,
            "search_strategy_decision": {
                "instruction": "First, determine your search intent:",
                "options": {
                    "specific_document": {
                        "when_to_use": "User wants to find ONE specific document",
                        "indicators": [
                            "mentions specific law name",
                            "references to 'the law about X'",
                            "needs full text of specific document",
                        ],
                        "tools_to_use": [
                            "document_search",
                            "title_search as helper",
                            "web search for identification",
                        ],
                    },
                    "explore_topic": {
                        "when_to_use": "User wants to explore what documents exist about a topic/subject/issuer",
                        "indicators": [
                            "wants to see 'all laws about X'",
                            "research on topic",
                            "what documents mention Y",
                        ],
                        "tools_to_use": ["content_search", "title_search"],
                    },
                },
            },
            "workflow_for_specific_document": {
                "note": "Use this workflow when looking for ONE specific document",
                "steps": [
                    {
                        "step": 1,
                        "action": "Check if you already have specifics",
                        "instruction": f"""From '{description}', check if you have:
                        - Document type (law/emergency ordinance/ordinance/code)
                        - Number (e.g., 197)
                        - Year (e.g., 2018)
                        - Issuer (Not need for laws, always the Parliament (search term: "Parlamentul") 
                        and for Emergency Ordinances, always the Government (search term: Guvernul"))
                        
                        If YES → Go directly to step 4 (document_search)
                        If NO → Continue to step 2""",
                    },
                    {
                        "step": 2,
                        "action": "Web search for exact identification",
                        "suggested_queries": [
                            f"Romania {description} law number year",
                            f"{description} Romanian legislation official name",
                            f"Legea {description} România număr an",
                            f"{description} site:legislatie.just.ro",
                        ],
                        "instruction": "Use web search to find the official name, law number, year, and type",
                    },
                    {
                        "step": 3,
                        "action": "Try title_search as backup",
                        "instruction": "If web search didn't give clear results, use title_search with key terms from the description to find candidate documents",
                    },
                    {
                        "step": 4,
                        "action": "Use document_search with exact details",
                        "instruction": """Once you have specifics, use document_search with:
                        - document_type: 'lege' (for laws), 'oug' (for emergency ordinances), etc.
                        - number: the law number
                        - year: the year issued
                        - issuer: 'Parlamentul' (for laws), 'Guvernul' (for emergency ordinances)
                        
                        This is the MOST RELIABLE method when you have exact details.""",
                    },
                ],
            },
            "workflow_for_topic_exploration": {
                "note": "Use this workflow when exploring what documents exist about a topic",
                "steps": [
                    {
                        "step": 1,
                        "action": "Use content_search",
                        "instruction": f"Search for '{description}' using content_search to find documents that mention this topic",
                    },
                    {
                        "step": 2,
                        "action": "Use title_search",
                        "instruction": f"Search for '{description}' using title_search to find documents with this topic in their title",
                    },
                    {
                        "step": 3,
                        "action": "Review and refine",
                        "instruction": "Review results and try different keywords if needed. The SOAP API search is not very reliable, so try multiple keyword variations.",
                    },
                ],
            },
            "important_notes": {
                "document_search_reliability": "document_search is the MOST RELIABLE tool when you have exact document details (type, number, year, issuer)",
                "soap_api_limitations": "title_search and content_search use the underlying SOAP API which is not very reliable - use them for exploration, not for finding specific documents",
                "default_issuers": {
                    "laws": "Always use 'Parlamentul' as issuer for laws (Lege)",
                    "emergency_ordinances": "Always use 'Guvernul' as issuer for emergency ordinances (Ordonanță de Urgență/OUG)",
                },
            },
            "example_workflows": {
                "specific_document_example": f"For '{description}' → Web search → Find 'Law 197/2018' → document_search(document_type='lege', number=197, year=2018, issuer='Parlamentul')",
                "topic_exploration_example": f"For 'environmental protection laws' → content_search('environmental protection') + title_search('environment')",
            },
            "romanian_terms": {
                "law": "lege",
                "emergency_ordinance": "ordonanta de urgenta",
                "ordinance": "ordonanta",
                "code": "cod",
                "parliament": "Parlamentul",
                "government": "Guvernul",
            },
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
