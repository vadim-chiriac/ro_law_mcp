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
    valid_element_draft = None

    single_art = _try_find_single_article(text, offset)
    if single_art:
        return single_art
    
    while len(valid_types) > 0:
        curr_type = valid_types.pop(0)
        element_data = _find_element(text, curr_type, offset, preceding_text)
        if element_data is None:
            continue
        
        element_draft = element_data["element"]
        if (
            valid_element_draft is None
            or element_draft["start"] + offset < valid_element_draft["start"]
        ):
            valid_element_draft = element_draft
            
    if valid_element_draft is not None:
        if valid_element_draft["type"] == DocumentElementType.ARTICLE:
            extractor.last_valid_art_no = valid_element_draft["number"]
            
        return DocumentElement(
            type_name=valid_element_draft["type"],
            number=valid_element_draft["number"],
            title=valid_element_draft["title"],
            start_pos=valid_element_draft["start"],
            end_pos=valid_element_draft["end"],
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


def _find_element(text: str, e_type: DocumentElementType, offset: int, preceding_text: dict) -> dict:
    # if existing_header is None:
    #     e_header = _find_next_valid_header(text, e_type)
    # else:
    #     e_header = existing_header
    e_header = _find_next_valid_header(text, e_type, preceding_text)
    if not e_header:
        return None
    
    next_search_start = e_header["end"]
    next_header = _find_next_element_header(text[next_search_start:], e_type, None)
    
    end = len(text) - next_search_start if next_header is None else next_header["start"]
    element_draft = {
        "type": e_type,
        "start": e_header["start"] + offset,
        "end": end + offset + next_search_start - 1,
        "number": e_header["number"],
        "title": e_header["title"],
    }

    return {"element": element_draft, "next": next_header}


def _find_next_element_header(text: str, element_type: DocumentElementType, preceding_text: Optional[dict]) -> dict:
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

    header_data = extractor.validate_and_extract_header(header, element_type, preceding_text)

    if header_data is None:
        skip_pos = header["start"] + len(keyword)
        header_data = _find_next_valid_header(text[skip_pos:], element_type, preceding_text)
        if header_data is not None:
            header_data["start"] += skip_pos
            header_data["end"] += skip_pos

    return header_data


def _find_element_header(
    text: str, element_type: DocumentElementType
) -> Optional[dict]:
    keyword = element_type.to_keyword()
    element = _find_element_header_by_keyword(text, keyword)

    return element


def _find_element_header_by_keyword(text: str, keyword: str):
    if keyword is None:
        return None
    element_start = text.find(keyword)
    if element_start == -1:
        return None

    title_start = element_start + len(keyword)
    # if keyword == "Titlul":
    #     logger.info(f"Found title: {text[title_start:][:20]}")
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
