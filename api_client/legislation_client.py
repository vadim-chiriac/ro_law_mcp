from typing import List, Optional
from api_client.legislation_document import LegislationDocument


class LegislationClient:

    # Public API methods (for MCP server calls)
    async def search_by_text(
        query: str, max_results: int = 10
    ) -> List[LegislationDocument]:
        """Search legislation documents by full-text query.

        :param query: Full-text search query.
        :param max_results: Maximum number of results to return.
        :return: List of LegislationDocument objects matching the search criteria.
        """
        pass

    async def search_by_title(
        title: str, max_results: int = 10
    ) -> List[LegislationDocument]:
        """Search legislation documents by title.
        :param title: Title to search for.
        :param max_results: Maximum number of results to return.
        :return: List of LegislationDocument objects matching the title.
        """
        pass

    async def search_by_number(
        number: str, year: Optional[int] = None
    ) -> List[LegislationDocument]:
        """Search legislation documents by number and optional year.
        :param number: Document number to search for.
        :param year: Optional year to filter results.
        :return: List of LegislationDocument objects matching the number and year.
        """
        pass

    async def search_advanced(**kwargs) -> List[LegislationDocument]:
        """Advanced search with multiple parameters.
        :param kwargs: Search parameters like title, number, year, emitter, etc.
        :return: List of LegislationDocument objects matching the advanced search criteria.
        """
        pass

    # Private methods
    async def _ensure_valid_token():
        pass

    async def _get_fresh_token():
        pass

    def _process_search_results(raw_results) -> List[LegislationDocument]:
        pass

    def _create_search_model(**params):
        pass
