from typing import Optional
from romanian_legislation_mcp.api_client.legislation_document import LegislationDocument
from romanian_legislation_mcp.document_model.model import (
    DocumentModel,
    DocumentPart,
    DocumentPartType,
)
from romanian_legislation_mcp.document_model.validator import validate_header
import logging

logger = logging.getLogger(__name__)


class ModelBuilder:
    def __init__(self, document: LegislationDocument):
        self.document = document
        self.model = DocumentModel()
        self.level = 0
        self.current_element = DocumentPart

    def parse_document(self):
        self._build_document_structure()

    def _build_document_structure(self):
        top = DocumentPart(
            DocumentPartType.TOP, self.document.title, None, 0, len(self.document.text)
        )
        self._find_element_structure(top)

    def _find_element_structure(self, parent: DocumentPart) -> list[DocumentPart]:
        element_list: list[DocumentPart] = []
        search_start = 0
        text = self.document.text[parent.start_pos : parent.end_pos]
        max_parent_type = parent.type_name
        
        while search_start < len(text):
            # logger.info(f"Searching from {search_start} (absolute: {parent.start_pos + search_start}).")
            # logger.info(f"Text starts with: {text[search_start:][:50]}")
            # logger.info(f"Parent range: {parent.start_pos}:{parent.end_pos}, remaining text length: {len(text) - search_start}")
            element = self._find_element(
                text[search_start:], max_parent_type, parent, parent.start_pos + search_start
            )
            
            if element is None:
                continue

            parent.add_child(element)
            logger.info(
                f"Found element: {element.type_name} - {element.title}. {element.start_pos}:{element.end_pos}"
            )

            max_parent_type = element.type_name.get_possible_equal_or_greater_types()[0]
            search_start = element.end_pos - parent.start_pos


    def _find_element(
        self, text: str, parent_type: DocumentPartType, parent: DocumentPart, offset: int
    ) -> Optional[DocumentPart]:
        opening_types = parent_type.get_possible_child_types()
        closing_types = []
        opening_index = -1
        i = 0
        element = None
        while len(opening_types) > 0:
            o_type = opening_types.pop()
            o_header = self._find_next_valid_header(text, o_type)
            if not o_header:
                continue
            if opening_index != -1 and o_header["element_start"] > opening_index:
                continue
            # if (o_type == DocumentPartType.BOOK):
            #     logger.info(f"Found opening: {o_header}")
            closing_types = o_header[
                "element_type"
            ].get_possible_equal_or_greater_types()
            i = o_header["title_end"]
            c_header = None
            while len(closing_types) > 0:
                c_type = closing_types.pop(0)
                c_header = self._find_next_valid_header(text[i:], c_type)
                if c_header:
                    break

            element_end = 0
            if c_header is None:
                # if (o_type == DocumentPartType.BOOK):
                #     logger.info(f"Found none closing for type {o_type} with parent type {parent.type_name} and parent: {parent.children}")
                if len(parent.get_children_of_type(o_type)) == 0:
                    continue
                else:
                    logger.info(f"Possible last element {o_type}")
                    element_end = len(self.document.text)
            else:
                element_end = c_header["element_start"] + i + offset
            
            element = DocumentPart(
                o_type,
                o_header["header"],
                None,
                o_header["element_start"] + offset,
                element_end
            )

            opening_index = element.start_pos

        return element

    def _find_next_valid_header(
        self, text: str, element_type: DocumentPartType
    ) -> Optional[dict]:
        keyword = element_type.to_keyword()
        header = self._find_element_header(text, element_type)
        if header is None:
            return None

        if not validate_header(header, element_type):
            # logger.info(f"Invalid header found and skipped: '{header['header'][:50]}'")
            skip_pos = header["element_start"] + len(keyword)
            h = self._find_next_valid_header(text[skip_pos:], element_type)
            if h is not None:
                start = h["element_start"] + skip_pos
                t_start = h["title_start"] + skip_pos
                t_end = h["title_end"] + skip_pos

                h["element_start"] = start
                h["title_start"] = t_start
                h["title_end"] = t_end
            return h

        return header

    def _find_element_header(
        self, text: str, element_type: DocumentPartType
    ) -> Optional[dict]:
        keyword = element_type.to_keyword()
        if keyword is None:
            return
        element_start = text.find(keyword)
        if element_start == -1:
            return

        title_start = element_start + len(keyword)
        part_title_end = text[title_start:].find("\n")
        if part_title_end == -1:
            full_title_end = len(text)
        else:
            full_title_end = title_start + part_title_end

        # Not super consistent, for book/title/chapter, element_name_row is just the name,
        # for article it also includes (or only) content
        header = text[title_start:full_title_end]
        # element_pos_in_doc = pos_in_doc + title_start  # Position in full doc
        return {
            "header": header,
            "element_start": element_start,
            "title_start": title_start,
            "title_end": full_title_end,
            "element_type": element_type,
        }
