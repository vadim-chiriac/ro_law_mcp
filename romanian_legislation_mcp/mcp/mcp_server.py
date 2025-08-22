from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import uvicorn
import logging
import os

from romanian_legislation_mcp.api_client.soap_client import SoapClient
from romanian_legislation_mcp.api_consumers.document_finder import DocumentFinder
from romanian_legislation_mcp.api_consumers.search_service import SearchService
from romanian_legislation_mcp.mcp.register_tools import register_tools
from romanian_legislation_mcp.structured_document.service import StructuredDocumentService
logger = logging.getLogger(__name__)

load_dotenv()
PORT = int(os.environ.get("MCP_PORT", "5000"))
HOSTNAME = os.environ.get("MCP_HOSTNAME", "localhost")
WSDL_URL = os.environ.get(
    "WSDL_URL", "https://legislatie.just.ro/apiws/FreeWebService.svc?singleWsdl"
)
CONNECTION_TIMEOUT = int(os.environ.get("CONNECTION_TIMEOUT", "10"))
READ_TIMEOUT = int(os.environ.get("READ_TIMEOUT", "30"))

app = FastMCP("Romanian Legislation MCP server")

def start_server():
    """Initializes and starts the MCP server"""
    
    init_resources()
    
    logger.info("Starting MCP server in STDIO mode...")
    logger.info("Server will communicate via stdin/stdout for MCP protocol")
    
    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


async def start_server_async():
    """Async version of the MCP server start"""
    init_resources()
    await app.run_stdio_async()


def start_http_server():
    """Starts the MCP server in HTTP mode"""
    
    init_resources()
    
    server_url = f"http://{HOSTNAME}:{PORT}"
    logger.info(f"MCP server starting on {server_url}")
    logger.info(f"MCP endpoint will be available at {server_url}/mcp")
    
    try:
        asgi_app = app.streamable_http_app()
        uvicorn.run(asgi_app, host=HOSTNAME, port=PORT)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


def init_resources():
    """Initializes underlying resources needed for SOAP API connection"""
        
    logger.info("Initializing SOAP client...")
    client = SoapClient.create(
        wsdl_url=WSDL_URL,
        connection_timeout=CONNECTION_TIMEOUT,
        read_timeout=READ_TIMEOUT,
    )
    logger.info("SOAP client successfully started!")

    logger.info("Starting document service...")
    document_finder = DocumentFinder(legislation_client=client)
    service = StructuredDocumentService(document_finder)
    logger.info("Document service succesfully started.")

    register_tools(app, service)
