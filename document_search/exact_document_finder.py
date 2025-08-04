from typing import List, Optional
from api_client.soap_client import SoapClient
from api_client.legislation_document import LegislationDocument
from document_search.issuer_mappings import get_canonical_issuer
from document_search.document_type_mappings import get_canonical_document_type
import logging

logger = logging.getLogger(__name__)


class ExactDocumentFinder:
    """Class responsible for trying to retrive a document by its unique identifiers,
    meaning type, number, year and issuer"""

    def __init__(self, legislation_client: SoapClient):
        """Initializes a new `ExactDocumentFinder`

        :param legislation_client: The underlying `SoapClient` for searching
        """

        self.client = legislation_client

    async def find_exact_document(
        self, document_type: str, number: int, year: int, issuer: str
    ) -> Optional[LegislationDocument]:
        """Tries to find an exact match for the given parameters

        :param document_type: The type of the document (e.g. "lege", "hotărâre").
        :param number: The number of the document.
        :param year: The issuance year of the document. This might be different than publication year or entry into force year.
        :param issuer: The issuing authority of the document (e.g. Guvernul României)
        """
        search_text = ""
        search_text += get_canonical_document_type(document_type, issuer)
        search_text += f" {number}/{year}"

        logger.info(f"Trying to find match for {search_text}")
        results = await self.client.search_raw(title=search_text)
        if not results:
            return None

        logger.info(f"Found {len(results)} initial results.")
        exact_match = self._get_exact_match(
            all_results=results,
            expected_type=document_type,
            expected_no=number,
            expected_issuer=issuer,
        )

        return exact_match

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

        for result in all_results:
            _type = result.document_type
            issuer = result.issuer

            if not self._compare_document_type(_type, expected_type, issuer):
                continue

            number = result.number
            if not self._compare_no(number, expected_no):
                continue

            if not self._compare_issuer(issuer, expected_issuer):
                continue

            return result

        return None

    def _compare_document_type(
        self, actual_type: str, expected_type: str, issuer: str
    ) -> bool:
        """Compares actual retrieved and expected document types for exact search

        :param actual_type: The type of the retrieved document
        :param expected_type: The type expected by the client
        :return: `True` if types match, `False` otherwise
        """

        actual_canonical = get_canonical_document_type(actual_type, issuer)
        expected_canonical = get_canonical_document_type(expected_type, issuer)

        logger.info(f"Comparing normalized types: '{actual_canonical}' vs '{expected_canonical}'")

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

        do_issuers_match = expected_canonical in actual_canonical or actual_canonical in expected_canonical
        logger.info(f"Match: {do_issuers_match}")

        return do_issuers_match
