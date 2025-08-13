from datetime import datetime
import logging
import re
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("utils")


def extract_field_safely(
    record, field_name: str, required: bool = True
) -> Optional[str]:
    """Extract field from API record with error handling.

    :param record: The record to parse.
    :param field_name: The field name to extract the value from.
    :param required: Whether the field is required or not.
    :return: The value of the field.
    """

    try:
        value = getattr(record, field_name)
        if required and (value is None or value == ""):
            return None
        return value
    except Exception as e:
        logger.warning(f"Error extracting field: {field_name}.")
        return None


def extract_date_safely(date_string: str) -> Optional[str]:
    """Parse a date string with fallback handling.

    :param date_string: The date string to parse.
    """

    if not date_string:
        return None

    try:
        return str(datetime.strptime(date_string, "%Y-%m-%d"))
    except Exception as e:
        logger.warning(f"Error extracting date from string {date_string}: {e}.")
        return None


def normalize_romanian_text(text: str) -> str:
    """Normalize Romanian text by replacing diacritics with base characters.

    :param text: Text to normalize
    :return: Text with diacritics replaced
    """
    if not text:
        return text

    return (
        text.replace("ă", "a")
        .replace("Ă", "A")
        .replace("â", "a")
        .replace("Â", "A")
        .replace("î", "i")
        .replace("Î", "I")
        .replace("ț", "t")
        .replace("Ț", "T")
        .replace("ţ", "t")
        .replace("Ţ", "T")
        .replace("ș", "s")
        .replace("Ș", "S")
        .replace("ş", "s")
        .replace("Ş", "S")
    )


def create_fuzzy_romanian_pattern(query: str, allow_partial_words: bool = False) -> str:
    """Create a regex pattern that matches Romanian text with or without diacritics.

    :param query: The search query
    :param allow_partial_words: If True, allows matching partial words (e.g., "durata locatiunii" matches "durata maxima a locatiunii")
    :return: Regex pattern that matches diacritic variations and optionally partial words
    """
    if not query:
        return query

    char_variations = {
        "a": "[aăâ]",
        "ă": "[aăâ]",
        "â": "[aăâ]",
        "A": "[AĂÂ]",
        "Ă": "[AĂÂ]",
        "Â": "[AĂÂ]",
        "i": "[iî]",
        "î": "[iî]",
        "I": "[IÎ]",
        "Î": "[IÎ]",
        "t": "[tțţ]",
        "ț": "[tțţ]",
        "ţ": "[tțţ]",
        "T": "[TȚŢ]",
        "Ț": "[TȚŢ]",
        "Ţ": "[TȚŢ]",
        "s": "[sșş]",
        "ș": "[sșş]",
        "ş": "[sșş]",
        "S": "[SȘŞ]",
        "Ș": "[SȘŞ]",
        "Ş": "[SȘŞ]",
    }

    if allow_partial_words:
        words = query.strip().split()
        word_patterns = []

        for word in words:
            word_pattern_parts = []
            for char in word:
                if char in char_variations:
                    word_pattern_parts.append(char_variations[char])
                else:
                    word_pattern_parts.append(re.escape(char))
            word_patterns.append("".join(word_pattern_parts))

        if len(word_patterns) == 1:
            return word_patterns[0]
        else:
            flexible_separator = r"(?:\s+\S+){0,50}?\s+"
            return flexible_separator.join(word_patterns)
    else:
        pattern_parts = []
        for char in query:
            if char in char_variations:
                pattern_parts.append(char_variations[char])
            else:
                pattern_parts.append(re.escape(char))

        return "".join(pattern_parts)
