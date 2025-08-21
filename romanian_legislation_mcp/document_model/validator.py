from romanian_legislation_mcp.document_model.model import DocumentPartType
from romanian_legislation_mcp.document_model.mappings import ROMAN_NUMERALS


def validate_header(header: str, element_type: DocumentPartType) -> bool:
    header_str = header["header"]
    if element_type == DocumentPartType.BOOK:
        return _validate_book_header(header_str)
    if element_type == DocumentPartType.TITLE:
        return _validate_title_header(header_str)
    if element_type == DocumentPartType.CHAPTER:
        return _validate_chapter_header(header_str)
    if element_type == DocumentPartType.SECTION:
        return _validate_section_header(header_str)

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

def _validate_section_header(header: str) -> bool:
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
