from zeep import Client
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WSDL_URL = 'https://legislatie.just.ro/apiws/FreeWebService.svc?singleWsdl'

class LegislationTester:
    def __init__(self):
        self.client = None
        self.token = None
    
    async def test(self):
        
        try:
            # Create SOAP client
            logger.info('Creating SOAP client for WSDL: %s', WSDL_URL)
            self.client = Client(WSDL_URL)
            
            # Print available operations for debugging            
            logger.info('Getting token...')
            # Get token
            token_result = self.client.service.GetToken()
            self.token = token_result
            logger.info('Token: %s', self.token)
            
            search_model = {
                'NumarPagina': 0,
                'RezultatePagina': 5,
                'SearchAn': None,
                'SearchNumar': None,
                'SearchTitlu': None,
                'SearchText': 'contract'  # Test full-text search
            }
            
            search_result = self.client.service.Search(search_model, self.token)
            logger.info('Search results: %s', json.dumps(search_result, indent=2, ensure_ascii=False, default=str))
            
        except Exception as error:
            logger.error('Error: %s', error)
            # Print more details about the error
            if hasattr(error, 'detail'):
                logger.error('Error detail: %s', error.detail)

# Run the test
import asyncio
tester = LegislationTester()
asyncio.run(tester.test())