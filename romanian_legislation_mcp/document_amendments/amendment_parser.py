from romanian_legislation_mcp.api_client.legislation_document import LegislationDocument
from romanian_legislation_mcp.document_model.part import DocumentPartType

from dataclasses import dataclass
from typing import Optional
import requests
import logging
import html
import re
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


@dataclass
class Amendment:
    amendment_type: str
    source_str: str
    source_url: str
    target_element_type: DocumentPartType
    target_element_no: Optional[str] = None


@dataclass
class AmendmentData:
    amendments: list[Amendment]
    is_document_repealed: bool
    document: Optional[LegislationDocument] = None


class AmendmentParser:
    """Class that tries to obtain the list of amendments to legal document.
    Unfortunately, the SOAP API does not return the consolidated form of legal documents.
    We can therefore try to get a list of amendments made to the document to pass to clients, so
    they know at least if a specific article or the document itself was amendmentd/repelead/subject
    to other amendments.
    """

    def __init__(self, url: str, request_timeout: int = 10):
        self.url = url
        self.request_timeout = request_timeout
        self.session = requests.Session()

    def get_amendment_data(self) -> AmendmentData:
        """
        Fetch and parse document HTML to try to determine if it's repealed or in force.

        :param url: The HTML URL of the legislation document.
        :return: Dict containg the list of amendments made to the legal document.
        """

        url = self.url

        if not url:
            return {}

        try:
            logger.info(f"Parsing amendments for {url}")
            doc_id = url.split("/")[-1]
            return self._parse_amendments(doc_id)

        except Exception as e:
            logger.warning(
                f"Failed to determine document amendments for url: {url}: {e}"
            )
            return {}

    def _parse_amendments(self, doc_id: str) -> AmendmentData:
        """Parse HTML amendments content to build structured data containing document amendments."""

        try:
            actions_response = requests.post(
                "https://legislatie.just.ro/Public/actiuniSuferite", {"contor": doc_id}
            )
            actions_response.raise_for_status()

            json_data = actions_response.json()
            if "acte" in json_data:
                html_content = json_data["acte"]
                decoded_html = html_content.encode().decode("unicode_escape")
                decoded_html = html.unescape(decoded_html)

                logger.debug(f"Decoded HTML content: {decoded_html}")

                amendments = self._parse_amendments_from_html(decoded_html)
                is_repealed = any(
                    amendment.amendment_type.lower() == "repealed"
                    and amendment.target_element_type == DocumentPartType.TOP
                    for amendment in amendments
                )
                document_amendments = AmendmentData(
                    amendments=amendments, is_document_repealed=is_repealed
                )
                return document_amendments
            else:
                logger.warning("No 'acte' field found in JSON response")

        except Exception as e:
            logger.warning(f"Failed to parse HTML: {e}")
            return {}

    def _parse_amendments_from_html(self, html_content: str) -> list[Amendment]:
        """
        Parse the HTML table to extract amendments metadata.

        :param html_content: Decoded HTML content containing the amendments table
        :return: List of dictionaries with amendment metadata
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            amendments: list[Amendment] = []

            rows = soup.find_all("tr")

            for row in rows:
                cells = row.find_all("td")

                if len(cells) != 3:
                    continue

                target_str = cells[0].get_text(strip=True)
                # Header row for HTML view, we are skipping this
                if target_str in ["SECTIUNE ACT", "TIP OPERATIUNE"]:
                    continue

                target_type: DocumentPartType = None
                target_no: str = None
                if target_str == "Actul":
                    target_type = DocumentPartType.TOP

                if self._is_article(target_str):
                    article_no = self._try_get_article_number(target_str)
                    logger.info(f"Article no str: {target_str}")
                    logger.info(f"Article no: {article_no}")
                    if article_no is not None:
                        target_type = DocumentPartType.ARTICLE
                        target_no = article_no

                amendment_type_raw = cells[1].get_text(strip=True)
                source_cell = cells[2]

                source_link = source_cell.find("a")
                if source_link:
                    source_text = source_link.get_text(strip=True)
                    source_href = source_link.get("href", "")
                    if source_href.startswith("~/../../../"):
                        source_href = "https://legislatie.just.ro/" + source_href[11:]
                else:
                    source_text = source_cell.get_text(strip=True)
                    source_href = None

                if source_text:
                    source_text = re.sub(r"\s{2,}", " ", source_text)

                amendment_type = self._normalize_amendment_type(amendment_type_raw)

                if target_type and amendment_type and source_text:
                    amendment = Amendment(
                        amendment_type=amendment_type,
                        target_element_type=target_type,
                        target_element_no=target_no,
                        source_str=source_text,
                        source_url=source_href,
                    )
                    amendments.append(amendment)
                    logger.debug(f"Parsed amendment: {amendment}")

            return amendments

        except Exception as e:
            logger.warning(f"Failed to parse amendments from HTML: {e}")
            return []

    def _normalize_amendment_type(self, raw_type: str) -> str:
        """
        Normalize the amendment type from Romanian to English.

        :param raw_type: Raw amendment type in Romanian
        :return: Normalized amendment type in English
        """
        raw_upper = raw_type.upper().strip().replace(" ", "")

        type_mapping = {
            "ABROGATDE": "repealed",
            "ABROGATPARTIALDE": "partially repealed",
            "MODIFICATDE": "amended",
            "COMPLETATDE": "supplemented",
            "SUSPENDATDE": "suspended",
            "REPUBLICAT": "republished",
            "INTRATINVIGOARE": "entered into force",
            "RECTIFICATDE": "corrected",
        }

        return type_mapping.get(raw_upper, raw_type.lower())

    def _is_article(self, row: str):
        return row.split()[0] == "ART."

    def _try_get_article_number(self, raw_text: str) -> str:
        try:
            number = raw_text.split()[1]
            return number
        except Exception as e:
            logger.warning(e)
            return None
