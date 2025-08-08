"""
Validation utilities for MCP tool parameters.
"""

from typing import Dict, Any, Optional


def validate_document_identification(
    document_type: str, 
    number: int, 
    year: int, 
    issuer: str
) -> Optional[Dict[str, Any]]:
    """
    Validate common document identification parameters.
    
    Args:
        document_type: The type of document (e.g. 'lege')
        number: The number of the document
        year: The year the document was issued
        issuer: The issuing authority of the document
    
    Returns:
        Error dict if validation fails, None if valid
    """
    if not document_type.strip():
        return {"document_found": False, "error": "Document type cannot be empty"}

    if number < 0:
        return {
            "document_found": False,
            "error": "Document number cannot be negative",
        }

    if year < 0:
        return {
            "document_found": False,
            "error": "Document year cannot be negative",
        }

    if not issuer.strip():
        return {"document_found": False, "error": "Document issuer cannot be empty"}

    return None


def validate_search_query(search_query: str) -> Optional[Dict[str, Any]]:
    """
    Validate search query parameter.
    
    Args:
        search_query: The search query string
    
    Returns:
        Error dict if validation fails, None if valid
    """
    if not search_query.strip():
        return {"document_found": False, "error": "Search query cannot be empty"}
    
    return None


def validate_search_parameters(
    max_excerpts: int,
    excerpt_context_chars: int,
    search_position: Optional[int] = None,
    search_radius: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """
    Validate search-related parameters.
    
    Args:
        max_excerpts: Maximum number of excerpts to return
        excerpt_context_chars: Characters of context around matches
        search_position: Optional position in document to center search around
        search_radius: Optional radius for positional search
    
    Returns:
        Error dict if validation fails, None if valid
    """
    if max_excerpts <= 0:
        return {"document_found": False, "error": "Max excerpts must be positive"}

    if excerpt_context_chars < 0:
        return {
            "document_found": False,
            "error": "Excerpt context chars cannot be negative",
        }

    if search_position is not None and search_position < 0:
        return {
            "document_found": False,
            "error": "Search position cannot be negative",
        }

    if search_radius is not None and search_radius <= 0:
        return {
            "document_found": False,
            "error": "Search radius must be positive",
        }

    return None


def validate_simple_search_parameters(query: str, max_results: Optional[int]) -> Optional[Dict[str, Any]]:
    """
    Validate parameters for simple search operations (content, title, number search).
    
    Args:
        query: Search query string
        max_results: Optional maximum results limit
    
    Returns:
        Error dict if validation fails, None if valid
    """
    if not query or query.strip() == "":
        return {"results": [], "error": "Query cannot be empty."}

    if max_results is not None and max_results <= 0:
        return {"results": [], "error": "Max results must be positive."}

    return None


def validate_document_search_parameters(
    document_type: str, 
    number: int, 
    year: int, 
    issuer: str
) -> Optional[Dict[str, Any]]:
    """
    Validate parameters for exact document search.
    
    Args:
        document_type: The type of document (e.g. 'lege')
        number: The number of the document
        year: The year the document was issued
        issuer: The issuing authority of the document
    
    Returns:
        Error dict if validation fails, None if valid
    """
    if document_type.strip() == "":
        return {"results": [], "error": "Document type cannot be empty."}

    # Some documents actually have 0 as number in the SOAP API database
    if number < 0:
        return {"results": [], "error": "Document number cannot be less than 0."}

    if year < 0:
        return {"results": [], "error": "Document year cannot be less than 0."}

    if issuer.strip() == "":
        return {"results": [], "error": "Document issuer cannot be empty."}

    return None