from fastmcp import FastMCP
from romanian_legislation_mcp.api_consumers.search_service import SearchService
import logging

logger = logging.getLogger(__name__)


def register_tools(app: FastMCP, service: SearchService):
    """Register available tools with the MCP server"""
    global search_service
    search_service = service

    register_content_search(app)

    logger.info("All MCP tools registered successfully.")


def register_content_search(app):
    """Register text search tool."""

    @app.tool()
    async def content_search(query: str, max_results: Optional[int] = None) -> dict:
        """Search the legislation database for documents that may contain the query text.
        This is a broad database search, not a precise content search within documents.
        Do not use if user is looking for a specific document - use document_search instead.
        For precise content search within a known document, use document_content_search.

        ROMANIAN LEGAL TERMINOLOGY: Legal concepts typically use DEFINITE ARTICLES:
        - "contract" → "contractul" (the contract)
        - "proprietate" → "proprietatea" (the property)
        - "obligatie" → "obligatia" (the obligation)
        - Also try plural forms: "contractele" (the contracts), "obligatiile" (the obligations)

        SEARCH STRATEGY for Romanian legal documents:
        1. START BROAD: Use general legal concepts first (e.g., "contractul de depozit", "dreptul de proprietate")
        2. AVOID combining multiple specific terms in one search (e.g., avoid "contract depozit încetare terminare")
        3. HIERARCHICAL APPROACH: Find the main legal institution first, then search within it for specifics
        4. Romanian legal structure: Codes are organized by main topics → chapters → specific provisions

        EXAMPLES of effective search patterns:
        - For storage contract termination: First search "contractul de depozit", then search within results for termination provisions
        - For property rights: First search "dreptul de proprietate", then narrow to specific aspects
        - For employment issues: First search "contractul de muncă", then search specific clauses

        Args:
            query: Search query (start with broad legal concepts, avoid combining multiple specific terms)
            max_results: Maximum number of results to return (optional, defaults to 10)
        """

        return await _execute_simple_search(
            search_service.search_content, query, max_results, "Text search"
        )
