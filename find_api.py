#!/usr/bin/env python3
"""
Script to discover the correct Tecmundo API endpoints.
"""

import sys
import json
import time
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.logger import get_logger
from src.utils.http_client import HTTPClient

logger = get_logger(__name__)

BASE_URL = "https://www.tecmundo.com.br"

# Common API endpoint patterns
ENDPOINTS_TO_TRY = [
    "/api/posts",
    "/api/articles",
    "/api/content",
    "/api/news",
    "/api/blog",
    "/api/feed",
    "/wp-json/wp/v2/posts",  # WordPress REST API
    "/wp-json/wp/v2/posts?per_page=20",
    "/api/posts?page=1",
    "/api/posts?limit=20",
    "/api/v1/posts",
    "/api/v2/posts",
    "/feed",
    "/rss",
    "/rss.xml",
    "/api/posts?endpoint=home",
    "/api/posts?endpoint=latest",
    "/api/posts?endpoint=recent",
    "/api/posts?category=tech",
]


def test_endpoint(endpoint):
    """Test a single endpoint."""
    try:
        client = HTTPClient()
        url = f"{BASE_URL}{endpoint}"
        
        logger.info(f"Testing: {url}")
        
        response = client.get(url, timeout=10)
        content_type = response.headers.get('content-type', '')
        
        if response.status_code == 200:
            logger.info(f"  ✅ Status: 200")
            logger.info(f"  Content-Type: {content_type}")
            logger.info(f"  Size: {len(response.text)} chars")
            
            if 'json' in content_type.lower():
                try:
                    data = response.json()
                    logger.info(f"  JSON structure: {type(data)}")
                    
                    if isinstance(data, dict):
                        keys = list(data.keys())
                        logger.info(f"  Keys: {keys[:10]}...")
                        
                        # Look for array of posts/articles
                        for key in keys:
                            value = data[key]
                            if isinstance(value, list) and len(value) > 0:
                                logger.info(f"  🎯 Found array '{key}' with {len(value)} items")
                                
                                # Check first item
                                if isinstance(value[0], dict):
                                    item_keys = list(value[0].keys())
                                    logger.info(f"     First item keys: {item_keys[:15]}...")
                                    
                                    # Check for typical article fields
                                    article_indicators = ['title', 'content', 'id', 'slug', 'author']
                                    found_indicators = [k for k in article_indicators if k in item_keys]
                                    if found_indicators:
                                        logger.info(f"     🎉 LOOKS LIKE ARTICLES! Found: {found_indicators}")
                                        return True, url, data
                    
                    elif isinstance(data, list) and len(data) > 0:
                        logger.info(f"  Direct array with {len(data)} items")
                        if isinstance(data[0], dict):
                            item_keys = list(data[0].keys())
                            logger.info(f"  First item keys: {item_keys[:15]}...")
                            
                            article_indicators = ['title', 'content', 'id', 'slug', 'author']
                            found_indicators = [k for k in article_indicators if k in item_keys]
                            if found_indicators:
                                logger.info(f"  🎉 LOOKS LIKE ARTICLES! Found: {found_indicators}")
                                return True, url, data
                    
                except json.JSONDecodeError:
                    logger.info("  ❌ Invalid JSON")
            
            elif 'xml' in content_type.lower() or 'rss' in content_type.lower():
                logger.info("  📄 XML/RSS feed detected")
                # Could parse RSS if needed
                if 'item' in response.text.lower() or 'entry' in response.text.lower():
                    logger.info("  🎉 RSS feed with items found!")
                    return True, url, response.text[:1000]
        
        else:
            logger.info(f"  ❌ Status: {response.status_code}")
        
        client.close()
        
    except Exception as e:
        logger.info(f"  ❌ Error: {e}")
    
    return False, None, None


def main():
    """Test various endpoints to find the correct API."""
    logger.info("🔍 Searching for Tecmundo API endpoints...")
    logger.info("=" * 60)
    
    working_endpoints = []
    
    for endpoint in ENDPOINTS_TO_TRY:
        success, url, data = test_endpoint(endpoint)
        
        if success:
            working_endpoints.append({
                'url': url,
                'endpoint': endpoint,
                'data_preview': str(data)[:200] if data else None
            })
        
        # Be respectful with rate limiting
        time.sleep(1)
        logger.info("-" * 40)
    
    logger.info("\n" + "=" * 60)
    logger.info("🎯 RESULTS")
    logger.info("=" * 60)
    
    if working_endpoints:
        logger.info(f"Found {len(working_endpoints)} working endpoints:")
        
        for i, ep in enumerate(working_endpoints, 1):
            logger.info(f"\n{i}. {ep['url']}")
            if ep['data_preview']:
                logger.info(f"   Preview: {ep['data_preview']}...")
    else:
        logger.warning("❌ No working endpoints found with article-like content")
        logger.info("\n💡 Suggestions:")
        logger.info("1. The site might use a different API structure")
        logger.info("2. Try inspecting the network tab when browsing the site")
        logger.info("3. Look for GraphQL endpoints")
        logger.info("4. Check if the site uses a headless CMS")
        logger.info("5. Consider scraping HTML instead of using API")


if __name__ == "__main__":
    main()