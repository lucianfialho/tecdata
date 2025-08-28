#!/usr/bin/env python3
"""
Debug script to examine Tecmundo API response structure in detail.
"""

import sys
import json
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.logger import get_logger
from src.utils.http_client import HTTPClient
from config.settings import settings

logger = get_logger(__name__)


def debug_api_response():
    """Debug the actual API response structure."""
    
    try:
        client = HTTPClient()
        url = settings.api.tecmundo_full_url
        
        logger.info(f"Fetching: {url}")
        response = client.get(url)
        data = response.json()
        
        logger.info("Raw JSON Response:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        client.close()
        
    except Exception as e:
        logger.error(f"Failed to fetch or parse response: {e}")


if __name__ == "__main__":
    debug_api_response()