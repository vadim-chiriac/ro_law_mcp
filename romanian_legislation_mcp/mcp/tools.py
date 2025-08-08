import logging
import json
from typing import Optional
from mcp.server.fastmcp import FastMCP

from romanian_legislation_mcp.document_search.search_service import SearchService
from romanian_legislation_mcp.document_search.legal_document_mappings import (
    DOCUMENT_MAPPINGS,
    COMMON_DOCUMENTS,
    ISSUER_MAPPINGS_FOR_TOOLS,
    COMMON_ISSUERS,
)
from romanian_legislation_mcp.mcp.res_size_utils import (
    _manage_response_size,
)

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
    register_document_content_search(app)
    register_document_changes(app)
    register_guidance_tool(app)
    register_document_identification_tool(app)
    register_issuer_mapping_tool(app)

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


def register_title_search(app):
    """Register the title search tool."""

    @app.tool()
    async def title_search(query: str, max_results: Optional[int] = None) -> dict:
        """Search the legislation database for documents with titles that may match the query.
        This is a broad database search of document titles, not precise title matching.
        Do not use if user is looking for a specific document - use document_search instead.

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
        """Search the legislation database for documents with identification numbers that may match the query.
        This is a broad database search of document numbers, not precise number matching.
        Do not use if user is looking for a specific document - use document_search instead.

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

            response = {"results": [result.__dict__], "total": 1}
            response = _manage_response_size(response)

            return response
        except Exception as e:
            return {"results": [], "error": str(e)}


def register_document_content_search(app):
    """Register the document content search tool."""

    @app.tool()
    async def document_content_search(
        document_type: str,
        number: int,
        year: int,
        issuer: str,
        search_query: str,
        max_excerpts: int = 5,
        excerpt_context_chars: int = 500,
    ) -> dict:
        """Search for specific content within a identified legal document.

        Use this tool when you need to find specific information within a known document.
        First use identify_legal_document or other tools to get the exact document details,
        then use this tool to search within that document's content.

        ROMANIAN LEGAL TERMINOLOGY: Legal concepts typically use DEFINITE ARTICLES:
        - "contract" → "contractul" (the contract)
        - "proprietate" → "proprietatea" (the property)
        - "obligatie" → "obligatia" (the obligation)
        - Also try plural forms: "contractele" (the contracts), "obligatiile" (the obligations)

        SEARCH STRATEGY within Romanian legal documents:
        1. LEGAL HIERARCHY: Romanian codes follow: Title → Chapter → Section → Article → Paragraph
        2. START GENERAL: Search for main legal concepts first, then refine for specific aspects
        3. INCREMENTAL SEARCH: If no results with specific terms, try broader related terms
        4. CONTEXT MATTERS: Legal provisions often reference each other - check surrounding articles
        
        EFFECTIVE search query patterns:
        - For termination: Try "încetarea", "denunțarea" (with definite articles)
        - For obligations: Try "obligațiile", "răspunderea" 
        - For rights: Try "drepturile"

        Args:
            document_type: The type of document (e.g. 'lege')
            number: The number of the document
            year: The year the document was issued
            issuer: The issuing authority of the document (e.g. 'Parlamentul')
            search_query: What to search for within that document (start broad, then refine)
            max_excerpts: Maximum number of relevant excerpts to return (default: 5)
            excerpt_context_chars: Characters of context around each match (default: 500)

        Returns:
            Dictionary containing document info and matching excerpts with context
        """

        if search_service is None:
            return {"document_found": False, "error": "Search service not initialized"}

        # Validate inputs
        if not document_type.strip():
            return {"document_found": False, "error": "Document type cannot be empty"}

        if number < 0:
            return {
                "document_found": False,
                "error": "Document number cannot be negative",
            }

        if year < 0:
            return {
                "document_found": False,
                "error": "Document year cannot be negative",
            }

        if not issuer.strip():
            return {"document_found": False, "error": "Document issuer cannot be empty"}

        if not search_query.strip():
            return {"document_found": False, "error": "Search query cannot be empty"}

        if max_excerpts <= 0:
            return {"document_found": False, "error": "Max excerpts must be positive"}

        if excerpt_context_chars < 0:
            return {
                "document_found": False,
                "error": "Excerpt context chars cannot be negative",
            }

        try:
            result = await search_service.document_content_search(
                document_type=document_type,
                number=number,
                year=year,
                issuer=issuer,
                search_query=search_query,
                max_excerpts=max_excerpts,
                excerpt_context_chars=excerpt_context_chars,
            )

            return result

        except Exception as e:
            logger.error(f"Document content search failed: {e}")
            return {"document_found": False, "error": str(e)}


def register_document_changes(app):
    """Register the document changes tool."""

    @app.tool()
    async def document_changes(
        document_type: str,
        number: int,
        year: int,
        issuer: str,
    ) -> dict:
        """Retrieve changes made to a specific legal document.

        Use this tool AFTER document_content_search to understand if the excerpts you found
        are still current or have been modified by subsequent legislation.

        This helps determine if:
        - The found excerpts are still valid
        - You need to search newer documents that modified these provisions
        - The legal text has been repealed or updated

        Args:
            document_type: The type of document (e.g. 'lege')
            number: The number of the document
            year: The year the document was issued
            issuer: The issuing authority of the document (e.g. 'Parlamentul')

        Returns:
            Dictionary containing document info and list of changes made to it
        """

        if search_service is None:
            return {"document_found": False, "error": "Search service not initialized"}

        if not document_type.strip():
            return {"document_found": False, "error": "Document type cannot be empty"}

        if number < 0:
            return {
                "document_found": False,
                "error": "Document number cannot be negative",
            }

        if year < 0:
            return {
                "document_found": False,
                "error": "Document year cannot be negative",
            }

        if not issuer.strip():
            return {"document_found": False, "error": "Document issuer cannot be empty"}

        try:
            document = await search_service.try_get_exact_match(
                document_type, number, year, issuer
            )

            if not document:
                return {
                    "document_found": False,
                    "error": f"Document not found: {document_type} {number}/{year} from {issuer}",
                }

            result = {
                "document_found": True,
                "document_info": {
                    "document_type": document_type,
                    "number": document.number,
                    "title": document.title,
                    "issuer": document.issuer,
                    "effective_date": document.effective_date,
                },
                "changes": document.changes if hasattr(document, 'changes') and document.changes else [],
                "total_changes": len(document.changes) if hasattr(document, 'changes') and document.changes else 0,
            }

            result = _manage_response_size(result)
            return result

        except Exception as e:
            logger.error(f"Document changes retrieval failed: {e}")
            return {"document_found": False, "error": str(e)}


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
                "issuer": "For laws: always 'Parlamentul' | For emergency ordinances: always 'Guvernul' | For others: varies",
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
                    - If it's emergency ordinance → issuer is 'Guvernul'""",
                },
                {
                    "step": 2,
                    "action": "Web search for missing details",
                    "searches": [
                        f'Romania "{description}" law number year',
                        f'"{description}" Romanian legislation number',
                        f'Legea "{description}" România număr an',
                        f'"{description}" site:legislatie.just.ro',
                    ],
                    "instruction": "Search specifically for the EXACT law number and year",
                },
                {
                    "step": 3,
                    "action": "Use title_search if web search fails",
                    "instruction": f"If web search doesn't give clear results, try title_search('{description}') to find candidate documents and extract their details",
                },
                {
                    "step": 4,
                    "action": "Use document_search with found details",
                    "instruction": "Once you have all details, use document_search - this is the MOST RELIABLE method",
                    "example": "document_search(document_type='lege', number=197, year=2018, issuer='Parlamentul')",
                },
            ],
            "quick_reference": {
                "common_types": {
                    "Law": "document_type='lege', issuer='Parlamentul'",
                    "Emergency Ordinance": "document_type='ordonanta de urgenta', issuer='Guvernul'",
                    "Ordinance": "document_type='ordonanta', issuer='Guvernul'",
                    "Code": "document_type='cod', issuer=(varies)",
                },
                "success_pattern": f"'{description}' → Web search → Find exact details → document_search()",
            },
        }

        return json.dumps(guidance, indent=2, ensure_ascii=False)


def register_document_identification_tool(app):
    """Register the document identification tool."""

    @app.tool()
    async def identify_legal_document(document_description: str) -> str:
        """
        Identifies Romanian legal documents from natural language descriptions.

        Converts user descriptions like "Civil Code", "Criminal Code", "Labor Code"
        into exact parameters needed for document_search.

        Use this tool when you need to find the exact document identification details
        from a natural language description. Essential for focused document searches.

        Args:
            document_description: Natural language description in English or Romanian
            (e.g., "Civil Code", "Romanian Criminal Code", "Codul Muncii")

        Returns:
            JSON with document identification details for use with document_search,
            or suggestions if no exact match is found
        """

        normalized = document_description.strip().lower()
        normalized = (
            normalized.replace("ă", "a")
            .replace("â", "a")
            .replace("î", "i")
            .replace("ț", "t")
            .replace("ţ", "t")
            .replace("ş", "s")
            .replace("ș", "s")
        )

        normalized = (
            normalized.replace("romanian", "")
            .replace("romania", "")
            .replace("romaniei", "")
            .replace("din romania", "")
            .replace("al romaniei", "")
            .strip()
        )

        document_mappings = DOCUMENT_MAPPINGS

        if normalized in document_mappings:
            document_info = document_mappings[normalized]
            return json.dumps(
                {
                    "input": document_description,
                    "match_type": "exact",
                    "confidence": "high",
                    "document_details": document_info,
                    "usage_instruction": "Use these details with document_search(document_type='{type}', number={number}, year={year}, issuer='{issuer}')".format(
                        type=document_info["document_type"],
                        number=document_info["number"],
                        year=document_info["year"],
                        issuer=document_info["issuer"],
                    ),
                },
                ensure_ascii=False,
                indent=2,
            )

        # Check for partial matches
        partial_matches = []
        for key, value in document_mappings.items():
            if normalized in key or key in normalized:
                partial_matches.append({"description": key, "document_details": value})

        if partial_matches:
            return json.dumps(
                {
                    "input": document_description,
                    "match_type": "partial",
                    "confidence": "medium",
                    "suggestions": partial_matches[:3],
                    "note": "Multiple potential matches found. Choose the most appropriate one.",
                },
                ensure_ascii=False,
                indent=2,
            )

        common_documents = COMMON_DOCUMENTS

        return json.dumps(
            {
                "input": document_description,
                "match_type": "none",
                "confidence": "low",
                "message": "No direct match found. Try web search or title_search to find the document details.",
                "search_suggestions": [
                    f'Web search: "{document_description} numar romania"',
                    f'Web search: "{document_description} romanian law number year"',
                    f'Use title_search("{document_description}") to find candidate documents',
                ],
                "common_documents": common_documents,
            },
            ensure_ascii=False,
            indent=2,
        )


def register_issuer_mapping_tool(app):
    """Register the issuer mapping tool."""

    @app.tool()
    async def get_correct_issuer(issuer_description: str) -> str:
        """
        Maps various issuer descriptions to the correct legal terms for document_search.

        Use this tool when you need to find the exact issuer name for document_search from
        a user's description like "prime minister", "consumer protection authority", "tax authority" etc.
        If in doubt, use this tool rather than not, as users are not familiar with legal terminology, but the
        SOAP API search is rather strict.

        Args:
            issuer_description: Description of the issuer in English or Romanian
            (e.g., "prime minister", "guvern", "anaf", "finance ministry")

        Returns:
            JSON with the correct issuer term and alternatives, or suggestions if no exact match
        """

        normalized = issuer_description.strip().lower()
        normalized = (
            normalized.replace("ă", "a")
            .replace("â", "a")
            .replace("î", "i")
            .replace("ț", "t")
            .replace("ţ", "t")
            .replace("ş", "s")
            .replace("ș", "s")
        )

        issuer_mappings = ISSUER_MAPPINGS_FOR_TOOLS

        if normalized in issuer_mappings:
            correct_issuer = issuer_mappings[normalized]
            return json.dumps(
                {
                    "input": issuer_description,
                    "correct_issuer": correct_issuer,
                    "match_type": "exact",
                    "confidence": "high",
                },
                ensure_ascii=False,
                indent=2,
            )

        partial_matches = []
        for key, value in issuer_mappings.items():
            if normalized in key or key in normalized:
                partial_matches.append(
                    {"input_variation": key, "correct_issuer": value}
                )

        if partial_matches:
            return json.dumps(
                {
                    "input": issuer_description,
                    "match_type": "partial",
                    "confidence": "medium",
                    "suggestions": partial_matches[:5],  
                },
                ensure_ascii=False,
                indent=2,
            )

        common_issuers = COMMON_ISSUERS

        return json.dumps(
            {
                "input": issuer_description,
                "match_type": "none",
                "confidence": "low",
                "message": "No direct match found. Try web search or use title_search to find the document and identify the correct issuer.",
                "common_issuers": common_issuers,
            },
            ensure_ascii=False,
            indent=2,
        )


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

        response = {"results": dict_results, "total": len(dict_results)}
        response = _manage_response_size(response)

        return response

    except Exception as e:
        logger.error(f"{operation_name} MCP tool failed: {e}")
        return {"results": [], "error": str(e)}
