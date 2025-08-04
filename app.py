import os
import asyncio
from dotenv import load_dotenv
import logging
from api_client.legislation_client import LegislationClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

WSDL_URL = os.environ.get(
    "WSDL_URL", "https://legislatie.just.ro/apiws/FreeWebService.svc?singleWsdl"
)
CONNECTION_TIMEOUT = int(os.environ.get("CONNECTION_TIMEOUT", "1"))
READ_TIMEOUT = int(os.environ.get("READ_TIMEOUT", "1"))


async def main():
    logger.info("Starting application...")
    try:
        logger.info("Initializing legislation client...")

        client = await LegislationClient.create(
            wsdl_url=WSDL_URL,
            connection_timeout=CONNECTION_TIMEOUT,
            read_timeout=READ_TIMEOUT,
        )

        logger.info("Legislation client successfully started!")

        # Temporary testing
        logger.info("Testing legislation client...")
        results = await client.search_by_text("contract")
        logger.info(f"Found {len(results)} documents.")
        # for r in results:
        #     logger.info(f"Document title: {r.title}")

    except Exception as e:
        logger.exception(f"Error starting application: {e}")


if __name__ == "__main__":
    asyncio.run(main())
