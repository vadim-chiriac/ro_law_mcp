from typing import List, Optional
import logging

from romanian_legislation_mcp.api_client.soap_client import SoapClient
from romanian_legislation_mcp.api_client.legislation_document import LegislationDocument

logger = logging.getLogger(__name__)


class SearchService:
    """Class containing methods for different types of searches in the SOAP API"""

    def __init__(self, soap_client: SoapClient):
        """Creates a new instance of `Search Service`

        :param soap_client: The instance of `SoapClient` to use for API calls
        """
        self.client = soap_client

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

   