from typing import Optional
from romanian_legislation_mcp.api_client.legislation_document import LegislationDocument
from romanian_legislation_mcp.document_amendments.amendment import Amendment
from romanian_legislation_mcp.document_model.model_controller import ModelController
from romanian_legislation_mcp.document_model.model import (
    DocumentPart,
    DocumentPartType,
)
from romanian_legislation_mcp.document_model.utils.text_parse import find_element
import logging

from romanian_legislation_mcp.document_amendments.amendment_parser import (
    AmendmentData,
    AmendmentParser,
)

logger = logging.getLogger(__name__)


class ModelBuilder:
    """Class responsible for creating structured data from `LegislationDocument` objects"""

    def __init__(self, document: LegislationDocument):
        self.document = document
        self.top = DocumentPart(
            type_name=DocumentPartType.TOP,
            title=self.document.title,
            start_pos=0,
            end_pos=len(self.document.text),
        )
        self.controller = ModelController(self.document, self.top)

    def create_controller(self) -> ModelController:
        """Parses the `LegislationDocument` instance to create structured `DocumentPart` instances"""

        self._build_document_structure()
        amendment_data = None
        if self.document.url:
            amendment_parser = AmendmentParser(self.document.url)
            amendment_data = amendment_parser.get_amendment_data()
            self.controller.amendment_data = amendment_data

        return self.controller

    def _build_document_structure(self):
        self._build_hierarchy(self.top)
        logger.info(f"Document parsing complete for {self.document.title}.")

    def _build_hierarchy(self, element: DocumentPart):
        self._find_element_structure(element)
        for child in element.children:
            if child.type_name != DocumentPartType.ARTICLE:
                self._build_hierarchy(child)

    def _find_element_structure(self, parent: DocumentPart) -> list[DocumentPart]:
        search_start = 0
        text = self.document.text[parent.start_pos : parent.end_pos]

        valid_types = parent.type_name.get_possible_child_types()

        while search_start < len(text):
            element = find_element(
                text[search_start:],
                valid_types,
                parent.start_pos + search_start,
            )

            if element is None:
                break

            parent.add_child(element)
            if element.type_name == DocumentPartType.ARTICLE:
                self.controller.add_article(element)
            elif element.type_name != DocumentPartType.TOP:
                self.controller.add_element(element)

            valid_types = element.type_name.get_possible_equal_or_greater_types()
            search_start = element.end_pos - parent.start_pos
