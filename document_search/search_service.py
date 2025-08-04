from typing import List, Optional
from api_client.soap_client import SoapClient
from api_client.legislation_document import LegislationDocument
import logging

from document_search.exact_document_finder import ExactDocumentFinder

logger = logging.getLogger(__name__)


class SearchService:
    """Class containing methods for different types of searches in the SOAP API"""

    def __init__(self, soap_client: SoapClient):
        """Creates a new instance of `Search Service`

        :param soap_client: The instance of `SoapClient` to use for API calls
        """
        self.client = soap_client
        self.doc_finder = ExactDocumentFinder(soap_client)

    async def search_by_text(
        self, query: str, max_results: int = 10
    ) -> List[LegislationDocument]:
        """Search legislation documents by full-text query.

        :param query: Full-text search query.
        :param max_results: Maximum number of results to return.
        :return: List of `LegislationDocument` objects matching the search criteria.
        """

        return await self.client.search_raw(text=query, page_size=max_results)

    async def search_by_title(
        self, title: str, max_results: int = 10
    ) -> List[LegislationDocument]:
        """Search legislation documents by title.

        :param title: Title to search for.
        :param max_results: Maximum number of results to return.
        :return: List of `LegislationDocument` objects matching the title.
        """

        return await self.client.search_raw(title=title, page_size=max_results)

    async def search_by_number(
        self, number: str, year: Optional[int] = None, max_results: int = 10
    ) -> List[LegislationDocument]:
        """Search legislation documents by number and optional year.
        Note: Year filtering may return documents from nearby years if no exact matches exist.

        :param number: Document number to search for.
        :param year: Optional year to filter results.
        :return: List of `LegislationDocument` objects matching the number and year.
        """

        return await self.client.search_raw(number=number, year=year, page_size=max_results)

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
        return await self.doc_finder.find_exact_document(
            document_type=document_type, number=number, year=year, issuer=issuer
        )
