import logging
from typing import Dict

from romanian_legislation_mcp.structured_document.service import (
    StructuredDocumentService,
)

logger = logging.getLogger(__name__)

def register_test(app, document_service: StructuredDocumentService):
    @app.tool()
    async def test() -> Dict | None:
        civil_code_data = await document_service.get_document_data(
            "lege", 287, 2009, "parlamentul"
        )
        id = civil_code_data["id"]
        
        civil_code = await document_service.get_document_by_id(id)
        
        return {
            "id":civil_code_data["id"],
            "structure": civil_code._get_json_structure()
        }

def register_get_document_data(app, document_service: StructuredDocumentService):
    """Register tool to retrieve and structure legal documents."""
    
    @app.tool()
    async def get_document_data(
        document_type: str, number: int, year: int, issuer: str
    ) -> Dict | None:
        """Retrieve a Romanian legal document and create its structured representation.

        Use this FIRST when the you need to search a new legal document. You will receive
        an id that you will use for subsequent queries, as well as a json representation
        of the document hierarchy. Use this to inform further operations on the document.

        Args:
            document_type: Type of document (e.g., "LEGE", "ORDONANTA")
            number: Document number
            year: Year of publication
            issuer: Issuing authority (use get_correct_issuer tool for proper mapping)

        Returns:
            Dict containing:
            - id: Unique document ID for other tool calls
            - document_type: Type of document
            - title: Full document title
            - issuer: Issuing authority
            - content_length: Total character count
            - article_count: Number of articles found
            - element_count: Number of structural elements (books, titles, etc.)
            - structure: Document element hierarchy
            - amendment_data: General amendment information
        """
        return await document_service.get_document_data(
            document_type, number, year, issuer
        )

def register_get_article_or_list(app, document_service: StructuredDocumentService):
    """Register tool to get specific article content."""

    @app.tool()
    async def get_article_or_list(id: str, article_number_or_list: str) -> dict:
        """Get the full content of one or more specific articles (comma separated) from a document.

        IMPORTANT: Always check the returned amendments list. If relevant articles have been amended,
        you should retrieve the amending law using get_document_data to see
        what changes were made. The base document only contains original text.

        Args:
            id: Document ID obtained from get_document_data
            article_number: Article number as string (e.g., "25", "31")

        Returns:
            Dict containing article number, content text, amendments (if any), start_pos, end_pos
        """
        document = await document_service.get_document_by_id(id)
        if document is None:
            return {"error": f"Document with {id} not found."}

        if article_number_or_list.find(",") != -1:
            article_number_or_list = article_number_or_list.split(",")
            
        articles = document.get_articles(article_number_or_list)
        return articles

def register_get_element_by_id(app, document_service: StructuredDocumentService):
    """Register tool to get content by element ID."""

    @app.tool()
    async def get_element_by_id(
        id: str, element_id: str, include_amendments: bool = True
    ) -> dict:
        """Get content of a document element by its ID.

        Useful for getting content of books, titles, chapters, or sections identified
        from the JSON structure.

        IMPORTANT: When retrieving an element, always check the returned amendments list.
        If articles within this element have been amended, you should:
        1. Use get_document_data to retrieve the amending law mentioned in amendments
        2. Check what changes were made to get the current version of the law
        3. The base document only contains original text, not consolidated changes

        Args:
            id: Document ID obtained from get_document_data
            element_id: Element ID from the JSON structure
            include_amendments: Whether to include amendment information (default: True)

        Returns:
            Dict containing element number, content text, amendments (if requested), start_pos, end_pos
        """
        document = await document_service.get_document_by_id(id)
        if document is None:
            return {"error": f"Document with {id} not found."}

        element = document.get_element_by_id(element_id, include_amendments)
        if element is None:
            return {"error": f"Element with ID {element_id} not found in document."}
        
        return element


def register_search_in_element(app, document_service: StructuredDocumentService):
    """Register tool to search within an element text."""

    @app.tool()
    async def search_in_element(
        document_id: str,
        element_id: str,
        search_query: str,
        start_pos: int = 0,
        end_pos: int = -1,
        max_excerpts: int = 5,
        excerpt_context_chars: int = 500,
    ) -> dict:
        """Search for text within a document or document section.

        Performs fuzzy search that handles Romanian diacritics automatically.

        Args:
            document_id: Document ID obtained from get_document_data
            element_id: The ID of the elements to search in
            search_query: Text to search for (handles Romanian diacritics)
            start_pos: Start position in document text (default: 0 for beginning)
            end_pos: End position in document text (default: -1 for end)
            max_excerpts: Maximum number of search result excerpts (default: 5)
            excerpt_context_chars: Characters of context around each match (default: 500)

        Returns:
            Dict containing search results with excerpts and positions
        """
        document = await document_service.get_document_by_id(document_id)
        if document is None:
            return {"error": f"Document with {document_id} not found."}

        return document.search_in_element(
            element_id,
            search_query,
            start_pos,
            end_pos,
            max_excerpts,
            excerpt_context_chars,
        )