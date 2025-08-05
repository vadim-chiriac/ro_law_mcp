import requests
import logging
import html
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class DocumentStatusParser:
    """Class that tries to obtain the list of changes to legal document."""

    def __init__(self, request_timeout: int = 10):
        self.request_timeout = request_timeout
        self.session = requests.Session()

    def get_document_status(self, url: str) -> dict:
        """
        Fetch and parse document HTML to try to determine if it's repealed or in force.

        :param url: The HTML URL of the legislation document
        :return: `DocumentStatus` indicating if document is active, repealed, or unknown
        """

        if not url:
            return {}

        try:
            doc_id = url.split("/")[-1]
            return self._parse_status(doc_id)

        except Exception as e:
            logger.warning(f"Failed to determine document status for url: {url}: {e}")
            return {}

    def _parse_status(self, doc_id: str) -> dict:
        """Parse HTML content to determine document status"""

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

                changes = self._parse_changes_from_html(decoded_html)

                return {
                    "changes": changes,
                    "is_repealed": any(
                        change.get("change_type", "").lower() == "repealed"
                        and change.get("target", "").lower() == "entire document"
                        for change in changes
                    ),
                    "total_changes": len(changes),
                }
            else:
                logger.warning("No 'acte' field found in JSON response")

        except Exception as e:
            logger.warning(f"Failed to parse HTML: {e}")
            return {}

    def _parse_changes_from_html(self, html_content: str) -> list:
        """
        Parse the HTML table to extract changes metadata.

        :param html_content: Decoded HTML content containing the changes table
        :return: List of dictionaries with change metadata
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            changes = []

            rows = soup.find_all("tr")

            for row in rows:
                cells = row.find_all("td")

                if len(cells) != 3:
                    continue

                target = cells[0].get_text(strip=True)
                if target == "Actul":
                    target = "entire document"

                change_type_raw = cells[1].get_text(strip=True)
                source_cell = cells[2]

                # Header row for HTML view, we are skipping this
                if target in ["SECTIUNE ACT", "TIP OPERATIUNE"]:
                    continue

                source_link = source_cell.find("a")
                if source_link:
                    source_text = source_link.get_text(strip=True)
                    source_href = source_link.get("href", "")
                    if source_href.startswith("~/../../../"):
                        source_href = "https://legislatie.just.ro/" + source_href[11:]
                else:
                    source_text = source_cell.get_text(strip=True)
                    source_href = None

                # Clean up multiple consecutive whitespaces in source text
                if source_text:
                    source_text = re.sub(r"\s{2,}", " ", source_text)

                change_type = self._normalize_change_type(change_type_raw)

                if target and change_type and source_text:
                    change = {
                        "target": target,
                        "change_type": change_type,
                        "source": source_text,
                        "source_url": source_href,
                    }
                    changes.append(change)
                    logger.debug(f"Parsed change: {change}")

            return changes

        except Exception as e:
            logger.warning(f"Failed to parse changes from HTML: {e}")
            return []

    def _normalize_change_type(self, raw_type: str) -> str:
        """
        Normalize the change type from Romanian to English.

        :param raw_type: Raw change type in Romanian
        :return: Normalized change type in English
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
        }

        return type_mapping.get(raw_upper, raw_type.lower())
