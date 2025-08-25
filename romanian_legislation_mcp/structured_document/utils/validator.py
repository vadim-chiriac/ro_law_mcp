from typing import Optional
from romanian_legislation_mcp.structured_document.element import DocumentElementType
from romanian_legislation_mcp.structured_document.mappings.mappings import (
    ROMAN_NUMERALS,
)
import logging

logger = logging.getLogger(__name__)


class Validator:
    def __init__(self):
        self.last_valid_article_no: Optional[str] = None

    def validate_header(self, header: str, element_type: DocumentElementType) -> bool:
        header_str = header["header"]
        if element_type == DocumentElementType.BOOK:
            return self._validate_book_header(header_str)
        if element_type == DocumentElementType.TITLE:
            return self._validate_title_header(header_str)
        if element_type == DocumentElementType.CHAPTER:
            return self._validate_chapter_header(header_str)
        if element_type == DocumentElementType.SECTION:
            return self._validate_section_header(header_str)
        if element_type == DocumentElementType.ARTICLE:
            return self._validate_article(header_str)

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

        title_no = words[0]
        if title_no != "PRELIMINAR" and title_no not in ROMAN_NUMERALS:
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


    def _validate_section_header(self, header: str) -> bool:
        header = header.strip()

        words = header.split()
        if len(words) == 0:
            return False

        if words[0] != "a" and words[0] != "1":
            return False

        if words[0] != "1":
            second_word = words[1]
            if not second_word.endswith("-a"):
                return False
            number_part = second_word[:-2]
        else:
            number_part = words[0]

        try:
            num = int(number_part)
            if num <= 0:
                return False
        except ValueError:
            return False

        if len(header) > 300:
            return False

        return True


    def _validate_article(self, article_name_row: str) -> bool:
        clean_article_name_row = article_name_row.strip()

        parts = clean_article_name_row.split("      ")
        if len(parts) < 1:
            return False
        
        art_no = parts[0]
        # if art_no in ROMAN_NUMERALS:
        #     logger.info(f"Found art_no {art_no}")
        #     logger.info(f"Content: {clean_article_name_row[:20]}")
        
        return self._is_valid_article_no(self.last_valid_article_no, art_no)
    
    def _is_valid_number(self, number: str):
        try:
            return number in ROMAN_NUMERALS or int(number) >= 0
        except:
            return False
        
    def _is_valid_article_no(self, prev: str, curr: str) -> bool:
        if prev == None:
            return True
        
        if prev in ROMAN_NUMERALS:
            if curr in ROMAN_NUMERALS:
                return self._compare_roman_numerals(prev, curr)
            else:
                return False
        elif curr in ROMAN_NUMERALS:
                return False
        else:
            try:
                return int(curr) > int(prev)
            except:
                return True    
            
    def _compare_roman_numerals(self, first: str, second: str) -> bool:
        """
        Compare two Roman numerals and return True if second > first.
        Uses the index position in ROMAN_NUMERALS list for comparison.
        """
        try:
            first_index = ROMAN_NUMERALS.index(first)
            second_index = ROMAN_NUMERALS.index(second)
            return second_index > first_index
        except ValueError:
            return False


