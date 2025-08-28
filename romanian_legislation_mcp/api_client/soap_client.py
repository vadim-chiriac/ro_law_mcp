from __future__ import annotations
from datetime import datetime, timedelta, timezone
from zeep import Client
from typing import List, Optional
import logging
import signal
from contextlib import contextmanager

from romanian_legislation_mcp.api_client.legislation_document import LegislationDocument
from romanian_legislation_mcp.api_client.utils import extract_field_safely, extract_date_safely

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Custom timeout exception for SOAP operations."""
    pass


@contextmanager
def timeout_handler(seconds):
    """Context manager for handling timeouts on Windows and Unix systems."""
    def timeout_function(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    
    # Set up signal handler for Unix-like systems
    if hasattr(signal, 'SIGALRM'):
        old_handler = signal.signal(signal.SIGALRM, timeout_function)
        signal.alarm(seconds)
    
    try:
        yield
    finally:
        # Clean up signal handler for Unix-like systems
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)


class SoapClient:
    """Class responsible for 🧼 SOAP API connection."""

    def __init__(self, wsdl_url: str, connection_timeout: int, read_timeout: int):
        """Do not call this directly, use `create` class method instead."""

        self.wsdl_url: str = wsdl_url
        self.connection_timeout = connection_timeout
        self.read_timeout = read_timeout
        self.client: Client = None
        self.token: str = None
        self.token_expires_at = None

    @classmethod
    def create(
        cls, wsdl_url: str, connection_timeout: int = 5, read_timeout: int = 5
    ) -> "SoapClient":
        """Factory method for instance creation

        :param wsdl_url: URL to the WSDL service.
        :return: New `SoapClient` instance.
        :raises ConnectionError: If SOAP client initialization fails.
        """

        instance = cls(wsdl_url, connection_timeout, read_timeout)
        try:
            instance.client = instance._create_soap_client()
        except Exception as e:
            raise ConnectionError(f"Failed to create SOAP client: {e}")

        return instance

    # Public API methods (for search service calls)
    async def search_raw(self, **kwargs) -> List[LegislationDocument]:
        """Raw search with multiple parameters.

        :param kwargs: Search parameters like title, number, year, issuer etc.
        :return: List of `LegislationDocument` objects matching the advanced search criteria.
        """
        search_model = self._create_search_model(**kwargs)
        return self._execute_search(search_model)

    # Private methods
    def _create_soap_client(self) -> Client:
        """Creates SOAP client with configured timeouts."""
        from zeep.transports import Transport
        from requests import Session
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        session = Session()
        session.timeout = (self.connection_timeout, self.read_timeout)
        
        retry_strategy = Retry(
            total=0,  
            connect=0,
            read=0,
            status=0,
            backoff_factor=0,
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        logger.info(f"Session timeout set to: {session.timeout}")

        transport = Transport(session=session, timeout=self.connection_timeout)
        logger.info(f"Transport session timeout: {transport.session.timeout}")

        return Client(self.wsdl_url, transport=transport)

    def _get_fresh_token(self):
        """Gets a new token from the SOAP API with timeout protection."""
        logger.info("Attempting to get fresh token...")
        
        try:
            # For Windows compatibility, we'll use a different approach
            if hasattr(signal, 'SIGALRM'):
                # Unix-like systems
                with timeout_handler(max(self.connection_timeout, self.read_timeout) + 2):
                    self.token = self.client.service.GetToken()
            else:
                # Windows systems - rely on session timeouts
                import threading
                import time
                
                result = [None]
                exception = [None]
                
                def get_token():
                    try:
                        result[0] = self.client.service.GetToken()
                    except Exception as e:
                        exception[0] = e
                
                # Start token retrieval in a separate thread
                thread = threading.Thread(target=get_token)
                thread.daemon = True
                thread.start()
                
                # Wait for completion with timeout
                timeout_duration = max(self.connection_timeout, self.read_timeout) + 5
                thread.join(timeout=timeout_duration)
                
                if thread.is_alive():
                    logger.error(f"Token retrieval timed out after {timeout_duration} seconds")
                    raise TimeoutError(f"Token retrieval timed out after {timeout_duration} seconds")
                
                if exception[0] is not None:
                    raise exception[0]
                
                self.token = result[0]
            
            if self.token:
                self.token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
                logger.info("Successfully obtained fresh token")
            else:
                raise ConnectionError("Received empty token from API")
                
        except TimeoutError as e:
            logger.error(f"Token retrieval timeout: {e}")
            raise ConnectionError(f"Token retrieval timed out: {e}")
        except Exception as e:
            logger.error(f"Connection error during token retrieval: {e}")
            raise ConnectionError(f"Failed to get token: {e}")

    def _ensure_valid_token(self) -> bool:
        """Gets a new token from the SOAP API if it does not exist or is expired."""

        if self.token is None or self._is_token_expired():
            logger.info("Token expired or missing, getting fresh token.")
            self._get_fresh_token()
            return True
        else:
            return False

    def _is_token_expired(self) -> bool:
        """Checks if current SOAP API token is expired."""

        if self.token_expires_at is None:
            return True
        return datetime.now(timezone.utc) >= self.token_expires_at

    def _execute_search(self, search_model: dict) -> List[LegislationDocument]:
        """Executes a search with the given search model.

        :param search_model: The built search model to use with the SOAP API.
        :return: List of `LegislationDocument` matching the search model.
        """
        requested_size = search_model["RezultatePagina"]

        if requested_size <= 10:
            return self._execute_page_search(search_model)

        all_results = []

        # Ceiling divison trick which Claude taught me :)
        pages_needed = (requested_size + 9) // 10

        for page_index in range(pages_needed):
            page_search_model = search_model.copy()
            page_search_model["NumarPagina"] = page_index
            page_search_model["RezultatePagina"] = 10

            page_results = self._execute_page_search(page_search_model)

            all_results.extend(page_results)

            if len(page_results) < 10:
                break

        return all_results[:requested_size]

    def _execute_page_search(
        self, search_model: dict, retry: bool = True
    ) -> List[LegislationDocument]:
        """Executes a single page search.

        :param search_model: The search model to use.
        :param retry: Whether to retry a failed search
        :return: A list of `LegislationDocument` corresponding to the page returned from the SOAP API.
        """
        self._ensure_valid_token()
        try:
            # Add timeout protection for search operations as well
            if hasattr(signal, 'SIGALRM'):
                # Unix-like systems
                with timeout_handler(max(self.connection_timeout, self.read_timeout) + 2):
                    results = self.client.service.Search(search_model, self.token)
            else:
                # Windows systems - rely on session timeouts and threading
                import threading
                
                result = [None]
                exception = [None]
                
                def execute_search():
                    try:
                        result[0] = self.client.service.Search(search_model, self.token)
                    except Exception as e:
                        exception[0] = e
                
                thread = threading.Thread(target=execute_search)
                thread.daemon = True
                thread.start()
                
                timeout_duration = max(self.connection_timeout, self.read_timeout) + 5
                thread.join(timeout=timeout_duration)
                
                if thread.is_alive():
                    logger.error(f"Search operation timed out after {timeout_duration} seconds")
                    raise TimeoutError(f"Search operation timed out after {timeout_duration} seconds")
                
                if exception[0] is not None:
                    raise exception[0]
                
                results = result[0]
                
            parsed_results = self._parse_search_results(results)
            return parsed_results
            
        except TimeoutError as e:
            if retry:
                logger.warning(f"Search timed out for page no. {search_model['NumarPagina']}, retrying...")
                try:
                    self._ensure_valid_token()
                    return self._execute_page_search(search_model, False)
                except Exception as retry_error:
                    raise ConnectionError(f"Search timeout and retry failed for page no. {search_model['NumarPagina']}: {retry_error}")
            else:
                raise ConnectionError(f"Search timed out for page no. {search_model['NumarPagina']}: {e}")
                
        except Exception as e:
            if retry:
                logger.info(f"Exception: {e}")
                logger.warning(
                    f"Page searched failed for page no. {search_model['NumarPagina']}, retrying..."
                )
                try:
                    self._ensure_valid_token()
                    return self._execute_page_search(search_model, False)
                except Exception as retry_error:
                    raise ConnectionError(f"Search failed and retry failed for page no. {search_model['NumarPagina']}: {retry_error}")
            else:
                raise ConnectionError(
                    f"Page searched failed for page no. {search_model['NumarPagina']}: {e}"
                )

    def _parse_search_results(
        self, raw_results: List[dict]
    ) -> List[LegislationDocument]:
        """Converts the raw response from the SOAP API into a more generally readable format.

        :param raw_results: List of raw results received from the SOAP API.
        :return: List of parsed results.
        """
        if not raw_results or not isinstance(raw_results, (list, tuple)):
            return []

        parsed_results = []
        for record in raw_results:
            parsed_result = self._parse_single_record(record)
            if parsed_result:
                parsed_results.append(parsed_result)

        return parsed_results

    def _parse_single_record(self, record: dict) -> Optional[LegislationDocument]:
        """Parsed a single raw record from the SOAP API response.

        :param record: The record to parse .
        :return: A `LegislationDocument` object based on the record, or `None` if parsing failed.
        """

        title = extract_field_safely(record, "Titlu")
        number = extract_field_safely(record, "Numar")
        document_type = extract_field_safely(record, "TipAct")
        issuer = extract_field_safely(record, "Emitent")
        effective_date_string = extract_field_safely(record, "DataVigoare")
        effective_date = extract_date_safely(effective_date_string)
        text = extract_field_safely(record, "Text")
        publication = extract_field_safely(record, "Publicatie", False)
        url = extract_field_safely(record, "LinkHtml", False)

        if not all([title, number, document_type, issuer, effective_date, text]):
            logger.warning("Skipping record due to missing fields.")
            return None



        parsed_result = LegislationDocument(
            title=title,
            number=number,
            document_type=document_type,
            issuer=issuer,
            effective_date=effective_date,
            text=text,
            publication=publication,
            url=url,
        )

        return parsed_result

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
        :param year: Filter results by year of issuance. Note: API may return documents
                    from nearby years if no exact matches exist for the specified year.
        :param page: Page number for pagination (0-based)
        :param page_size: Maximum number of results per page
        :return: Dictionary formatted for SOAP API search request
        """
        if page < 0:
            raise ValueError("Page number cannot be negative.")

        if page_size <= 0:
            raise ValueError("Page size must be positive.")

        if page_size > 100:
            raise ValueError("Page size cannot exceed 100")
        
        return {
            "NumarPagina": page,
            "RezultatePagina": page_size,
            "SearchAn": year,
            "SearchNumar": number,
            "SearchTitlu": title,
            "SearchText": text,
        }
