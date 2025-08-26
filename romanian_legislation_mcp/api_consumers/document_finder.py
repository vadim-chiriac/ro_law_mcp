from typing import List, Optional
import logging

from romanian_legislation_mcp.api_client.soap_client import SoapClient
from romanian_legislation_mcp.api_client.legislation_document import LegislationDocument
from romanian_legislation_mcp.mappings.issuer_mappings import get_canonical_issuer
from romanian_legislation_mcp.mappings.document_type_mappings import (
    get_canonical_document_type,
)
from romanian_legislation_mcp.document_cache.document_cache import DocumentCache

logger = logging.getLogger(__name__)


class DocumentFinder:
    """Class responsible for trying to retrive a document by its unique identifiers,
    meaning type, number, year and issuer"""

    def __init__(self, legislation_client: SoapClient, enable_cache: bool = True):
        """Initializes a new `ExactDocumentFinder`

        :param legislation_client: The underlying `SoapClient` for searching
        :param enable_cache: Whether to enable document caching. Defaults to True.
        """

        self.client = legislation_client
        self.cache = DocumentCache() if enable_cache else None

    async def get_document(
        self, document_type: str, number: int, year: int, issuer: str
    ) -> Optional[LegislationDocument]:
        """Tries to find an exact match for the given parameters

        :param document_type: The type of the document (e.g. "lege", "hotărâre").
        :param number: The number of the document.
        :param year: The issuance year of the document. This might be different than publication year or entry into force year.
        :param issuer: The issuing authority of the document (e.g. Guvernul României)
        """
        if self.cache:
            cached_result = self.cache.get(document_type, number, year, issuer)
            if cached_result:
                return cached_result

        result = await self._try_search_strategy(
            document_type, number, year, issuer, strategy="standard"
        )

        if result:
            if self.cache:
                self.cache.put(result, document_type, number, year, issuer)
            return result

        result = await self._try_search_strategy(
            document_type, number, year, issuer, strategy="alternate"
        )

        if result and self.cache:
            self.cache.put(result, document_type, number, year, issuer)

        return result

    async def _try_search_strategy(
        self, document_type: str, number: int, year: int, issuer: str, strategy: str
    ) -> Optional[LegislationDocument]:
        """Tries one search strategy"""

        search_text = self._build_search_text(
            document_type, number, year, issuer, strategy
        )
        logger.info(f"Trying {strategy} search: {search_text}")

        try:
            results = await self.client.search_raw(title=search_text)
            logger.info(f"Found {len(results)} results for {strategy} search")
            return self._get_exact_match(results, document_type, number, issuer)
        except ConnectionError as e:
            logger.warning(f"{strategy.title()} search failed: {e}")
            return None

    def _build_search_text(
        self, document_type: str, number: int, year: int, issuer: str, strategy: str
    ) -> str:
        """Build search text based on strategy"""
        issuer_canonical = get_canonical_issuer(issuer)
        doc_type_canonical = get_canonical_document_type(
            document_type, issuer_canonical
        )

        if strategy == "standard":
            return f"{doc_type_canonical} {number} * {year}"
        elif strategy == "alternate":
            return f"{doc_type_canonical} {number}/{year}"
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def _get_exact_match(
        self,
        all_results: List[LegislationDocument],
        expected_type: str,
        expected_no: int,
        expected_issuer: str,
    ) -> Optional[LegislationDocument]:
        """Checks if the SOAP API results match the search parameters passed by the client.

        :param all_results: List of SOAP API results from built title search
        :param expected_type: The type of legal document as given by the client
        :param expected_no: The number of the document as given by the client
        :param expected_issuer: The issuer of the document as given by the client

        :return: A single `LegislationDocument` matching the parameters given by the client, or `None`.
        """
        candidates: List[LegislationDocument] = []
        for result in all_results:
            doc_type = result.document_type
            issuer = result.issuer

            if not self._compare_document_type(doc_type, expected_type, issuer):
                continue

            number = result.number
            # Sometimes, the API returns "0" as the document number for those documents which are
            # identified only by date. In this case, we skip the number check.
            # This seems to the case for document identified by date only (e.g. Norma din 01/01/2000),
            # but clients might query for this as Norma 1/2000.
            if not self._compare_no(number, expected_no) and number != "0":
                continue

            if not self._compare_issuer(issuer, expected_issuer):
                continue

            candidates.append(result)
            if len(candidates) == 2:
                break

        for c in candidates:
            if "(*republicată*)" in c.title:
                return c

        if len(candidates) > 0:
            return candidates[0]

        return None

    def _compare_document_type(
        self, actual_type: str, expected_type: str, issuer: str
    ) -> bool:
        """Compares actual retrieved and expected document types for exact search

        :param actual_type: The type of the retrieved document
        :param expected_type: The type expected by the client
        :return: `True` if types match, `False` otherwise
        """
        issuer_canonical = get_canonical_issuer(issuer)

        actual_canonical = get_canonical_document_type(actual_type, issuer_canonical)
        expected_canonical = get_canonical_document_type(
            expected_type, issuer_canonical
        )

        logger.info(
            f"Comparing normalized types: '{actual_canonical}' vs '{expected_canonical}'"
        )

        do_types_match = actual_canonical == expected_canonical
        logger.info(f"Match: {do_types_match}")

        return do_types_match

    def _compare_no(self, actual_no: int, expected_no: int) -> bool:
        """Compares actual retrieved and expected document numbers for exact search

        :param actual_no: The number of the retrieved document
        :param expected_no: The number expected by the client
        :return: `True` if numbers match, `False` otherwise
        """

        do_numbers_match = int(actual_no) == int(expected_no)
        logger.info(f"Comparing actual no. {actual_no} vs expected {expected_no}")
        logger.info(f"Match {do_numbers_match}")

        return do_numbers_match

    def _compare_issuer(self, actual_issuer, expected_issuer) -> bool:
        """Compares actual retrieved and expected document issuers for exact search

        :param actual_issuer: The issuer of the retrieved document
        :param expected_issuer: The issuer expected by the client
        :return: `True` if issuers match, `False` otherwise
        """

        actual_canonical = get_canonical_issuer(actual_issuer)
        expected_canonical = get_canonical_issuer(expected_issuer)

        logger.info(
            f"Comparing normalized issuers: '{actual_canonical}' vs '{expected_canonical}'"
        )

        do_issuers_match = (
            expected_canonical in actual_canonical
            or actual_canonical in expected_canonical
        )
        logger.info(f"Match: {do_issuers_match}")

        return do_issuers_match
