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
class ResultArticle:
    """Class representing structured article data to be sent to clients."""

    number: str
    title: str
    content: str
    amendment_data: AmendmentData | None
    is_latest_version: bool


class StructuredDocument:
    """Class containing data and methods for structured operations on legal documents."""

    def __init__(
        self,
        base_document: LegislationDocument,
        top_element: DocumentElement,
        amendment_data: Optional[AmendmentData] = None,
    ):
        """Creates a new document model.

        :param document: The underlying `LegislationDocument` instance.
        :param top_element: A `DocumentElement` instance representing the root of the document
        :param amendment_data: Metadata representing amendments made to the document which are not reflected in the base text
        """

        self.base_document = base_document
        self.top_element = top_element
        self.articles: dict[str, DocumentElement] = {}
        self.elements: dict[str, DocumentElement] = {}
        self.amendment_data = amendment_data

    def get_one_or_more_articles(
        self, art_no_or_list: str | list[str]
    ) -> List[ResultArticle | dict]:
        """Retrieves one or more articles in structured format.

        :param art_no_or_list: Article number(s) to retrieve.
        """
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

    def search_document(
        self,
        query: str,
        start_pos: int = 0,
        end_pos: int = -1,
        max_excerpts: int = 5,
        excerpt_context_chars: int = 250,
    ) -> Dict[str, Any]:
        """Searches the text contents of a legal document or a part of it."""
        
        search_text = self.get_text(start_pos, end_pos)
        excerpts = text_search(search_text, query, max_excerpts, excerpt_context_chars)

        for excerpt in excerpts.get("excerpts", []):
            excerpt["match_start_in_document"] = (
                excerpt["match_start_in_text"] + start_pos
            )

        return excerpts

    def get_text(self, start_pos=0, end_pos=-1) -> Optional[str]:
        """Retrieves the text contents of a legal document or a part of it.
        :param start_pos: The start index to retrieve text from 
        :param end_pos: The end index to retrieve text from
        """
        
        try:
            return self.base_document.text[start_pos:end_pos]
        except Exception as e:
            logger.warning(f"Error getting text for {self.base_document.title}: ")
            return None

    def get_structural_amendment_data(self) -> AmendmentData:
        amendments = [
            a
            for a in self.amendment_data.amendments
            if a.target_element_type != DocumentElementType.ARTICLE.to_string()
        ]

        data = AmendmentData(amendments, self.amendment_data.is_document_repealed)
        return data

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

    def _get_article(self, art_no: str) -> Optional[ResultArticle]:
        article = self.articles.get(art_no, None)
        if article is None:
            return None

        content = self.base_document.text[article.start_pos : article.end_pos]
        amendments = self._get_amendments_for_article(article)
        result = ResultArticle(
            number=article.number,
            title=article.title,
            content=content,
            amendment_data=amendments,
            is_latest_version=len(amendments) == 0,
        )

        return result

    def _get_amendments_for_article(self, article: DocumentElement) -> List[Amendment]:
        if self.amendment_data is None:
            return []

        results = []
        for amendment in self.amendment_data.amendments:
            if amendment.target_element_type != DocumentElementType.ARTICLE.to_string():
                continue

            if amendment.target_element_no != article.number:
                continue

            results.append(amendment)

        return results
