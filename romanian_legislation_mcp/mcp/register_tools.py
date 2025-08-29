from mcp.server.fastmcp import FastMCP
from romanian_legislation_mcp.mcp.tools.document_flow import (
    register_get_document_data,
    register_get_article_or_list,
    register_search_in_document,
)

from romanian_legislation_mcp.mcp.tools.utils import (
    register_document_identification_tool,
    register_issuer_mapping_tool,
)
from romanian_legislation_mcp.structured_document.service import (
    StructuredDocumentService,
)

import logging

logger = logging.getLogger(__name__)


def register_tools(app: FastMCP, service: StructuredDocumentService):
    """Register available tools with the MCP server"""

    register_get_document_data(app, service)
    register_get_article_or_list(app, service)
    register_search_in_document(app, service)
    register_issuer_mapping_tool(app)
    register_document_identification_tool(app)

    logger.info("All MCP tools registered successfully.")
