import copy
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
        self._find_first_part()

    def _find_first_part(self):
        book_list = self._find_books(self.document.text)

    def _find_books(self, text: str):
        book_list = self._find_element_list(text, DocumentElementName.BOOK)
        for book in book_list:
            logger.info(book["header"])

    def _find_element_list(self, text: str, element_type: DocumentElementName):
        element_list = []
        search_start = 0
        next_element_header = None
        while search_start < len(text):
            curr_element_header = self._find_next_valid_header(text[search_start:], element_type, search_start)            
            if not curr_element_header:
                break
            next_search_start = curr_element_header["header_end"]
            next_element_header = self._find_next_valid_header(text[next_search_start:], element_type, next_search_start)
            if not next_element_header:
                break
            
            element = curr_element_header.copy()
            element["content"] = text[curr_element_header["header_end"]:next_element_header["element_start"]]
            element["element_end"] = next_element_header["element_start"]
            element_list.append(element)
            
            search_start = element["element_end"]

        return element_list

    def _find_next_valid_header(
        self, text: str, element_type: DocumentElementName, pos_in_doc: int
    ) -> Optional[dict]:
        keyword = self._elem_type_to_keyword(element_type)
        header = self._find_element_header(text, keyword, pos_in_doc)
        if header is None:
            return None
        
        if not self._validate_header(header, element_type):
            logger.info(f"Invalid header found and skipped: '{header['header']}'")
            skip_pos = header["element_start"] + len(keyword)
            return self._find_next_valid_header(
                text[skip_pos - pos_in_doc:], element_type, skip_pos
            )

        return header

    # def _find_element_header(self, text: str, element_type: DocumentElementName) -> Optional[list[dict]]:
    #     first_header = self._find_element_header(text, self._elem_type_to_keyword(element_type))
    #     if first_header is None:
    #         return None

    #     next_header = self._find_element_header(
    #         text[first_header["header_end"] :], self._elem_type_to_keyword(element_type)
    #     )

    #     if next_header is None:
    #         return None

    #     first_content = text[first_header["header_end"] : next_header["element_start"]]
    #     first_element = copy(first_header)
    #     first_element["content"] = first_content

    def _find_element_header(self, text: str, keyword: str, pos_in_doc: int) -> Optional[dict]:
        element_start = text.find(keyword)
        if element_start == -1:
            return

        header_start = element_start + len(keyword)
        part_header_end = text[header_start:].find("\n")
        if part_header_end == -1:
            full_header_end = len(text)
        else:
            full_header_end = header_start + part_header_end
            
        # Not super consistent, for book/title/chapter, element_name_row is just the name,
        # for article it also includes (or only) content
        header = text[header_start:full_header_end]
        # element_pos_in_doc = pos_in_doc + header_start  # Position in full doc
        return {
            "header": header,
            "element_start": pos_in_doc + element_start,
            "header_start": pos_in_doc + header_start,
            "header_end": pos_in_doc + full_header_end
        }
        

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
        if first_word not in ROMAN_NUMERALS:
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
