from romanian_legislation_mcp.document_model.model import DocumentPartType
from romanian_legislation_mcp.document_model.mappings import ROMAN_NUMERALS


def validate_header(header: str, element_type: DocumentPartType) -> bool:
    if element_type == DocumentPartType.BOOK:
        return _validate_book_header(header["header"])
    if element_type == DocumentPartType.TITLE:
        return _validate_title_header(header["header"])
    if element_type == DocumentPartType.CHAPTER:
        return _validate_chapter_header(header["header"])

    return False

def _validate_book_header(header: str) -> bool:
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

def _validate_title_header(header: str) -> bool:
    header = header.strip()

    words = header.split()
    if len(words) == 0:
        return False

    first_word = words[0]
    if first_word != "PRELIMINAR" and first_word not in ROMAN_NUMERALS:
        return False

    return True

def _validate_chapter_header(header: str) -> bool:
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

def _validate_article(article_name_row: str) -> bool:
    article_name_row = article_name_row.strip()

    parts = article_name_row.split()
    if len(parts) < 1:
        return False

    try:
        int(parts[0])
    except ValueError:
        return False

    return True
