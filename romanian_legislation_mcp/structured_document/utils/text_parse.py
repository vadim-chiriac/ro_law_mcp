from typing import Optional
from romanian_legislation_mcp.structured_document.element import (
    DocumentElement,
    DocumentElementType,
)
from romanian_legislation_mcp.structured_document.utils.validator import Validator

from romanian_legislation_mcp.structured_document.element import DocumentElementType
from romanian_legislation_mcp.structured_document.mappings.mappings import (
    ROMAN_NUMERALS,
)

import logging

logger = logging.getLogger(__name__)

_validator = None

def find_element(
    text: str,
    valid_types: list[DocumentElement],
    offset: int,
    validator: Validator
) -> Optional[DocumentElement]:
    global _validator
    _validator = validator
    element_draft = None
    while len(valid_types) > 0:
        e_type = valid_types.pop(0)
        e_header = _find_next_valid_header(text, e_type)
        if not e_header:
            continue

        next_search_start = e_header["title_end"]
        e_end = _find_element_end(text[next_search_start:], e_type)

        if (
            element_draft is None
            or e_header["element_start"] + offset < element_draft["start"]
        ):
            element_draft = {
                "type": e_type,
                "header": e_header["header"],
                "start": e_header["element_start"] + offset,
                "end": e_end + offset + next_search_start,
            }

    if element_draft is not None:
        number = _extract_number_from_header(
            element_draft["header"], element_draft["type"]
        )
        if element_draft["type"] == DocumentElementType.ARTICLE:
            title = _try_extract_article_title(element_draft["header"])
            if title is None:
                title = "N/A"
        else:
            title = element_draft["header"]
        
        if element_draft["type"] == DocumentElementType.ARTICLE:
            validator.last_valid_article_no = number

        return DocumentElement(
            type_name=element_draft["type"],
            number=number,
            title=title,
            start_pos=element_draft["start"],
            end_pos=element_draft["end"],
        )

    return None


def _find_element_end(text: str, element_type: DocumentElementType) -> int:
    valid_siblings = element_type.get_possible_equal_or_greater_types()
    while len(valid_siblings) > 0:
        next_e_type = valid_siblings.pop(0)
        next_e_header = _find_next_valid_header(text, next_e_type)
        if next_e_header is not None:
            return next_e_header["element_start"]
        elif len(valid_siblings) == 0:
            return len(text)


def _find_next_valid_header(
    text: str, element_type: DocumentElementType
) -> Optional[dict]:
    keyword = element_type.to_keyword()
    header = _find_element_header(text, element_type)
    skip_pos = 0
    if header is None:
        return None

    if not _validator.validate_header(header, element_type):
        # logger.info(f"Invalid header found and skipped: '{header['header'][:50]}'")
        skip_pos = header["element_start"] + len(keyword)
        header = _find_next_valid_header(text[skip_pos:], element_type)

        if header is not None:
            start = header["element_start"] + skip_pos
            t_start = header["title_start"] + skip_pos
            t_end = header["title_end"] + skip_pos

            header["element_start"] = start
            header["title_start"] = t_start
            header["title_end"] = t_end

    return header


def _find_element_header(
    text: str, element_type: DocumentElementType
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


def _extract_number_from_header(header: str, element_type: DocumentElementType) -> str:
    """
    Extract numeric/identifier from header based on element type.

    Args:
        header: The header string or dict containing 'header' key
        element_type: The type of document element

    Returns:
        String representation of the extracted number/identifier
    """
    if isinstance(header, dict):
        header_str = header.get("header", "")
    else:
        header_str = header

    if element_type == DocumentElementType.BOOK:
        return _extract_book_number(header_str)
    elif element_type == DocumentElementType.TITLE:
        return _extract_title_number(header_str)
    elif element_type == DocumentElementType.CHAPTER:
        return _extract_chapter_number(header_str)
    elif element_type == DocumentElementType.SECTION:
        return _extract_section_number(header_str)
    elif element_type == DocumentElementType.ARTICLE:
        return _extract_article_number(header_str)
    else:
        return "0"


def _extract_book_number(header: str) -> str:
    """Extract number from book header (Roman numerals or single letters)."""
    header = header.strip()
    if not header:
        return "0"

    words = header.split()
    if not words:
        return "0"

    first_word = words[0]

    if first_word in ROMAN_NUMERALS:
        return str(ROMAN_NUMERALS.index(first_word) + 1)

    if len(first_word) == 1 and first_word.isalpha():
        return str(ord(first_word.upper()) - ord("A") + 1)

    return "0"


def _extract_title_number(header: str) -> str:
    """Extract number from title header (Roman numerals or 'PRELIMINAR')."""
    header = header.strip()
    if not header:
        return "0"

    words = header.split()
    if not words:
        return "0"

    first_word = words[0]

    return first_word


def _extract_chapter_number(header: str) -> str:
    """Extract number from chapter header (Roman numerals)."""
    header = header.strip()
    if not header:
        return "0"

    words = header.split()
    if not words:
        return "0"

    first_word = words[0]

    if first_word in ROMAN_NUMERALS:
        return str(ROMAN_NUMERALS.index(first_word) + 1)

    return "0"


def _extract_section_number(header: str) -> str:
    """Extract number from section header (numbers with optional '-a' suffix)."""
    header = header.strip()
    if not header:
        return "0"

    words = header.split()
    if not words:
        return "0"

    first_word = words[0]

    if first_word == "a" and len(words) > 1:
        second_word = words[1]
        if second_word.endswith("-a"):
            number_part = second_word[:-2]
        else:
            return "0"
    else:
        number_part = first_word

    try:
        num = int(number_part)
        if num > 0:
            return str(num)
    except ValueError:
        pass

    return "0"


def _extract_article_number(header: str) -> str:
    """Extract number from article header (integer numbers)."""
    header = header.strip()
    if not header:
        return "0"

    #logger.info(f"Found header: {header}")
    words = header.split()
    if not words:
        return "0"

    first_word = words[0]
    #logger.info(f"Found {first_word}")
    if first_word in ROMAN_NUMERALS:
        return first_word
    try:
        num = int(first_word)
        if num > 0:
            return str(num)
    except ValueError:
        pass

    return "0"


def _try_extract_article_title(raw_text: str) -> Optional[str]:
    raw_text = raw_text.strip()
    if not raw_text:
        return None

    rows = raw_text.split("     ")
    # art_no = rows[0]

    try:
        if len(rows) < 2:
            return None

        possible_title = rows[1]
        if len(rows) == 2:
            alt_rows = rows[1].split("  ")
            possible_title = alt_rows[0]

        if possible_title.strip().startswith("("):
            return None

        if len(rows) > 2:
            if not rows[2].strip().startswith("("):
                return None

        return possible_title
    except Exception as e:
        return None
