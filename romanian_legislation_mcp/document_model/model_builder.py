from typing import Optional
from romanian_legislation_mcp.api_client.legislation_document import LegislationDocument
from romanian_legislation_mcp.document_model.model import ModelController
from romanian_legislation_mcp.document_model.part import (
    DocumentPart,
    DocumentPartType,
)
from romanian_legislation_mcp.document_model.validator import (
    validate_header,
    extract_number_from_header,
)
import logging

from romanian_legislation_mcp.document_amendments.amendment_parser import AmendmentParser

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
        self.model = ModelController(self.document, self.top)
        if self.document.url:
            self.amendment_parser = AmendmentParser(self.document.url)
        else:
            logger.warning(f"Document URL is None for {self.document.title}")
            self.amendment_parser = None

    def parse_document(self):
        """Parses the `LegislationDocument` instance to create structured `DocumentPart` instances"""

        self._build_document_structure()
        if self.amendment_parser is not None:
            amendment_data = self.amendment_parser.get_amendment_data()

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
            element = self._find_element(
                text[search_start:],
                valid_types,
                parent.start_pos + search_start,
            )

            if element is None:
                break
            
            parent.add_child(element)
            if element.type_name == DocumentPartType.ARTICLE:
                self.model.add_article(element)
            elif element.type_name != DocumentPartType.TOP:
                self.model.add_element(element)
                
            valid_types = element.type_name.get_possible_equal_or_greater_types()
            search_start = element.end_pos - parent.start_pos

    def _find_element(
        self,
        text: str,
        valid_types: list[DocumentPart],
        offset: int,
    ) -> Optional[DocumentPart]:
        element = None
        while len(valid_types) > 0:
            e_type = valid_types.pop(0)
            e_header = self._find_next_valid_header(text, e_type)
            if not e_header:
                continue

            next_search_start = e_header["title_end"]
            e_end = self._find_element_end(text[next_search_start:], e_type)

            if (
                element is None
                or e_header["element_start"] + offset < element.start_pos
            ):
                if e_type == DocumentPartType.ARTICLE:
                    title = e_header["header"].split()[0]
                else:
                    title = e_header["header"]

                element = DocumentPart(
                    type_name=e_type,
                    title=title,
                    start_pos=e_header["element_start"] + offset,
                    end_pos=e_end + offset + next_search_start,
                )

        if element is not None:
            number = extract_number_from_header(e_header, e_type)
            element.set_number(number)

        return element

    def _find_element_end(self, text: str, element_type: DocumentPartType) -> int:
        valid_siblings = element_type.get_possible_equal_or_greater_types()
        while len(valid_siblings) > 0:
            next_e_type = valid_siblings.pop(0)
            next_e_header = self._find_next_valid_header(text, next_e_type)
            if next_e_header is not None:
                return next_e_header["element_start"]
            elif len(valid_siblings) == 0:
                return len(text)

    def _find_next_valid_header(
        self, text: str, element_type: DocumentPartType
    ) -> Optional[dict]:
        keyword = element_type.to_keyword()
        header = self._find_element_header(text, element_type)
        skip_pos = 0
        if header is None:
            return None

        if not validate_header(header, element_type):
            # logger.info(f"Invalid header found and skipped: '{header['header'][:50]}'")
            skip_pos = header["element_start"] + len(keyword)
            header = self._find_next_valid_header(text[skip_pos:], element_type)

            if header is not None:
                start = header["element_start"] + skip_pos
                t_start = header["title_start"] + skip_pos
                t_end = header["title_end"] + skip_pos

                header["element_start"] = start
                header["title_start"] = t_start
                header["title_end"] = t_end

        return header

    def _find_element_header(
        self, text: str, element_type: DocumentPartType
    ) -> Optional[dict]:
        keyword = element_type.to_keyword()
        if keyword is None:
            return None
        element_start = text.find(keyword)
        if element_start == -1:
            return None

        title_start = element_start + len(keyword)
        part_title_end = text[title_start:].find("\n")
        if part_title_end == -1:
            full_title_end = len(text)
        else:
            full_title_end = title_start + part_title_end

        header = text[title_start:full_title_end]

        return {
            "header": header,
            "element_start": element_start,
            "title_start": title_start,
            "title_end": full_title_end,
            "element_type": element_type,
        }
