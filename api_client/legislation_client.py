from __future__ import annotations
from datetime import datetime, timedelta, timezone
from zeep import Client
from legislation_document import LegislationDocument
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LegislationClient:
    def __init__(self, wsdl_url: str):
        """Do not call this directly, use `create` class method instead."""

        self.wsdl_url: str = wsdl_url
        self.client: Client = None
        self.token: str = None
        self.token_expires_at = None

    @classmethod
    async def create(cls, wsdl_url: str) -> "LegislationClient":
        """Factory method for instance creation

        :param wsdl_url: URL to the WSDL service
        :return: New `LegislationClient` instance
        :raises ConnectionError: If SOAP client initialization fails
        """

        instance = cls(wsdl_url)

        try:
            instance.client = Client(wsdl_url)
        except Exception as e:
            raise ConnectionError(f"Failed to create SOAP client: {e}")

        return instance

    # Public API methods (for MCP server calls)
    async def search_by_text(
        self, query: str, max_results: int = 10
    ) -> List[LegislationDocument]:
        """Search legislation documents by full-text query.

        :param query: Full-text search query.
        :param max_results: Maximum number of results to return.
        :return: List of `LegislationDocument` objects matching the search criteria.
        """

        search_model = self._create_search_model(text=query, page_size=max_results)
        return self._execute_search(search_model)

    async def search_by_title(
        self, title: str, max_results: int = 10
    ) -> List[LegislationDocument]:
        """Search legislation documents by title.

        :param title: Title to search for.
        :param max_results: Maximum number of results to return.
        :return: List of `LegislationDocument` objects matching the title.
        """
        search_model = self._create_search_model(title=title, page_size=max_results)
        return self._execute_search(search_model)

    async def search_by_number(
        self, number: str, year: Optional[int] = None, max_results=10
    ) -> List[LegislationDocument]:
        """Search legislation documents by number and optional year.

        :param number: Document number to search for.
        :param year: Optional year to filter results.
        :return: List of `LegislationDocument` objects matching the number and year.
        """
        search_model = self._create_search_model(
            number=number, year=year, page_size=max_results
        )
        return self._execute_search(search_model)

    async def search_advanced(**kwargs) -> List[LegislationDocument]:
        """Advanced search with multiple parameters.

        :param kwargs: Search parameters like title, number, year, issuer etc.
        :return: List of `LegislationDocument` objects matching the advanced search criteria.
        """

        pass

    # Private methods
    def _get_fresh_token(self):
        """Gets a new token from the SOAP API"""

        try:
            self.token = self.client.service.GetToken()
            self.token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        except Exception as e:
            raise ConnectionError(f"Failed to get token: {e}")

    def _ensure_valid_token(self):
        """Gets a new token from the SOAP API if it does not exist or is expired"""

        if self.token is None or self._is_token_expired():
            self._get_fresh_token()

    def _is_token_expired(self) -> bool:
        """Checks if current SOAP API token is expired"""

        if self.token_expires_at is None:
            return True
        return datetime.now(timezone.utc) >= self.token_expires_at
    
    def _execute_search(self, search_model: dict) -> List[LegislationDocument]:
        """ Executes a search with the given search model
        
        :param search_model: The built search model to use with the SOAP API.
        :return: List of `LegislationDocument` matching the search model.
        """
        self._ensure_valid_token()
        try:
            results = self.client.service.Search(search_model, self.token)
            parsed_results = self._parse_search_results(results)

            return parsed_results
        except Exception as e:
            raise ConnectionError(f"Error retrieving search results: {e}")


    def _parse_search_results(
        self, raw_results: List[dict]
    ) -> List[LegislationDocument]:
        """Converts the raw response from the SOAP API into a more generally readable format

        :param raw_results: List of raw results received from the SOAP API
        :return: List of parsed results
        """

        parsed_results = []
        for r in raw_results:
            title = r.Titlu
            number = r.Numar
            act_type = r.TipAct
            issuer = r.Emitent
            effective_date = datetime.strptime(r.DataVigoare, "%Y-%m-%d")
            text = r.Text
            publication = getattr(r, "Publicatie", None)
            url = getattr(r, "LinkHtml", None)

            parsed_result = LegislationDocument(
                title=title,
                number=number,
                act_type=act_type,
                issuer=issuer,
                effective_date=effective_date,
                text=text,
                publication=publication,
                url=url,
            )

            parsed_results.append(parsed_result)

        return parsed_results

    def _create_search_model(
        self,
        text: Optional[str] = None,
        title: Optional[str] = None,
        number: Optional[str] = None,
        year: Optional[int] = None,
        page: int = 0,
        page_size: int = 10,
    ):
        """Creates a SOAP search model for the Romanian legislation API.

        :param text: Search term to find within document content (full-text search)
        :param title: Search term to find within document titles
        :param number: Specific document number to search for
        :param year: Filter results by year of issuance
        :param page: Page number for pagination (0-based)
        :param page_size: Maximum number of results per page
        :return: Dictionary formatted for SOAP API search request
        """

        return {
            "NumarPagina": page,
            "RezultatePagina": page_size,
            "SearchAn": year,
            "SearchNumar": number,
            "SearchTitlu": title,
            "SearchText": text,
        }


import asyncio


async def test_client():
    logger.info("Testing client...")
    l_client = await LegislationClient.create(
        "https://legislatie.just.ro/apiws/FreeWebService.svc?singleWsdl"
    )
    await l_client.search_by_text("contract")


if __name__ == "__main__":
    asyncio.run(test_client())
