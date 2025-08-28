from typing import Optional
from romanian_legislation_mcp.api_client.legislation_document import LegislationDocument
from romanian_legislation_mcp.structured_document.structured_document import (
    StructuredDocument,
)
from romanian_legislation_mcp.structured_document.element import (
    DocumentElement,
    DocumentElementType,
)
import logging

from romanian_legislation_mcp.document_amendments.amendment_parser import (
    AmendmentParser,
)
from romanian_legislation_mcp.structured_document.utils.text_parse import TextParser

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
        self.structured_document.add_element(self.top)
        self.text_parser = TextParser()

    def create_structured_document(self) -> StructuredDocument:
        """Parses the `LegislationDocument` instance to create structured `DocumentPart` instances"""

        self._find_elements(self.top)

        amendment_data = None
        if self.base_document.url:
            amendment_parser = AmendmentParser(self.base_document.url)
            amendment_data = amendment_parser.get_amendment_data()
            self.structured_document.amendment_data = amendment_data

        return self.structured_document
    
    def _find_elements(self, element: DocumentElement):
        # self._build_element_structure(element)
        # # if len(element.children) > 0:
        # #     element.max_depth +=1
        # for child in element.children:
        #     if child.type_name != DocumentElementType.ARTICLE:
        #         self._find_elements_recursive(child)
        self._find_elements_recursive(element)
        

    def _find_elements_recursive(self, element: DocumentElement):
        self._build_element_structure(element)
        if len(element.children) == 0:
            return 0
        
        new_max = 1
        for child in element.children:
            if child.type_name != DocumentElementType.ARTICLE:
                depth = self._find_elements_recursive(child)
                if depth > new_max:
                    new_max = depth
                elif depth == new_max:
                    new_max += 1
        
        element.max_depth = new_max
        return new_max

    def _build_element_structure(self, parent: DocumentElement) -> list[DocumentElement]:
        search_start = 0
        text = self.base_document.text[parent.start_pos : parent.end_pos]
        valid_types = parent.type_name.get_possible_child_types()
        prev = None
        preceding_text = None
        while search_start < len(text):

            element = self.text_parser.find_next_element(
                text[search_start:],
                valid_types,
                parent.start_pos + search_start,
                preceding_text,
            )
            if element is None:
                break

            parent.add_child(element)
            if element.type_name == DocumentElementType.ARTICLE:
                self.structured_document.add_article(element)
            elif element.type_name != DocumentElementType.TOP:
                self.structured_document.add_element(element)

            if prev is None or element.type_name != prev.type_name:
                valid_types = element.type_name.get_possible_equal_or_greater_types()
                try:
                    parent_index = valid_types.index(parent.type_name)
                    if parent_index != -1:
                        valid_types = valid_types[(parent_index + 1) :]
                except ValueError:
                    pass
            elif prev.type_name == element.type_name:
                prev = element
            else:
                excerpt_start = prev.end_pos - min(prev.start_pos - prev.end_pos, 200)
                prev_excerpt = text[excerpt_start : prev.end_pos]
                preceding_text = {
                    "excerpt": prev_excerpt,
                    "end_pos_in_doc": element.end_pos,
                }

            search_start = element.end_pos - parent.start_pos
