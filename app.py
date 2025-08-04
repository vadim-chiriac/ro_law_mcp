import os
import asyncio
from dotenv import load_dotenv
import logging
from api_client.soap_client import SoapClient
from document_search.search_service import SearchService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

WSDL_URL = os.environ.get(
    "WSDL_URL", "https://legislatie.just.ro/apiws/FreeWebService.svc?singleWsdl"
)
CONNECTION_TIMEOUT = int(os.environ.get("CONNECTION_TIMEOUT", "10"))
READ_TIMEOUT = int(os.environ.get("READ_TIMEOUT", "30"))


async def main():
    logger.info("Starting application...")
    try:
        logger.info("Initializing SOAP client...")

        client = await SoapClient.create(
            wsdl_url=WSDL_URL,
            connection_timeout=CONNECTION_TIMEOUT,
            read_timeout=READ_TIMEOUT,
        )

        search_service = SearchService(soap_client=client)

        logger.info("SOAP client successfully started!")

        # Temporary testing
        logger.info("Testing SOAP client...")

        result = await search_service.try_get_exact_match(
            document_type="ordin",
            number=3216,
            year=2020,
            issuer="MINISTERUL FINANŢELOR PUBLICE"
        )
        if not result:
            logger.info("No result found!")
        else:
            logger.info(f"Document title: {result.title}")
        
        # results = await search_service.search_by_title("NORMA din 16 * 2014")
        # for r in results:
        #     logger.info(r.title)

    except Exception as e:
        logger.exception(f"Error starting application: {e}")


if __name__ == "__main__":
    asyncio.run(main())
