from typing import Optional
from romanian_legislation_mcp.api_client.legislation_document import LegislationDocument
from romanian_legislation_mcp.document_model.document_model import (
    DocumentModel,
    DocumentPart,
    DocumentElementName,
)
from romanian_legislation_mcp.document_model.mappings import ROMAN_NUMERALS
import logging

logger = logging.getLogger(__name__)


class DocumentModelBuilder:
    def __init__(self, document: LegislationDocument):
        self.document = document
        self.model = DocumentModel()
        self.level = 0
        self.current_element = DocumentPart

    def parse_document(self):
        self._build_document_structure()

    def _build_document_structure(self):
        text = self.document.text
        element_list = self._find_element_structure(text, DocumentElementName.TOP, 0)
        i = 0
        for element in element_list:
            if i >= 2:
                break
            start = element["element_start"]
            end = element["element_end"]
            children = self._find_element_structure(text[start:end], element["element_type"], 0)
            for c in children:
                logger.info(f"Found child: {c["header"]}")
            i += 1

    def _find_element_structure(
        self, element_text: str, element_type: DocumentElementName, pos_in_doc: int
    ):
        element_list = []
        search_start = 0
        logger.info(f"Element type is {element_type}")
        opening_types = list(reversed(element_type.get_possible_child_types()))

        closing_types = element_type.get_possible_child_types()
        if element_type != DocumentElementName.TOP:
            logger.info(f"Searching from {pos_in_doc}")
            logger.info(f"Len of text is {len(element_text)}")
            logger.info(f"Text starts with {element_text[:50]}")
            closing_types.append(element_type)
        second_header = None
        i = 0
        while search_start < len(element_text):
            # if i > 2:
            #     break
            first_header = self._find_next_possible_headers(
                element_text[search_start:], search_start, opening_types
            )
            if element_type != DocumentElementName.TOP:
                logger.info(f"Found first header: {first_header}")
            if not first_header:
                break
            closing_types = DocumentElementName.get_possible_equal_or_greater_types(first_header["element_type"])
            next_search_start = first_header["title_end"]
            second_header = self._find_next_possible_headers(
                element_text[next_search_start:], next_search_start, closing_types
            )
            if not second_header:
                break

            if element_type != DocumentElementName.TOP:
                logger.info(f"Found second header: {second_header}")
                
            element = first_header.copy()
            element["element_end"] = second_header["element_start"]
            e_type: DocumentElementName = element["element_type"]
            opening_types = e_type.get_possible_equal_or_greater_types()
            
            # logger.info(
            #     f"Found element: {element["element_type"]} - {element}"
            # )
            element["content"] = element_text[
                first_header["title_end"] : second_header["element_start"]
            ]
            element_list.append(element)
            search_start = element["element_end"]
            i += 1
            
        return element_list

    def _find_next_possible_headers(
        self,
        element_text: str,
        pos_in_doc: int,
        child_types: list[DocumentElementName],
    ):
        start_index = -1
        header = None
        c_type = None

        if child_types is None:
            return None

        for child_type in child_types:
            valid_header = self._find_next_valid_header(element_text, child_type, pos_in_doc)

            if valid_header is None:
                continue
            header_start_index = valid_header["element_start"]
            if start_index == -1 or header_start_index < start_index:
                start_index = header_start_index
                header = valid_header

        return header

    def _find_element_list(self, text: str, parent_type: DocumentElementName):
        element_list = []
        search_start = 0
        next_element_header = None
        while search_start < len(text):
            curr_element_header = self._find_next_valid_header(
                text[search_start:], element_type, search_start
            )
            if not curr_element_header:
                break
            next_search_start = curr_element_header["title_end"]
            next_element_header = self._find_next_valid_header(
                text[next_search_start:], element_type, next_search_start
            )
            if not next_element_header:
                break

            element = curr_element_header.copy()
            element["content"] = text[
                curr_element_header["title_end"] : next_element_header["element_start"]
            ]
            element["element_end"] = next_element_header["element_start"]
            element_list.append(element)
            logger.info(f"Found element: {element_type} - {element["header"]}")
            if element_type != DocumentElementName.CHAPTER:
                self._find_element_list(element["content"], DocumentElementName.TITLE)
            search_start = element["element_end"]

        return element_list

    def _find_next_valid_header(
        self, text: str, element_type: DocumentElementName, pos_in_doc: int
    ) -> Optional[dict]:
        keyword = self._elem_type_to_keyword(element_type)
        header = self._find_element_header(text, element_type, pos_in_doc)
        if header is None:
            return None

        if not self._validate_header(header, element_type):
            logger.info(f"Invalid header found and skipped: '{header['header'][:50]}'")
            skip_pos = header["element_start"] + len(keyword)
            return self._find_next_valid_header(
                text[skip_pos - pos_in_doc :], element_type, skip_pos
            )

        return header

    # def _find_element_header(self, text: str, element_type: DocumentElementName) -> Optional[list[dict]]:
    #     first_header = self._find_element_header(text, self._elem_type_to_keyword(element_type))
    #     if first_header is None:
    #         return None

    #     next_header = self._find_element_header(
    #         text[first_header["title_end"] :], self._elem_type_to_keyword(element_type)
    #     )

    #     if next_header is None:
    #         return None

    #     first_content = text[first_header["title_end"] : next_header["element_start"]]
    #     first_element = copy(first_header)
    #     first_element["content"] = first_content

    def _find_element_header(
        self, text: str, element_type: DocumentElementName, pos_in_doc: int
    ) -> Optional[dict]:
        keyword = self._elem_type_to_keyword(element_type)
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
            "element_start": pos_in_doc + element_start,
            "title_start": pos_in_doc + title_start,
            "title_end": pos_in_doc + full_title_end,
            "element_type": element_type,
        }

    # def get_child_part(element_type: DocumentElementName):
    #     types = [DocumentElementName.BOOK, DocumentElementName.]

    def _validate_header(self, header: str, element_type: DocumentElementName) -> bool:
        if element_type == DocumentElementName.BOOK:
            return self._validate_book_header(header["header"])
        if element_type == DocumentElementName.TITLE:
            return self._validate_title_header(header["header"])
        if element_type == DocumentElementName.CHAPTER:
            return self._validate_chapter_header(header["header"])

        return False

    def _validate_book_header(self, header: str) -> bool:
        header = header.strip()

        if len(header) == 0:
            return False

        words = header.split()
        if len(words) == 0:
            return False

        first_word = words[0]
        if first_word not in ROMAN_NUMERALS and not (
            len(first_word) == 1 and first_word.isalpha()
        ):
            return False

        if len(header) > 500:
            return False

        return True

    def _validate_title_header(self, header: str) -> bool:
        header = header.strip()

        words = header.split()
        if len(words) == 0:
            return False

        first_word = words[0]
        if first_word != "PRELIMINAR" and first_word not in ROMAN_NUMERALS:
            return False

        return True

    def _validate_chapter_header(self, header: str) -> bool:
        header = header.strip()

        words = header.split()
        if len(words) == 0:
            return False

        first_word = words[0]
        if first_word not in ROMAN_NUMERALS:
            return False

        if len(header) > 200:
            return False

        return True

    def _validate_article(self, article_name_row: str) -> bool:
        article_name_row = article_name_row.strip()

        parts = article_name_row.split()
        if len(parts) < 1:
            return False

        try:
            int(parts[0])
        except ValueError:
            return False

        return True

    def _extract_article_content(
        self, doc_text: str, article_start: int, article_header: str
    ) -> str:
        """Extract the full content of an article including its text body."""
        article_start_in_text = article_start + len("Articolul")

        article_end = len(doc_text)
        search_patterns = ["Articolul", "Capitolul", "Titlul", "Cartea", "Anexa"]

        for pattern in search_patterns:
            pos = doc_text.find(pattern, article_start_in_text)
            if pos != -1 and pos < article_end:
                article_end = pos

        article_content = doc_text[article_start:article_end].strip()

        lines = article_content.split("\n", 1)
        if len(lines) > 1:
            header_after_keyword = lines[0][len("Articolul") :].strip()
            article_body = lines[1].strip()
            return (
                f"{header_after_keyword}\n{article_body}"
                if article_body
                else header_after_keyword
            )
        else:
            return lines[0][len("Articolul") :].strip()

    def _elem_type_to_keyword(self, t: DocumentElementName) -> str:
        if t == DocumentElementName.BOOK:
            return "Cartea"
        elif t == DocumentElementName.TITLE:
            return "Titlul"
        elif t == DocumentElementName.CHAPTER:
            return "Capitolul"

    def get_element_type_from_header(
        self, header: str
    ) -> Optional[DocumentElementName]:
        """Extract DocumentElementName from a string header.

        Args:
            header: String header that may contain Romanian legal document keywords

        Returns:
            DocumentElementName if found, None otherwise
        """
        header = header.strip()

        if header.startswith("Cartea"):
            return DocumentElementName.BOOK
        elif header.startswith("Titlul"):
            return DocumentElementName.TITLE
        elif header.startswith("Capitolul"):
            return DocumentElementName.CHAPTER

        return None
