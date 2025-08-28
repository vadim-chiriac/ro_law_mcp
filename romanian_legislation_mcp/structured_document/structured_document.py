from dataclasses import dataclass
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
    type: str
    number: str
    title: str
    content: str
    start_pos: int
    end_pos: int

@dataclass
class ResultArticle(ResultElement):
    amendments: AmendmentData | None
    is_latest_version: bool


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
        

    def add_article(self, article: DocumentElement):
        if article.type_name != DocumentElementType.ARTICLE:
            logger.warning(
                f"Trying to add non-article element as article: {article.title}"
            )
            return

        art_no = article.number
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

        self.elements[str(element.id)] = element

    def get_articles(
        self, art_no_or_list: str | list[str]
    ) -> List[ResultArticle | dict]:
        if isinstance(art_no_or_list, str):
            art_no_or_list = [art_no_or_list]

        results = []
        for art_no in art_no_or_list:
            article = self._get_article(art_no)
            if article is not None:
                results.append(article)
            else:
                results.append({"error": f"Article {art_no} not found."})

        return results

    def _get_article(self, art_no: str) -> Optional[ResultArticle]:
        article = self.articles.get(art_no, None)
        if article is None:
            return None

        content = self.base_document.text[article.start_pos : article.end_pos]
        amendments = self._get_amendments_for_article(article)
        result = ResultArticle(
            type=article.type_name.to_string(),
            number=article.number,
            title=article.title,
            content=content,
            start_pos=article.start_pos,
            end_pos=article.end_pos,
            amendments=amendments,
            is_latest_version=len(amendments) == 0,
        )

        return result

    def get_element_by_id(self, element_id: str) -> Optional[ResultElement]:
        element = self.elements.get(element_id, None)

        if element is None:
            return None

        content = self.base_document.text[element.start_pos : element.end_pos]

        return ResultElement(
            type=element.type_name.to_string(),
            number=element.number,
            title=element.title,
            content=content,
            start_pos=element.start_pos,
            end_pos=element.end_pos,
        )

    def search_in_element(
        self,
        element_id: str,
        query: str,
        start_pos: int = 0,
        end_pos: int = -1,
        max_excerpts: int = 5,
        excerpt_context_chars: int = 250,
        include_article_changes: bool = False,
    ) -> Dict[str, Any]:
        element = self.elements.get(element_id, None)

        if element is None:
            return {
                "error": f"Element with id {element_id} not found in parent {self.base_document.title}"
            }

        element_text = self.get_text(element.start_pos, element.end_pos)
        text = element_text[start_pos:end_pos]
        excerpts = text_search(text, query, max_excerpts, excerpt_context_chars)

        for excerpt in excerpts.get("excerpts", []):
            excerpt["match_start_in_element"] = (
                excerpt["match_start_in_text"] + start_pos
            )
            excerpt["match_start_in_document"] = (
                excerpt["match_start_in_element"] + element.start_pos
            )

        result = {"element_id": element.id, "excerpt_data": excerpts}

        if include_article_changes:
            amendments = self._get_amendments_for_art_children(element)
            result["article_amendments"] = amendments

        return result

    def get_text(self, start_pos=0, end_pos=-1) -> Optional[str]:
        try:
            return self.base_document.text[start_pos:end_pos]
        except Exception as e:
            logger.warning(f"Error getting text for {self.base_document.title}: ")
            logger.warning(e)
            return None

    def get_structural_amendment_data(self) -> AmendmentData:
        amendments = [
            a
            for a in self.amendment_data.amendments
            if a.target_element_type != DocumentElementType.ARTICLE.to_string()
        ]

        data = AmendmentData(amendments, self.amendment_data.is_document_repealed)
        return data

    def get_element_structure(self, element_id: str, max_depth: int = 0) -> dict:
        """Builds the hierarchical element structure."""

        def _build_element_structure(element: DocumentElement, max_depth: int, curr_depth: int) -> dict:
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
            if curr_depth < max_depth and non_article_children:
                structure["children"] = [
                    _build_element_structure(child, max_depth, curr_depth + 1) for child in non_article_children
                ]

            return structure

        element = self.elements.get(element_id, None)
        if element is None:
            logger.info(f"No element found with id {element_id}. Elements: {len(list(self.elements.values()))}")
            return element
        
        return _build_element_structure(element, max_depth, 0)

    def _get_amendments_for_art_children(
        self, element: DocumentElement
    ) -> List[Amendment]:
        if element.type_name == DocumentElementType.ARTICLE:
            return self._get_amendments_for_article(element.number)

        children = element.children.copy()
        amendments = []
        for child in children:
            if child.type_name == DocumentElementType.ARTICLE:
                amendments.extend(self._get_amendments_for_article(child))
            else:
                amendments.extend(self._get_amendments_for_art_children(child))

        amendments = [amendment for amendment in amendments if amendment is not None]
        return amendments

    def _get_amendments_for_article(self, article: DocumentElement) -> List[Amendment]:
        if self.art_amendment_map.get(article.number, None) is not None:
            return self.art_amendment_map[article.number]

        if self.amendment_data is None:
            return []

        if not self.amendment_data.has_amendments():
            return []

        for amendment in self.amendment_data.amendments:
            if amendment.target_element_type != DocumentElementType.ARTICLE.to_string():
                continue

            if amendment.target_element_no != article.number:
                continue

            map = self.art_amendment_map.get(article.number, None)
            if map is None:
                map = []
                self.art_amendment_map[article.number] = map

            map.append(amendment)

        amendments = self.art_amendment_map.get(article.number, [])
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
