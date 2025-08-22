from dataclasses import dataclass
from typing import Any, Dict, Optional

from romanian_legislation_mcp.api_client.legislation_document import LegislationDocument
from romanian_legislation_mcp.document_amendments.amendment import Amendment
from romanian_legislation_mcp.document_model.model import DocumentPart, DocumentPartType
from romanian_legislation_mcp.document_amendments.amendment_parser import AmendmentData
from romanian_legislation_mcp.document_search.content_search import text_search

import logging


logger = logging.getLogger(__name__)


@dataclass
class ResultElement:
    number: str
    content: str
    amendments: Optional[list[Amendment]] = None


class ModelController:
    """Class responsible for retrieving element content from a `DocumentPart`"""

    def __init__(
        self,
        document: LegislationDocument,
        top_element: DocumentPart,
        amendment_data: Optional[AmendmentData] = None,
    ):
        """Creates a new document model.

        :param document: The underlying `LegislationDocument` instance.
        :param top_element: The
        """
        self.document = document
        self.top = top_element
        self.articles: dict[str, DocumentPart] = {}
        self.elements: dict[str, DocumentPart] = {}
        self.amendment_data = amendment_data
        self.art_amendment_map: dict[str, list[Amendment]] = {}
        self._document_structure: Optional[dict] = None

    def add_article(self, article: DocumentPart):
        if article.type_name != DocumentPartType.ARTICLE:
            logger.warning(
                f"Trying to add non-article element as article: {article.title}"
            )
            return

        art_no = article.number
        if self.articles.get(art_no, None) is not None:
            logger.warning(f"Article already exists: {art_no}")
            return

        self.articles[art_no] = article

    def add_element(self, element: DocumentPart):
        if element is None:
            logger.warning("Trying to add None element to model.")

        if (
            element.type_name == DocumentPartType.ARTICLE
            or element.type_name == DocumentPartType.TOP
        ):
            logger.warning("Trying to add invalid element to model")

        if self.elements.get(element.id, None) is not None:
            logger.warning(f"Element already exists: {element.id}")
            return

        self.elements[element.id] = element

    def get_article(self, art_no: str) -> Optional[ResultElement]:
        art_data = self.articles.get(art_no, None)
        if art_data is None:
            return None

        content = self.document.text[art_data.start_pos : art_data.end_pos]
        amendments = self._get_amendments_for_article(art_data)
        article = ResultElement(art_data.number, content, amendments)

        return article

    def get_element_by_id(self, id: str) -> Optional[ResultElement]:
        e_data = self.elements.get(id, None)
        if e_data is not None:
            content = self.document.text[e_data.start_pos : e_data.end_pos]
        element = ResultElement(e_data.number, content)
        return element

    def get_document_structure(self) -> dict:
        """Returns a hierarchical structure of the document suitable for LLM consumption.

        Builds and caches the structure on first call, returns cached version on subsequent calls.

        Returns:
            dict: Hierarchical structure with type, number, title, id, and article ranges
        """
        if self._document_structure is None:
            self._document_structure = self._build_document_structure()
        return self._document_structure

    def search_in_text(
        self,
        search_query: str,
        start_pos: int = 0,
        end_pos: int = -1,
        max_excerpts: int = 5,
        excerpt_context_chars: int = 500,
    ) -> Dict[str, Any]:
        text = self.document.text[start_pos:end_pos]
        return text_search(text, search_query, max_excerpts, excerpt_context_chars)

    def _build_document_structure(self) -> dict:
        """Builds the hierarchical document structure."""

        def _build_element_structure(element: DocumentPart) -> dict:
            structure = {
                "type": element.type_name.name.lower(),
                "number": element.number,
                "title": element.title,
                "id": str(element.id),
            }

            # Get direct article children
            article_children = [
                child
                for child in element.children
                if child.type_name == DocumentPartType.ARTICLE
            ]

            if article_children:
                numeric_articles = []
                other_articles = []

                for article in article_children:
                    if article.number.isdigit():
                        numeric_articles.append(int(article.number))
                    else:
                        other_articles.append(article.number)

                if numeric_articles:
                    numeric_articles.sort()
                    structure["article_range"] = self._format_numeric_range(
                        numeric_articles
                    )

                if other_articles:
                    structure["other_articles"] = other_articles

            # Recursively process non-article children
            non_article_children = [
                child
                for child in element.children
                if child.type_name != DocumentPartType.ARTICLE
            ]
            if non_article_children:
                structure["children"] = [
                    _build_element_structure(child) for child in non_article_children
                ]

            return structure

        return _build_element_structure(self.top)

    def _get_amendments_for_article(self, article: DocumentPart):
        if self.art_amendment_map.get(article.number, None) is not None:
            return self.art_amendment_map[article.number]

        if self.amendment_data is None:
            return None

        if not self.amendment_data.has_amendments():
            return None

        for amendment in self.amendment_data.amendments:
            if amendment.target_element_type != DocumentPartType.ARTICLE:
                continue

            if amendment.target_element_no != article.number:
                continue

            map = self.art_amendment_map.get(article.number, None)
            if map is None:
                map = []
                self.art_amendment_map[article.number] = map

            map.append(amendment)

        amendments = self.art_amendment_map.get(article.number, None)
        return amendments

    def _format_numeric_range(self, numbers: list[int]) -> str:
        """Formats a list of numbers into readable ranges (e.g., '1-5, 7, 9-12')"""
        if not numbers:
            return ""

        ranges = []
        start = numbers[0]
        end = numbers[0]

        for i in range(1, len(numbers)):
            if numbers[i] == end + 1:
                end = numbers[i]
            else:
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{end}")
                start = end = numbers[i]

        # Add the last range
        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{end}")

        return ", ".join(ranges)
