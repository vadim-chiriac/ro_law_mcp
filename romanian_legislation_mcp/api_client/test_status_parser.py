#!/usr/bin/env python3
"""
Test script for document status parsing functionality.
Tests the SOAP client with integrated status parsing without going through MCP layer.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from romanian_legislation_mcp.api_client.soap_client import SoapClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

WSDL_URL = os.environ.get(
    "WSDL_URL", "https://legislatie.just.ro/apiws/FreeWebService.svc?singleWsdl"
)
CONNECTION_TIMEOUT = int(os.environ.get("CONNECTION_TIMEOUT", "10"))
READ_TIMEOUT = int(os.environ.get("READ_TIMEOUT", "30"))


async def test_status_parsing():
    """Test the status parsing functionality with real documents."""
    
    logger.info("Initializing SOAP client with status parsing...")
    
    try:
        # Create SOAP client (should now include status parser)
        client = SoapClient.create(
            wsdl_url=WSDL_URL,
            connection_timeout=CONNECTION_TIMEOUT,
            read_timeout=READ_TIMEOUT,
        )
        logger.info("SOAP client successfully created!")
        
        # Test 1: Search for a few documents
        logger.info("\n=== Test 1: Basic search with status parsing ===")
        results = await client.search_raw(text="lege", page_size=3)
        
        if results:
            logger.info(f"Found {len(results)} documents")
            for i, doc in enumerate(results, 1):
                logger.info(f"\nDocument {i}:")
                logger.info(f"  Title: {doc.title[:80]}...")
                logger.info(f"  Number: {doc.number}")
                logger.info(f"  Type: {doc.document_type}")
                logger.info(f"  URL: {doc.url}")
                logger.info(f"  Status: {doc.status}")
        else:
            logger.warning("No results found")
            
        # Test 2: Search for a specific document type
        logger.info("\n=== Test 2: Search by document number ===")
        results = await client.search_raw(number="95", year=2006, page_size=2)
        
        if results:
            logger.info(f"Found {len(results)} documents")
            for i, doc in enumerate(results, 1):
                logger.info(f"\nDocument {i}:")
                logger.info(f"  Title: {doc.title}")
                logger.info(f"  Number: {doc.number}")
                logger.info(f"  Year: {doc.effective_date.year if doc.effective_date else 'Unknown'}")
                logger.info(f"  URL: {doc.url}")
                logger.info(f"  Status: {doc.status}")
        else:
            logger.warning("No results found for number search")
            
        # Test 3: Check if we can find documents with different statuses
        logger.info("\n=== Test 3: Status distribution ===")
        larger_results = await client.search_raw(text="ordin", page_size=10)
        
        if larger_results:
            status_counts = {}
            for doc in larger_results:
                status = str(doc.status) if doc.status else "None"
                status_counts[status] = status_counts.get(status, 0) + 1
            
            logger.info("Status distribution:")
            for status, count in status_counts.items():
                logger.info(f"  {status}: {count} documents")
        
        logger.info("\n=== Status parsing test completed ===")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise


async def test_specific_document():
    """Test status parsing for a specific document URL if provided."""
    
    # You can modify this URL to test specific documents
    test_url = "https://legislatie.just.ro/Public/DetaliiDocument/33131"
    
    logger.info(f"\n=== Testing specific document: {test_url} ===")
    
    try:
        client = SoapClient.create(
            wsdl_url=WSDL_URL,
            connection_timeout=CONNECTION_TIMEOUT,
            read_timeout=READ_TIMEOUT,
        )
        
        # Test the status parser directly
        if hasattr(client, 'status_parser') and client.status_parser:
            status = client.status_parser.get_document_status(test_url)
            logger.info(f"Direct status check result: {status}")
        else:
            logger.warning("Status parser not available")
            
    except Exception as e:
        logger.error(f"Specific document test failed: {e}")


if __name__ == "__main__":
    print("Starting status parser test...")
    print("This will test the SOAP client with integrated status parsing.")
    print("Make sure you have implemented DocumentStatusParser before running this test.\n")
    
    # Run the tests
    asyncio.run(test_status_parsing())
    asyncio.run(test_specific_document())
