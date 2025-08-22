from dataclasses import dataclass
from typing import Optional
from romanian_legislation_mcp.api_client.legislation_document import LegislationDocument
from romanian_legislation_mcp.document_model.part import DocumentPart, DocumentPartType
import logging
import uuid

logger = logging.getLogger(__name__)


@dataclass
class ResultElement:
    number: str
    content: str
    changes: Optional[list[dict]] = None


class DocumentController:
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
    
    def get_document_structure(self):
        pass
