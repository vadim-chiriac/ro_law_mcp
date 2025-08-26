from typing import Optional
from romanian_legislation_mcp.structured_document.element import (
    DocumentElement,
    DocumentElementType,
)
from romanian_legislation_mcp.structured_document.utils.extractor import Extractor
from romanian_legislation_mcp.structured_document.element import DocumentElementType

import logging

logger = logging.getLogger(__name__)
extractor = Extractor()


def find_next_element(
    text: str, valid_types: list[DocumentElement], offset: int, preceding_text: dict
) -> Optional[DocumentElement]:
    first_valid_header = None

    single_art = _try_find_single_article(text, offset)
    if single_art:
        return single_art

    while len(valid_types) > 0:
        curr_type = valid_types.pop(0)
        header = _find_next_valid_header(text, curr_type, None)
        if header is None:
            continue

        if first_valid_header is None or header["start"] < first_valid_header["start"]:
            first_valid_header = header

    if first_valid_header is not None:
        next_search_start = first_valid_header["end"]
        next_valid_header = _find_next_element_header(
            text[next_search_start:], first_valid_header["type"], None
        )
        if first_valid_header["type"] == DocumentElementType.ARTICLE:
            extractor.last_valid_art_no = first_valid_header["number"]

        end = (
            next_valid_header["start"] + next_search_start - 1
            if next_valid_header
            else len(text)
        )
        return DocumentElement(
            type_name=first_valid_header["type"],
            number=first_valid_header["number"],
            title=first_valid_header["title"],
            start_pos=first_valid_header["start"] + offset,
            end_pos=end + offset,
        )

    return None


def _try_find_single_article(text: str, offset: int):
    article = _find_element_header_by_keyword(text, "ARTICOL")
    if article:
        return DocumentElement(
            type_name=DocumentElementType.ARTICLE,
            number="UNIC",
            title="UNIC",
            start_pos=article["start"] + offset,
            end_pos=article["end"] + offset,
        )

    return None


def _find_next_element_header(
    text: str, element_type: DocumentElementType, preceding_text: Optional[dict]
) -> dict:
    valid_siblings = element_type.get_possible_equal_or_greater_types()
    while len(valid_siblings) > 0:
        next_e_type = valid_siblings.pop(0)
        next_e_header = _find_next_valid_header(text, next_e_type, preceding_text)

        if next_e_header is not None:
            return next_e_header
        elif len(valid_siblings) == 0:
            return None


def _find_next_valid_header(
    text: str, element_type: DocumentElementType, preceding_text: dict
) -> Optional[dict]:
    keyword = element_type.to_keyword()
    header = _find_element_header(text, element_type)
    if header is None:
        return None

    preceding_text = text[int(header["start"]) - 50 : int(header["start"])]
    header_data = extractor.validate_and_extract_header(
        header, element_type, preceding_text
    )

    if header_data is None:
        skip_pos = header["start"] + len(keyword)
        header_data = _find_next_valid_header(
            text[skip_pos:], element_type, preceding_text
        )
        if header_data is not None:
            header_data["start"] += skip_pos
            header_data["end"] += skip_pos

    return header_data


def _find_element_header(
    text: str, element_type: DocumentElementType
) -> Optional[dict]:
    keyword = element_type.to_keyword()
    element = _find_element_header_by_keyword(text, keyword)
    if element:
        element["type"] = element_type

    return element


def _find_element_header_by_keyword(text: str, keyword: str):
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

    header_text = text[title_start:full_title_end]

    return {
        "text": header_text,
        "start": element_start,
        "end": full_title_end,
    }
