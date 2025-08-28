import asyncio
import json
import logging
import os

from dotenv import load_dotenv
from fastmcp import FastMCP
from romanian_legislation_mcp.api_client.soap_client import SoapClient

from romanian_legislation_mcp.api_consumers.document_finder import DocumentFinder
from romanian_legislation_mcp.api_consumers.search_service import SearchService
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
CONNECTION_TIMEOUT = int(os.environ.get("CONNECTION_TIMEOUT", "5"))
READ_TIMEOUT = int(os.environ.get("READ_TIMEOUT", "5"))

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
    # service = SearchService(client)
    # res = await service.search_title("ordonanta de urgenta 1* 2020")
    # for r in res:
    #     logger.info(r.title)
    document_finder = DocumentFinder(legislation_client=client)
    # doc =  await document_finder.get_document("lege", 287, 2009, "parlamentul")
    # logger.info(doc.title)
    service = StructuredDocumentService(document_finder)
    
    document_data = await service.get_document_data(
        document_type="LEGE", number=149, year=2022, issuer="parlamentul"
    )
    if document_data:
        doc = await service.get_document_by_id(document_data["id"])
        logger.info(f"Max depth: {doc.top_element.max_depth}")
        structure = json.dumps(doc.get_element_structure(document_data["id"], 5)).replace("'", "\"")
        
        with open("example.json", "w") as f:
            f.write(structure)
            
        with open("example.txt", "w") as f:
            f.write(json.dumps(doc.base_document.text))
            
        with open("amendment.json", "w") as f:
            f.write(str(doc.get_structural_amendment_data()))
        
        logger.info(f"Parsed document has {len(doc.articles)} articles.")
        #logger.info(doc.get_articles("4"))
    else:
        logger.error(f"Error")
    # logger.info(doc.get_articles("2585"))
    ##logger.info(doc._get_json_structure())
    # for art in list(doc.articles.values()):
    #     logger.info(f"Art no: {art.number}")
    # art_list = list(doc.articles.values())
    # logger.info(f"Article count: {len(art_list)}")
    # logger.info(f"First art: {art_list[0].number}")
    # logger.info(f"Last art: {art_list[-1].number}")
    # # logger.info("Art. content: ")
    # logger.info(doc.base_document.text)
    
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
