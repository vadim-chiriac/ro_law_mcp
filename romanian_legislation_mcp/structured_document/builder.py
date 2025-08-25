from romanian_legislation_mcp.api_client.legislation_document import LegislationDocument
from romanian_legislation_mcp.structured_document.structured_document import (
    StructuredDocument,
)
from romanian_legislation_mcp.structured_document.element import (
    DocumentElement,
    DocumentElementType,
)
from romanian_legislation_mcp.structured_document.utils.text_parse import find_element
import logging

from romanian_legislation_mcp.document_amendments.amendment_parser import (
    AmendmentParser,
)
from romanian_legislation_mcp.structured_document.utils.validator import Validator

logger = logging.getLogger(__name__)


class StructuredDocumentBuilder:
    """Class responsible for creating structured data from `LegislationDocument` objects"""

    def __init__(self, base_document: LegislationDocument):
        self.base_document = base_document
        self.top = DocumentElement(
            type_name=DocumentElementType.TOP,
            number="0",
            title=self.base_document.title,
            start_pos=0,
            end_pos=len(self.base_document.text),
        )
        self.structured_document = StructuredDocument(self.base_document, self.top)
        self.validator = Validator()

    def create_structured_document(self) -> StructuredDocument:
        """Parses the `LegislationDocument` instance to create structured `DocumentPart` instances"""

        self._find_elements(self.top)
        # logger.info(
        #     f"""Found {len(self.structured_document.elements)} elements
        #             and {len(self.structured_document.articles)} articles 
        #             for {self.base_document.title}."""
        # )
        amendment_data = None
        if self.base_document.url:
            amendment_parser = AmendmentParser(self.base_document.url)
            amendment_data = amendment_parser.get_amendment_data()
            self.structured_document.amendment_data = amendment_data

        return self.structured_document

    def _find_elements(self, element: DocumentElement):
        self._find_element_structure(element)
        for child in element.children:
            if child.type_name != DocumentElementType.ARTICLE:
                self._find_elements(child)


    def _find_element_structure(self, parent: DocumentElement) -> list[DocumentElement]:
        search_start = 0
        text = self.base_document.text[parent.start_pos : parent.end_pos]

        valid_types = parent.type_name.get_possible_child_types()

        while search_start < len(text):
            element = find_element(
                text[search_start:],
                valid_types,
                parent.start_pos + search_start,
                self.validator
            )

            if element is None:
                break

            parent.add_child(element)
            if element.type_name == DocumentElementType.ARTICLE:
                
                self.structured_document.add_article(element)
            elif element.type_name != DocumentElementType.TOP:
                self.structured_document.add_element(element)

            valid_types = element.type_name.get_possible_equal_or_greater_types()
            search_start = element.end_pos - parent.start_pos
