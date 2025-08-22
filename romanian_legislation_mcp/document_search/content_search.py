from typing import Any, Dict, Optional
from romanian_legislation_mcp.api_client.utils import create_fuzzy_romanian_pattern
import re


def text_search(
    text: str,
    search_query: str,
    max_excerpts: int = 5,
    excerpt_context_chars: int = 500,
) -> Dict[str, Any]:
    """Search for specific content within a identified legal document.
    :param text:
    :param search_query: What to search for within that document
    :param max_excerpts: Maximum number of relevant excerpts to return
    :param excerpt_context_chars: Characters of context around each match
    :param search_position: Optional position in document to center search around
    :param search_radius: Characters before/after search_position to search within
    :return: Dictionary containing document info and matching excerpts
    """

    search_text = text
    fuzzy_pattern = create_fuzzy_romanian_pattern(
        search_query, allow_partial_words=True
    )
    query_pattern = re.compile(fuzzy_pattern, re.IGNORECASE)
    matches = list(query_pattern.finditer(search_text))

    if not matches:
        return {
            "excerpts": [],
            "total_matches": 0,
            "search_query": search_query,
        }

    excerpts = []
    text_len = len(text)

    for i, match in enumerate(matches[:max_excerpts]):
        actual_match_start = match.start()
        actual_match_end = match.end()

        start_pos = max(0, actual_match_start - excerpt_context_chars)
        end_pos = min(text_len, actual_match_end + excerpt_context_chars)

        excerpt_text = text[start_pos:end_pos]

        match_start_in_excerpt = actual_match_start - start_pos
        match_end_in_excerpt = actual_match_end - start_pos

        excerpts.append(
            {
                "excerpt_number": i + 1,
                "text": excerpt_text,
                "match_start_in_excerpt": match_start_in_excerpt,
                "match_end_in_excerpt": match_end_in_excerpt,
                "position_in_document": actual_match_start,
                "match_length": actual_match_end - actual_match_start,
            }
        )

    return {
        "excerpts": excerpts,
        "total_matches": len(matches),
        "search_query": search_query,
        "showing_excerpts": min(len(matches), max_excerpts),
        "excerpt_context_chars": excerpt_context_chars,
    }
