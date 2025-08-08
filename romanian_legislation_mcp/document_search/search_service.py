from typing import List, Optional, Dict, Any
import logging
import re

from romanian_legislation_mcp.api_client.soap_client import SoapClient
from romanian_legislation_mcp.api_client.legislation_document import LegislationDocument
from romanian_legislation_mcp.api_client.utils import create_fuzzy_romanian_pattern
from romanian_legislation_mcp.document_search.exact_document_finder import (
    ExactDocumentFinder,
)

logger = logging.getLogger(__name__)


class SearchService:
    """Class containing methods for different types of searches in the SOAP API"""

    def __init__(self, soap_client: SoapClient):
        """Creates a new instance of `Search Service`

        :param soap_client: The instance of `SoapClient` to use for API calls
        """
        self.client = soap_client
        self.doc_finder = ExactDocumentFinder(soap_client)

    async def search_content(
        self, query: str, max_results: int = 10
    ) -> List[LegislationDocument]:
        """Search legislation documents by full-text query.

        :param query: Full-text search query.
        :param max_results: Maximum number of results to return.
        :return: List of `LegislationDocument` objects matching the search criteria.
        """

        return await self.client.search_raw(text=query, page_size=max_results)

    async def search_title(
        self, title: str, max_results: int = 10
    ) -> List[LegislationDocument]:
        """Search legislation documents by title.

        :param title: Title to search for.
        :param max_results: Maximum number of results to return.
        :return: List of `LegislationDocument` objects matching the title.
        """

        return await self.client.search_raw(title=title, page_size=max_results)

    async def search_number(
        self, number: str, year: Optional[int] = None, max_results: int = 10
    ) -> List[LegislationDocument]:
        """Search legislation documents by number and optional year.
        Note: Year filtering may return documents from nearby years if no exact matches exist.

        :param number: Document number to search for.
        :param year: Optional year to filter results.
        :return: List of `LegislationDocument` objects matching the number and year.
        """

        return await self.client.search_raw(
            number=number, year=year, page_size=max_results
        )

    async def try_get_exact_match(
        self, document_type: str, number: int, year: int, issuer: str
    ):
        """Tries to get an exact match from document identifiers.

        :param document_type: The type of document (e.g. 'lege', 'hotarare')
        :param number: The number of the document
        :param year: The issuance year of the document
        :param issuer: The issuer of the document (e.g. 'guvernul')
        :return
        """
        if document_type == "lege":
            issuer = "Parlamentul"

        return await self.doc_finder.find_exact_document(
            document_type=document_type, number=number, year=year, issuer=issuer
        )

    async def document_content_search(
        self,
        document_type: str,
        number: int,
        year: int,
        issuer: str,
        search_query: str,
        max_excerpts: int = 5,
        excerpt_context_chars: int = 500,
        search_position: Optional[int] = None,
        search_radius: Optional[int] = 10000,
    ) -> Dict[str, Any]:
        """Search for specific content within a identified legal document.

        :param document_type: The type of document (e.g. 'lege')
        :param number: The number of the document
        :param year: The issuance year of the document
        :param issuer: The issuer of the document (e.g. 'guvernul')
        :param search_query: What to search for within that document
        :param max_excerpts: Maximum number of relevant excerpts to return
        :param excerpt_context_chars: Characters of context around each match
        :param search_position: Optional position in document to center search around
        :param search_radius: Characters before/after search_position to search within
        :return: Dictionary containing document info and matching excerpts
        """

        document = await self.try_get_exact_match(document_type, number, year, issuer)

        if not document:
            return {
                "document_found": False,
                "error": f"Document not found: {document_type} {number}/{year} from {issuer}",
            }

        if not document.text or document.text.strip() == "":
            return {
                "document_found": False,
                "error": """A document with the specified details was found, but it is empty. 
                         This most likely indicated a SOAP API error.""",
            }

        text = document.text
        
        # If search_position is specified, limit search to that region
        search_text = text
        position_offset = 0
        if search_position is not None:
            start_pos = max(0, search_position - search_radius)
            end_pos = min(len(text), search_position + search_radius)
            search_text = text[start_pos:end_pos]
            position_offset = start_pos
        
        fuzzy_pattern = create_fuzzy_romanian_pattern(search_query)
        query_pattern = re.compile(fuzzy_pattern, re.IGNORECASE)
        matches = list(query_pattern.finditer(search_text))

        if not matches:
            return {
                "document_found": True,
                "document_info": {
                    "document_type": document_type,
                    "title": document.title,
                    "issuer": issuer,
                },
                "excerpts": [],
                "total_matches": 0,
                "search_query": search_query,
            }

        excerpts = []
        text_len = len(text)

        for i, match in enumerate(matches[:max_excerpts]):
            # Adjust match positions to account for position_offset
            actual_match_start = match.start() + position_offset
            actual_match_end = match.end() + position_offset
            
            start_pos = max(0, actual_match_start - excerpt_context_chars)
            end_pos = min(text_len, actual_match_end + excerpt_context_chars)

            excerpt_text = text[start_pos:end_pos]

            match_start_in_excerpt = actual_match_start - start_pos
            match_end_in_excerpt = actual_match_end - start_pos

            excerpts.append(
                {
                    "excerpt_number": i + 1,
                    "text": excerpt_text,
                    "match_start_in_excerpt": match_start_in_excerpt,
                    "match_end_in_excerpt": match_end_in_excerpt,
                    "position_in_document": actual_match_start,
                    "match_length": actual_match_end - actual_match_start,
                }
            )

        return {
            "document_found": True,
            "document_info": {
                "document_type": document_type,
                "title": document.title,
                "issuer": document.issuer,
                "effective_date": document.effective_date,
                # Skip adding changes for now, as we are reaching the size limit for documents with extensive changes
                # "changes": document.changes, 
                "document_url": getattr(document, "url", None),
            },
            "excerpts": excerpts,
            "total_matches": len(matches),
            "search_query": search_query,
            "showing_excerpts": min(len(matches), max_excerpts),
            "excerpt_context_chars": excerpt_context_chars,
        }
