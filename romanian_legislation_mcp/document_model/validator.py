from romanian_legislation_mcp.document_model.part import DocumentPartType
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
    if element_type == DocumentPartType.ARTICLE:
        return _validate_article(header_str)

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

def extract_number_from_header(header: str, element_type: DocumentPartType) -> str:
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
        
    if element_type == DocumentPartType.BOOK:
        return _extract_book_number(header_str)
    elif element_type == DocumentPartType.TITLE:
        return _extract_title_number(header_str)
    elif element_type == DocumentPartType.CHAPTER:
        return _extract_chapter_number(header_str)
    elif element_type == DocumentPartType.SECTION:
        return _extract_section_number(header_str)
    elif element_type == DocumentPartType.ARTICLE:
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
        return str(ord(first_word.upper()) - ord('A') + 1)
    
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
    
    if first_word == "PRELIMINAR":
        return "PRELIMINAR"  
    
    if first_word in ROMAN_NUMERALS:
        return str(ROMAN_NUMERALS.index(first_word) + 1)
    
    return "0"


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
        
    words = header.split()
    if not words:
        return "0"
        
    first_word = words[0]
    
    try:
        num = int(first_word)
        if num > 0:
            return str(num)
    except ValueError:
        pass
    
    return "0"