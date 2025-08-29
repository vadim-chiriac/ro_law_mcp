import logging
from typing import Dict

from romanian_legislation_mcp.structured_document.service import (
    StructuredDocumentService,
)

logger = logging.getLogger(__name__)


def register_get_document_data(app, document_service: StructuredDocumentService):
    """Register tool to retrieve and structure legal documents."""

    @app.tool()
    async def get_document_data(
        document_type: str, number: int, year: int, issuer: str
    ) -> Dict | None:
        """Use this when you have determined you need to consult a specific document.
        It will fetch it from the database and parse it to create a structured representation.
        The table of contents from the returned dict is particularly important, as it will allow you
        to narrow down a search to specific parts of a document's contents.
        
        Args:
            document_type: Type of document (e.g., "LEGE", "ORDONANTA")
            number: Document number
            year: Year of publication
            issuer: Issuing authority (use get_correct_issuer tool for proper mapping)

        Returns:
            Dict containing:
            - document_type: Type of document
            - title: Full document title
            - issuer: Issuing authority
            - content_length: Total character count
            - article_count: Number of articles found
            - table_of_content: Document element hierarchy
            - structural_amendment_data: Information about major changes further made to the document
                which are not included in this data
        """

        document = await document_service.get_document(
            document_type, number, year, issuer
        )
        if document is None:
            return {"error": f"Document {document_type} {number}/{year} issued by {issuer} with not found."}

        data = {
            "document_type": document.base_document.document_type,
            "title": document.base_document.title,
            "issuer": document.base_document.issuer,
            "content_length": len(document.base_document.text),
            "article_count": len(document.articles),
            "table_of_content": document.top_element.get_structure(),
            "structural_amendment_data": document.get_structural_amendment_data(),
        }

        return data


def register_get_article_or_list(app, document_service: StructuredDocumentService):
    """Register tool to get specific article content."""

    @app.tool()
    async def get_one_or_more_articles(
        document_type: str,
        number: int,
        year: int,
        issuer: str,
        article_number_or_list: str,
    ) -> dict:
        """Get the full content of one or more specific articles (comma separated) from a document.

        IMPORTANT: Always check the returned amendments list. If relevant articles have been amended,
        you should retrieve the amending law using the `get_document_data` tool to see
        what changes were made. The base document only contains original text.

        Args:
            document_type: Type of document (e.g., "LEGE", "ORDONANTA")
            number: Document number
            year: Year of publication
            issuer: Issuing authority
            article_number_or_list: Article number as string (e.g., "25", "31") or as comma-separated list (e.g. "25,31").

        Returns:
            Dict containing structured article data.
        """

        document = await document_service.get_document(
            document_type, number, year, issuer
        )
        if document is None:
            return {"error": f"Document {document_type} {number}/{year} issued by {issuer} with not found."}

        if article_number_or_list.find(",") != -1:
            article_number_or_list = article_number_or_list.split(",")

        articles = document.get_one_or_more_articles(article_number_or_list)
        return articles


def register_search_in_document(app, document_service: StructuredDocumentService):
    """Register tool to search within an element text."""

    @app.tool()
    async def search_in_document(
        document_type: str,
        number: int,
        year: int,
        issuer: str,
        search_query: str,
        start_pos: int = 0,
        end_pos: int = -1,
        max_excerpts: int = 5,
        excerpt_context_chars: int = 250
    ) -> dict:
        """Search the text contents (fuzzy search) of a document. When possible, always use start and end positions
        to narrow the search down to relevant parts of the documents (e.g. a certain book, title, chapter etc.) 
        as obtained from the 'get_document_data' tool.

        IMPORTANT: If you have identified relevant provisions by searching an element, and you can determine which
        article they belong to, use the "get_article_or_list" tool to get structured data for the relevant article 
        and check if it has further amendments, as these are not included in the retrieved document.

        Args:
            document_type: Type of document (e.g., "LEGE", "ORDONANTA")
            number: Document number
            year: Year of publication
            issuer: Issuing authority
            search_query: Text to search for (handles Romanian diacritics)
            start_pos: Start position in element text (default: 0 for beginning)
            end_pos: End position in element text (default: -1 for end)
            max_excerpts: Maximum number of search result excerpts (default: 5)
            excerpt_context_chars: Characters of context around each match (default: 250)

        Returns:
            Dict containing search results with excerpts and positions
        """
        
        document = await document_service.get_document(
            document_type, number, year, issuer
        )
        if document is None:
            return {"error": f"Document {document_type} {number}/{year} issued by {issuer} with not found."}


        return document.search_document(
            search_query,
            start_pos,
            end_pos,
            max_excerpts,
            excerpt_context_chars,
        )
