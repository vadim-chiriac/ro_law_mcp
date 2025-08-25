import json
from romanian_legislation_mcp.mappings.legal_document_mappings import (
    COMMON_DOCUMENTS,
    COMMON_ISSUERS,
    DOCUMENT_MAPPINGS,
    ISSUER_MAPPINGS_FOR_TOOLS,
)


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
