import logging
import json
from typing import Optional
from mcp.server.fastmcp import FastMCP

from romanian_legislation_mcp.document_search.search_service import SearchService
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

        Args:
            document_type: The type of document (e.g. 'lege')
            number: The number of the document
            year: The year the document was issued
            issuer: The issuing authority of the document (e.g. 'Parlamentul')
            search_query: What to search for within that document
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

        base_documents = {
            "civil_code": {
                "document_type": "lege",
                "number": 287,
                "year": 2009,
                "issuer": "Parlamentul",
                "full_name": "LEGE nr. 287 din 17 iulie 2009 privind Codul civil",
            },
            "criminal_code": {
                "document_type": "lege",
                "number": 286,
                "year": 2009,
                "issuer": "Parlamentul",
                "full_name": "LEGE nr. 286 din 17 iulie 2009 privind Codul civil",
            },
            "labor_code": {
                "document_type": "lege",
                "number": 53,
                "year": 2003,
                "issuer": "Parlamentul",
                "full_name": "CODUL MUNCII din 24 ianuarie 2003",
            },
            "tax_code": {
                "document_type": "lege",
                "number": 227,
                "year": 2015,
                "issuer": "Parlamentul",
                "full_name": "LEGE nr. 227 din 8 septembrie 2015 privind Codul fiscal",
            },
            "civil_procedure_code": {
                "document_type": "lege",
                "number": 134,
                "year": 2010,
                "issuer": "Parlamentul",
                "full_name": "LEGE nr. 134 din 1 iulie 2010 privind Codul de procedură civilă",
            },
            "criminal_procedure_code": {
                "document_type": "lege",
                "number": 135,
                "year": 2010,
                "issuer": "Parlamentul",
                "full_name": "LEGE nr. 135 din 1 iulie 2010 privind Codul de procedură penală",
            },
            "tax_procedure_code": {
                "document_type": "lege",
                "number": 207,
                "year": 2015,
                "issuer": "Parlamentul",
                "full_name": "LEGE nr. 207 din 20 iulie 2015 privind Codul de procedură fiscală",
            },
        }

        document_mappings = {
            # Civil Code variations
            "civil code": base_documents["civil_code"],
            "codul civil": base_documents["civil_code"],
            "cc": base_documents["civil_code"],
            # Criminal Code variations
            "criminal code": base_documents["criminal_code"],
            "codul penal": base_documents["criminal_code"],
            "penal code": base_documents["criminal_code"],
            "cp": base_documents["criminal_code"],
            # Labor Code variations
            "labor code": base_documents["labor_code"],
            "labour code": base_documents["labor_code"],
            "codul muncii": base_documents["labor_code"],
            "cm": base_documents["labor_code"],
            # Tax/Fiscal Code variations
            "tax code": base_documents["tax_code"],
            "fiscal code": base_documents["tax_code"],
            "codul fiscal": base_documents["tax_code"],
            "cf": base_documents["tax_code"],
            # Civil Procedure Code variations
            "civil procedure code": base_documents["civil_procedure_code"],
            "code of civil procedure": base_documents["civil_procedure_code"],
            "codul de procedura civila": base_documents["civil_procedure_code"],
            "cpc": base_documents["civil_procedure_code"],
            # Criminal Procedure Code variations
            "criminal procedure code": base_documents["criminal_procedure_code"],
            "code of criminal procedure": base_documents["criminal_procedure_code"],
            "codul de procedura penala": base_documents["criminal_procedure_code"],
            "cpp": base_documents["criminal_procedure_code"],
            # Tax Procedure Code variations
            "tax procedure code": base_documents["tax_procedure_code"],
            "fiscal procedure code": base_documents["tax_procedure_code"],
            "codul de procedura fiscala": base_documents["tax_procedure_code"],
            "cpf": base_documents["tax_procedure_code"],
        }

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

        # No matches found
        common_documents = [
            {"name": "Civil Code (Codul Civil)", "search_hint": "codul civil"},
            {"name": "Criminal Code (Codul Penal)", "search_hint": "codul penal"},
            {"name": "Labor Code (Codul Muncii)", "search_hint": "codul muncii"},
            {"name": "Tax Code (Codul Fiscal)", "search_hint": "codul fiscal"},
            {
                "name": "Civil Procedure Code (Codul de Procedura Civila)",
                "search_hint": "codul de procedura civila",
            },
            {
                "name": "Criminal Procedure Code (Codul de Procedura Penala)",
                "search_hint": "codul de procedura penala",
            },
            {
                "name": "Tax Procedure Code (Codul de Procedura Fiscala)",
                "search_hint": "codul de procedura fiscala",
            },
        ]

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

        issuer_mappings = {
            # Government variations
            "government": "Guvernul",
            "guvern": "Guvernul",
            "guvernul": "Guvernul",
            "guvernul romaniei": "Guvernul",
            "government of romania": "Guvernul",
            "romanian government": "Guvernul",
            # Parliament variations
            "parliament": "Parlamentul",
            "parlamentul": "Parlamentul",
            "parlament": "Parlamentul",
            "parlamentul romaniei": "Parlamentul",
            "parliament of romania": "Parlamentul",
            "romanian parliament": "Parlamentul",
            # Prime Minister variations
            "prime minister": "Prim-ministrul",
            "prim ministru": "Prim-ministrul",
            "primul ministru": "Prim-ministrul",
            "prim-ministru": "Prim-ministrul",
            "prim-ministrul": "Prim-ministrul",
            "pm": "Prim-ministrul",
            # President variations
            "president": "Presedintele Romaniei",
            "presedinte": "Presedintele Romaniei",
            "presedintele": "Presedintele Romaniei",
            "presedintele romaniei": "Presedintele Romaniei",
            "president of romania": "Presedintele Romaniei",
            # Ministries (common ones)
            "ministry of finance": "Ministerul Finantelor",
            "ministerul finantelor": "Ministerul Finantelor",
            "ministry of health": "Ministerul Sanatatii",
            "ministerul sanatatii": "Ministerul Sanatatii",
            "ministry of education": "Ministerul Educatiei",
            "ministerul educatiei": "Ministerul Educatiei",
            "ministry of interior": "Ministerul Afacerilor Interne",
            "ministerul afacerilor interne": "Ministerul Afacerilor Interne",
            "ministry of justice": "Ministerul Justitiei",
            "ministerul justitiei": "Ministerul Justitiei",
            # Agencies and authorities
            "anaf": "Agentia Nationala de Administrare Fiscala",
            "tax authority": "Agentia Nationala de Administrare Fiscala",
            "national bank": "Banca Nationala a Romaniei",
            "bnr": "Banca Nationala a Romaniei",
            "banca nationala": "Banca Nationala a Romaniei",
            # Consumer protection
            "anpc": "Autoritatea Nationala pentru Protectia Consumatorilor",
            "consumer protection": "Autoritatea Nationala pentru Protectia Consumatorilor",
            # Courts
            "constitutional court": "Curtea Constitutionala",
            "curtea constitutionala": "Curtea Constitutionala",
            "ccr": "Curtea Constitutionala",
            "supreme court": "Inalta Curte de Casatie si Justitie",
            "curtea suprema": "Inalta Curte de Casatie si Justitie",
            "inalta curte": "Inalta Curte de Casatie si Justitie",
            "iccj": "Inalta Curte de Casatie si Justitie",
        }

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
                    "suggestions": partial_matches[:5],  # Limit to top 5
                },
                ensure_ascii=False,
                indent=2,
            )

        common_issuers = [
            {"description": "Government/Executive", "issuer": "Guvernul"},
            {"description": "Parliament/Legislative", "issuer": "Parlamentul"},
            {"description": "Prime Minister", "issuer": "Prim-ministrul"},
            {"description": "President", "issuer": "Presedintele Romaniei"},
            {"description": "Ministry of Finance", "issuer": "Ministerul Finantelor"},
            {"description": "National Bank", "issuer": "Banca Nationala a Romaniei"},
        ]

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
