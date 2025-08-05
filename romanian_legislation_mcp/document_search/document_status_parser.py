from enum import Enum
from bs4 import BeautifulSoup
import requests
import logging

logger = logging.getLogger(__name__)


class DocumentStatus(Enum):
    ACTIVE = "active"
    REPEALED = "repealed"
    UNKNOWN = "unknown"


class DocumentStatusParser:
    """Class that tries to obtain current legal document status from its HTML content"""

    def __init__(self, request_timeout: int = 10):
        self.request_timeout = request_timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def get_document_status(self, url: str) -> DocumentStatus:
        """
        Fetch and parse document HTML to try to determine if it's repealed or in force.

        :param url: The HTML URL of the legislation document
        :return: `DocumentStatus` indicating if document is active, repealed, or unknown
        """
        
        if not url:
            return DocumentStatus.UNKNOWN
        
        try:
            html_content = self._fetch_html(url)
            if not html_content:
                return DocumentStatus.UNKNOWN
            
            return self._parse_status_from_html(html_content)
        
        except Exception as e:
            logger.warning(f"Failed to determine document status for url: {url}: {e}")
            return DocumentStatus.UNKNOWN
        
    def _fetch_html(self, url: str):
        """Fetch HTML content from the given URL."""
        
        try:
            response = self.session.get(url, timeout=self.request_timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch HTML from {url}: {e}")
            return None
        
    def _parse_status_from_html(self, html_content: str) -> DocumentStatus:
        """Parse HTML content to determine document status"""
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            doc_status_element = soup.find('span', id='fisaact')
            if not doc_status_element:
                logger.debug("Status info not found in HTML content.")
                return DocumentStatus.UNKNOWN
            
            doc_status_text = doc_status_element.get_text()
            
            if "ABROGAT DE" in doc_status_text.upper():
                logger.debug("Found 'ABROGAT DE' - document is repealed.")
                return DocumentStatus.REPEALED
            
            return DocumentStatus.ACTIVE
        
        except Exception as e:
            logger.warning(f"Failed to parse HTML: {e}")
            return DocumentStatus.UNKNOWN
                
            
            
