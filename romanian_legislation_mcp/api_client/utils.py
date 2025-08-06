from datetime import datetime
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("utils")

def extract_field_safely(record, field_name: str, required: bool = True) -> Optional[str]:
    """Extract field from API record with error handling.
    
    :param record: The record to parse.
    :param field_name: The field name to extract the value from.
    :param required: Whether the field is required or not.
    :return: The value of the field.
    """
    
    try:
        value = getattr(record, field_name)
        if required and (value is None or value == ""):
            return None
        return value
    except Exception as e:
        logger.warning(f"Error extracting field: {field_name}.")
        return None
        
def extract_date_safely(date_string: str) -> Optional[str]:
    """Parse a date string with fallback handling.
    
    :param date_string: The date string to parse.
    """
    
    if not date_string:
        return None
    
    try:
        return str(datetime.strptime(date_string, "%Y-%m-%d"))
    except Exception as e:
        logger.warning(f"Error extracting date from string {date_string}: {e}.")
        return None