#!/usr/bin/env python3
"""
Test script to validate Tecmundo API collection without database dependency.
This demonstrates the core collection and parsing functionality.
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


def test_api_connection():
    """Test direct API connection and response structure."""
    logger.info("🔌 Testing Tecmundo API Connection")
    logger.info("-" * 50)
    
    try:
        client = HTTPClient()
        url = settings.api.tecmundo_full_url
        
        logger.info(f"API URL: {url}")
        
        # Make request
        response = client.get(url)
        logger.info(f"✅ Response Status: {response.status_code}")
        logger.info(f"Response Headers Content-Type: {response.headers.get('content-type')}")
        logger.info(f"Response Size: {len(response.text)} characters")
        
        # Parse JSON
        data = response.json()
        logger.info(f"JSON Type: {type(data)}")
        
        if isinstance(data, dict):
            logger.info(f"Top-level keys: {list(data.keys())}")
        elif isinstance(data, list):
            logger.info(f"Array with {len(data)} items")
        
        client.close()
        return True, data
        
    except Exception as e:
        logger.error(f"❌ API connection failed: {e}")
        return False, None


def analyze_response_structure(data):
    """Analyze the structure of the API response."""
    logger.info("\n📊 Response Structure Analysis")
    logger.info("-" * 50)
    
    try:
        # Try to find articles/posts in various places
        posts = []
        
        if isinstance(data, list):
            posts = data
            logger.info(f"Direct array with {len(posts)} items")
        elif isinstance(data, dict):
            logger.info("Dictionary structure found")
            
            # Check common keys
            for key in ['posts', 'articles', 'data', 'items', 'results', 'content']:
                if key in data:
                    value = data[key]
                    logger.info(f"Found key '{key}': {type(value)}")
                    if isinstance(value, list):
                        posts = value
                        logger.info(f"Using '{key}' as posts array ({len(posts)} items)")
                        break
                    elif isinstance(value, dict):
                        logger.info(f"'{key}' contains: {list(value.keys())}")
            
            if not posts and ('title' in data or 'id' in data):
                posts = [data]
                logger.info("Treating whole response as single post")
        
        if posts:
            logger.info(f"\n📄 Found {len(posts)} potential articles")
            
            # Analyze first few posts
            for i, post in enumerate(posts[:3]):
                logger.info(f"\n--- Post {i+1} ---")
                if isinstance(post, dict):
                    logger.info("Available fields:")
                    for key, value in post.items():
                        value_type = type(value).__name__
                        if isinstance(value, str):
                            preview = value[:50] + "..." if len(value) > 50 else value
                        elif isinstance(value, (dict, list)):
                            preview = f"{len(value)} items"
                        else:
                            preview = str(value)
                        logger.info(f"  {key}: ({value_type}) {preview}")
                else:
                    logger.info(f"Non-dict item: {type(post)} - {post}")
        else:
            logger.warning("❌ No posts/articles found in response")
        
        return posts
        
    except Exception as e:
        logger.error(f"❌ Structure analysis failed: {e}")
        return []


def test_parsing_logic(posts):
    """Test article parsing logic with real data."""
    logger.info("\n🔍 Testing Parsing Logic")
    logger.info("-" * 50)
    
    if not posts:
        logger.warning("No posts to parse")
        return []
    
    try:
        # Import the collector parsing logic
        from src.collectors.tecmundo import TecmundoCollector
        
        collector = TecmundoCollector()
        
        parsed_articles = []
        for i, post in enumerate(posts):
            try:
                article_data = collector._parse_single_post(post)
                if article_data:
                    parsed_articles.append(article_data)
                    logger.info(f"✅ Post {i+1}: {article_data['title'][:60]}...")
                else:
                    logger.warning(f"⚠️  Post {i+1}: Failed to parse")
            except Exception as e:
                logger.error(f"❌ Post {i+1}: Error parsing - {e}")
        
        logger.info(f"\n📈 Parsing Results:")
        logger.info(f"Total posts: {len(posts)}")
        logger.info(f"Successfully parsed: {len(parsed_articles)}")
        logger.info(f"Success rate: {len(parsed_articles)/len(posts)*100:.1f}%")
        
        # Field analysis
        if parsed_articles:
            fields = ['external_id', 'title', 'author', 'category', 'url', 'summary', 'image_url']
            logger.info(f"\n📊 Field Extraction Success Rates:")
            
            for field in fields:
                count = sum(1 for article in parsed_articles if article.get(field))
                rate = count / len(parsed_articles) * 100
                logger.info(f"  {field}: {count}/{len(parsed_articles)} ({rate:.1f}%)")
        
        return parsed_articles
        
    except Exception as e:
        logger.error(f"❌ Parsing test failed: {e}")
        return []


def show_sample_articles(articles, count=3):
    """Show detailed information for sample articles."""
    logger.info(f"\n🔍 Sample Articles (showing {min(count, len(articles))})")
    logger.info("-" * 50)
    
    for i, article in enumerate(articles[:count]):
        logger.info(f"\n--- Article {i+1} ---")
        logger.info(f"ID: {article.get('external_id', 'Unknown')}")
        logger.info(f"Title: {article.get('title', 'No title')}")
        logger.info(f"Author: {article.get('author', 'Unknown')}")
        logger.info(f"Category: {article.get('category', 'Unknown')}")
        logger.info(f"URL: {article.get('url', 'No URL')}")
        
        summary = article.get('summary')
        if summary:
            summary_preview = summary[:100] + "..." if len(summary) > 100 else summary
            logger.info(f"Summary: {summary_preview}")
        
        logger.info(f"Image URL: {article.get('image_url', 'No image')}")
        logger.info(f"Published: {article.get('published_at', 'Unknown')}")
        logger.info(f"Word Count: {article.get('word_count', 'Unknown')}")
        
        # Calculate quality score
        try:
            from src.collectors.tecmundo import TecmundoCollector
            collector = TecmundoCollector()
            quality = collector._calculate_article_quality(article)
            logger.info(f"Quality Score: {quality:.1f}/100")
        except:
            logger.info("Quality Score: Unable to calculate")


def test_full_parsing_workflow():
    """Test the complete parsing workflow."""
    logger.info("\n🔄 Full Parsing Workflow Test")
    logger.info("-" * 50)
    
    try:
        from src.collectors.tecmundo import TecmundoCollector
        
        collector = TecmundoCollector()
        
        # Fetch data
        url = collector.get_api_url()
        response = collector.http_client.get(url)
        data = response.json()
        
        # Test the full parse_response method
        articles = collector.parse_response(data)
        
        logger.info(f"✅ Full parsing workflow completed")
        logger.info(f"Articles parsed: {len(articles)}")
        
        if articles:
            # Show quality distribution
            quality_scores = []
            for article in articles:
                try:
                    quality = collector._calculate_article_quality(article)
                    quality_scores.append(quality)
                except:
                    quality_scores.append(0)
            
            if quality_scores:
                avg_quality = sum(quality_scores) / len(quality_scores)
                logger.info(f"Average quality score: {avg_quality:.1f}")
                logger.info(f"Quality range: {min(quality_scores):.1f} - {max(quality_scores):.1f}")
        
        collector.http_client.close()
        return articles
        
    except Exception as e:
        logger.error(f"❌ Full workflow test failed: {e}")
        return []


def main():
    """Main test function."""
    logger.info("🚀 Tecmundo API-Only Test Suite")
    logger.info("=" * 60)
    
    # Show configuration
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"API URL: {settings.api.tecmundo_full_url}")
    logger.info(f"Request timeout: {settings.api.request_timeout}s")
    logger.info(f"Max retries: {settings.api.max_retries}")
    
    try:
        # Test 1: API Connection
        success, data = test_api_connection()
        if not success:
            logger.error("❌ API connection failed - cannot continue")
            return False
        
        # Test 2: Response Structure Analysis
        posts = analyze_response_structure(data)
        
        # Test 3: Parsing Logic
        if posts:
            articles = test_parsing_logic(posts)
            
            # Test 4: Show samples
            if articles:
                show_sample_articles(articles)
                
                # Test 5: Full workflow
                logger.info("\n" + "=" * 60)
                workflow_articles = test_full_parsing_workflow()
                
                # Final summary
                logger.info("\n" + "=" * 60)
                logger.info("🎯 Test Summary")
                logger.info("-" * 30)
                logger.info(f"✅ API Connection: Working")
                logger.info(f"✅ Data Structure: {len(posts)} posts found")
                logger.info(f"✅ Parsing Logic: {len(articles)} articles parsed")
                logger.info(f"✅ Full Workflow: {len(workflow_articles)} articles")
                
                # Check minimum requirements
                if len(articles) >= 5:
                    logger.info("✅ Minimum article count met (≥5)")
                else:
                    logger.warning(f"⚠️  Low article count: {len(articles)}")
                
                success_rate = len(articles) / len(posts) * 100 if posts else 0
                if success_rate >= 80:
                    logger.info(f"✅ High parsing success rate: {success_rate:.1f}%")
                else:
                    logger.warning(f"⚠️  Low parsing success rate: {success_rate:.1f}%")
                
                logger.info("\n🎉 API collection system is working correctly!")
                logger.info("Ready to integrate with database when PostgreSQL is available.")
                
                return True
        
        logger.error("❌ No articles were successfully parsed")
        return False
        
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)