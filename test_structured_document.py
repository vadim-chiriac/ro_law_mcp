import asyncio
import json
import logging
import os
import argparse
import sys

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
WSDL_URL = os.environ.get(
    "WSDL_URL", "https://legislatie.just.ro/apiws/FreeWebService.svc?singleWsdl"
)
CONNECTION_TIMEOUT = int(os.environ.get("CONNECTION_TIMEOUT", "5"))
READ_TIMEOUT = int(os.environ.get("READ_TIMEOUT", "5"))

app = FastMCP("Romanian Legislation MCP server")


def parse_arguments():
    """Parse command line arguments for document identification."""
    parser = argparse.ArgumentParser(
        description="Test structured document parsing with Romanian legislation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_structured_document.py --type LEGE --number 286 --year 2009 --issuer Parlamentul
  python test_structured_document.py -t ORDONANTA -n 57 -y 2019 -i "Guvernul"
        """
    )
    
    parser.add_argument(
        "--type", "-t",
        required=True,
        help="Document type (e.g., LEGE, ORDONANTA, HOTARARE)"
    )
    
    parser.add_argument(
        "--number", "-n",
        type=int,
        required=True,
        help="Document number"
    )
    
    parser.add_argument(
        "--year", "-y",
        type=int,
        required=True,
        help="Document year"
    )
    
    parser.add_argument(
        "--issuer", "-i",
        required=True,
        help="Issuer (e.g., Parlamentul, Guvernul)"
    )
    
    parser.add_argument(
        "--article", "-a",
        help="Specific article number to retrieve (optional)"
    )
    
    return parser.parse_args()


async def main():
    args = parse_arguments()
    
    logging.basicConfig(level=logging.INFO)
    logger.info("Initializing SOAP client...")
    client = SoapClient.create(
        wsdl_url=WSDL_URL,
        connection_timeout=CONNECTION_TIMEOUT,
        read_timeout=READ_TIMEOUT,
    )
    logger.info("SOAP client successfully started!")

    document_finder = DocumentFinder(legislation_client=client)
    service = StructuredDocumentService(document_finder)
    
    logger.info(f"Fetching document: {args.type} {args.number}/{args.year} by {args.issuer}")
    
    document = await service.get_document(
        document_type=args.type, 
        number=args.number, 
        year=args.year, 
        issuer=args.issuer
    )
    
    if document:
        logger.info(f"Successfully retrieved document: {document.base_document.title}")
        logger.info(f"Parsed document has {len(document.articles)} articles.")
        
        structure = json.dumps(document.top_element.get_structure(), indent=2, ensure_ascii=False)
        structure_filename = f"structure_{args.type}_{args.number}_{args.year}.json"
        with open(structure_filename, "w", encoding="utf-8") as f:
            f.write(structure)
        logger.info(f"Document structure saved to {structure_filename}")
        
        amendments_filename = f"amendments_{args.type}_{args.number}_{args.year}.json"
        with open(amendments_filename, "w", encoding="utf-8") as f:
            json.dump(document.amendment_data, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Amendment data saved to {amendments_filename}")
        
        if args.article:
            logger.info(f"Retrieving article {args.article}:")
            article_data = document.get_one_or_more_articles(args.article)
            logger.info(str(article_data))
        else:
            article_numbers = list(document.articles.keys())[:3]
            if article_numbers:
                logger.info(f"Sample articles available: {', '.join(article_numbers)}")
                logger.info("Use --article/-a flag to retrieve a specific article")
    else:
        logger.error(f"Failed to retrieve document: {args.type} {args.number}/{args.year} by {args.issuer}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
