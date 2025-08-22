from dataclasses import dataclass
from typing import Optional
from romanian_legislation_mcp.api_client.legislation_document import LegislationDocument
from romanian_legislation_mcp.document_model.part import DocumentPart, DocumentPartType
import logging
import uuid

from romanian_legislation_mcp.document_amendments.amendment_parser import AmendmentData

logger = logging.getLogger(__name__)


@dataclass
class ResultElement:
    number: str
    content: str
    changes: Optional[list[dict]] = None


class ModelController:
    """Class responsible for retrieving element content from a `DocumentPart`"""

    def __init__(self, document: LegislationDocument, top_element: DocumentPart):
        """Creates a new document model.

        :param document: The underlying `LegislationDocument` instance.
        :param top_element: The
        """
        self.document = document
        self.top = top_element
        self.articles: dict[str, DocumentPart] = {}
        self.elements: dict[str, DocumentPart] = {}
        self.amendments: Optional[AmendmentData] = None
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
        if art_data is not None:
            content = self.document.text[art_data.start_pos : art_data.end_pos]
        # for change in self.document.changes["changes"]:
        #     logger.info(change["target"])
        article = ResultElement(art_data.number, content)
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
    
    def _build_document_structure(self) -> dict:
        """Builds the hierarchical document structure."""
        def _build_element_structure(element: DocumentPart) -> dict:
            structure = {
                "type": element.type_name.name.lower(),
                "number": element.number,
                "title": element.title,
                "id": str(element.id)
            }
            
            # Get direct article children
            article_children = [child for child in element.children if child.type_name == DocumentPartType.ARTICLE]
            
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
                    structure["article_range"] = self._format_numeric_range(numeric_articles)
                
                if other_articles:
                    structure["other_articles"] = other_articles
            
            # Recursively process non-article children
            non_article_children = [child for child in element.children if child.type_name != DocumentPartType.ARTICLE]
            if non_article_children:
                structure["children"] = [_build_element_structure(child) for child in non_article_children]
            
            return structure
        
        return _build_element_structure(self.top)
    
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
