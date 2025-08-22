from dataclasses import dataclass
import random
from typing import Any, Dict, List, Optional

from romanian_legislation_mcp.api_client.legislation_document import LegislationDocument
from romanian_legislation_mcp.document_amendments.amendment import Amendment
from romanian_legislation_mcp.structured_document.element import (
    DocumentElement,
    DocumentElementType,
)
from romanian_legislation_mcp.document_amendments.amendment_parser import AmendmentData
from romanian_legislation_mcp.document_search.content_search import text_search

import logging


logger = logging.getLogger(__name__)


@dataclass
class ResultElement:
    number: str
    content: str
    amendments: List[Amendment] | None
    start_pos: int
    end_pos: int


class StructuredDocument:
    """Class responsible for retrieving element content from a `DocumentPart`"""

    def __init__(
        self,
        base_document: LegislationDocument,
        top_element: DocumentElement,
        amendment_data: Optional[AmendmentData] = None,
    ):
        """Creates a new document model.

        :param document: The underlying `LegislationDocument` instance.
        :param top_element: The
        """
        self.base_document = base_document
        self.top_element = top_element
        self.articles: dict[str, DocumentElement] = {}
        self.elements: dict[str, DocumentElement] = {}
        self.amendment_data = amendment_data
        self.art_amendment_map: dict[str, list[Amendment]] = {}
        self._document_structure_view: Optional[dict] = None

    def add_article(self, article: DocumentElement):
        if article.type_name != DocumentElementType.ARTICLE:
            logger.warning(
                f"Trying to add non-article element as article: {article.title}"
            )
            return

        art_no = article.number
        if self.articles.get(art_no, None) is not None:
            logger.warning(f"Article already exists: {art_no}")
            return

        self.articles[art_no] = article

    def add_element(self, element: DocumentElement):
        if element is None:
            logger.warning("Trying to add None element to model.")

        if (
            element.type_name == DocumentElementType.ARTICLE
            or element.type_name == DocumentElementType.TOP
        ):
            logger.warning("Trying to add invalid element to model")

        if self.elements.get(element.id, None) is not None:
            logger.warning(f"Element already exists: {element.id}")
            return

        self.elements[element.id] = element

    def get_article(self, art_no: str) -> Optional[ResultElement]:
        article = self.articles.get(art_no, None)
        if article is None:
            return None

        content = self.base_document.text[article.start_pos : article.end_pos]
        amendments = self._get_amendments_for_article(article)
        result = ResultElement(
            article.number, content, amendments, article.start_pos, article.end_pos
        )

        return result

    def get_random_id(self) -> str:
        pos = 50
        logger.info(f"Returning random pos: {pos}")
        i = 0
        for key in self.elements:
            if i == pos:
                return self.elements[key].id
            i += 1
        return None

    def get_element_by_id(
        self, id: str, include_article_changes: bool = True
    ) -> Optional[ResultElement]:
        element = self.elements.get(id, None)

        if element is None:
            return None

        content = self.base_document.text[element.start_pos : element.end_pos]

        if not include_article_changes:
            return ResultElement(element.number, content)

        amendments = self._get_amendments_for_art_children(element)

        return ResultElement(
            element.number, content, amendments, element.start_pos, element.end_pos
        )

    def get_json_structure(self) -> dict:
        """Returns a hierarchical structure of the document suitable for LLM consumption.

        Builds and caches the structure on first call, returns cached version on subsequent calls.

        Returns:
            dict: Hierarchical structure with type, number, title, id, and article ranges
        """
        if self._document_structure_view is None:
            self._document_structure_view = self._build_json_structure()
        return self._document_structure_view

    def get_text(self, start_pos=0, end_pos=-1) -> Optional[str]:
        try:
            return self.base_document.text[start_pos:end_pos]
        except Exception as e:
            logger.warning(f"Error getting text for {self.base_document.title}: ")
            logger.warning(e)
            return None

    def search_in_text(
        self,
        search_query: str,
        start_pos: int = 0,
        end_pos: int = -1,
        max_excerpts: int = 5,
        excerpt_context_chars: int = 500,
    ) -> Dict[str, Any]:
        text = self.get_text(start_pos, end_pos)
        if text is None:
            return {"error": f"document: {self.base_document.title}"}
        return text_search(text, search_query, max_excerpts, excerpt_context_chars)

    def _build_json_structure(self) -> dict:
        """Builds the hierarchical document structure."""

        def _build_element_structure(element: DocumentElement) -> dict:
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
                if child.type_name == DocumentElementType.ARTICLE
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

            non_article_children = [
                child
                for child in element.children
                if child.type_name != DocumentElementType.ARTICLE
            ]
            if non_article_children:
                structure["children"] = [
                    _build_element_structure(child) for child in non_article_children
                ]

            return structure

        return _build_element_structure(self.top_element)

    def _get_amendments_for_art_children(
        self, element: DocumentElement
    ) -> List[Amendment]:
        if element.type_name == DocumentElementType.ARTICLE:
            return self._get_amendments_for_article(element.number)

        children = element.children.copy()
        amendments = []
        for child in children:
            if child.type_name == DocumentElementType.ARTICLE:
                amendments.append(self._get_amendments_for_article(child))
            else:
                amendments.append(self._get_amendments_for_art_children(child))

        amendments = [amendment for amendment in amendments if amendment is not None]
        return amendments

    def _get_amendments_for_article(
        self, article: DocumentElement
    ) -> List[Amendment] | None:
        if self.art_amendment_map.get(article.number, None) is not None:
            return self.art_amendment_map[article.number]

        if self.amendment_data is None:
            return None

        if not self.amendment_data.has_amendments():
            return None

        for amendment in self.amendment_data.amendments:
            if amendment.target_element_type != DocumentElementType.ARTICLE:
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

        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{end}")

        return ", ".join(ranges)
