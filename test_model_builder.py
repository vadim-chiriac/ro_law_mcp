import asyncio
import logging
import os

from dotenv import load_dotenv
from fastmcp import FastMCP
from romanian_legislation_mcp.api_client.soap_client import SoapClient

from romanian_legislation_mcp.api_consumers.document_finder import DocumentFinder
from romanian_legislation_mcp.structured_document.service import (
    StructuredDocumentService,
)

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


async def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("Initializing SOAP client...")
    client = SoapClient.create(
        wsdl_url=WSDL_URL,
        connection_timeout=CONNECTION_TIMEOUT,
        read_timeout=READ_TIMEOUT,
    )
    logger.info("SOAP client successfully started!")

    logger.info("Starting search service...")
    # search_service = SearchService(soap_client=client)
    document_finder = DocumentFinder(legislation_client=client)
    service = StructuredDocumentService(document_finder)
    document = await service._get_document(
        document_type="lege", number=287, year=2009, issuer="parlamentul"
    )
    #ogger.info(document.get_json_structure())
    logger.info(document.base_document.number)
    # civil_code = await document_finder.get_document(
    #     document_type="lege", number=287, year=2009, issuer="parlamentul"
    # )
    # logger.info("Search service succesfully started.")
    # builder = ModelBuilder(civil_code)
    # controller = builder.create_controller()
    # logger.info(document.get_article("44"))
    # id = document.get_random_id()
    # element = document.get_element_by_id(id)
    #logger.info(element)
    # res = document.search_in_text("ilicite", 104583, 116448)

    # search_res = document.search_in_text("locatiune")
    # logger.info(res)
    # logger.info(model.get_document_structure())
    # logger.info(builder.model.get_title(16))
    # builder.model.log()


asyncio.run(main())
