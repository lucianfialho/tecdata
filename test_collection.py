#!/usr/bin/env python3
"""
Dedicated script for testing and monitoring Tecmundo collection.
This script provides detailed analysis of collection performance and data quality.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.logger import get_logger
from src.utils.database import DatabaseManager
from src.collectors.tecmundo import TecmundoCollector
from src.repositories.articles import ArticleRepository
from src.repositories.sites import SiteRepository
from src.repositories.snapshots import SnapshotRepository
from src.repositories.collection_stats import CollectionStatsRepository
from config.settings import settings

logger = get_logger(__name__)


def test_api_response():
    """Test raw API response structure."""
    logger.info("=" * 60)
    logger.info("Testing Tecmundo API Response Structure")
    logger.info("=" * 60)
    
    try:
        collector = TecmundoCollector()
        
        # Test HTTP client directly
        url = collector.get_api_url()
        logger.info(f"API URL: {url}")
        
        response = collector.http_client.get(url)
        logger.info(f"Response Status: {response.status_code}")
        logger.info(f"Response Headers: {dict(response.headers)}")
        
        # Parse JSON
        data = response.json()
        logger.info(f"Response Type: {type(data)}")
        logger.info(f"Response Size: {len(str(data))} characters")
        
        if isinstance(data, dict):
            logger.info(f"Top-level keys: {list(data.keys())}")
            
            # Look for articles/posts
            posts = collector._extract_articles_list(data)
            logger.info(f"Articles found: {len(posts)}")
            
            if posts:
                sample_post = posts[0]
                logger.info("Sample post structure:")
                for key, value in sample_post.items():
                    value_type = type(value).__name__
                    value_preview = str(value)[:100] if value else "None"
                    logger.info(f"  {key}: ({value_type}) {value_preview}")
        
        collector.http_client.close()
        return True
        
    except Exception as e:
        logger.error(f"API test failed: {e}")
        return False


def test_parsing_logic():
    """Test article parsing logic with real data."""
    logger.info("=" * 60)
    logger.info("Testing Article Parsing Logic")
    logger.info("=" * 60)
    
    try:
        collector = TecmundoCollector()
        
        # Fetch real data
        url = collector.get_api_url()
        response = collector.http_client.get(url)
        data = response.json()
        
        # Test parsing
        articles = collector.parse_response(data)
        
        logger.info(f"Total articles parsed: {len(articles)}")
        
        if articles:
            # Analyze parsing results
            fields_analysis = {
                'external_id': 0,
                'title': 0,
                'author': 0,
                'category': 0,
                'url': 0,
                'summary': 0,
                'image_url': 0,
                'published_at': 0,
                'word_count': 0
            }
            
            for article in articles:
                for field in fields_analysis:
                    if article.get(field):
                        fields_analysis[field] += 1
            
            logger.info("Field extraction success rates:")
            for field, count in fields_analysis.items():
                percentage = (count / len(articles)) * 100
                logger.info(f"  {field}: {count}/{len(articles)} ({percentage:.1f}%)")
            
            # Show sample articles
            logger.info("\nSample parsed articles:")
            for i, article in enumerate(articles[:3]):
                logger.info(f"\nArticle {i+1}:")
                logger.info(f"  ID: {article.get('external_id')}")
                logger.info(f"  Title: {article.get('title', '')[:80]}...")
                logger.info(f"  Author: {article.get('author', 'Unknown')}")
                logger.info(f"  Category: {article.get('category', 'Unknown')}")
                logger.info(f"  URL: {article.get('url', 'No URL')[:60]}...")
                logger.info(f"  Quality Score: {collector._calculate_article_quality(article):.1f}")
        
        collector.http_client.close()
        return True
        
    except Exception as e:
        logger.error(f"Parsing test failed: {e}")
        return False


def run_full_collection_test():
    """Run a full collection test with detailed monitoring."""
    logger.info("=" * 60)
    logger.info("Running Full Collection Test")
    logger.info("=" * 60)
    
    try:
        # Initialize database
        DatabaseManager.init_database()
        
        # Run collection
        with TecmundoCollector() as collector:
            success = collector.collect_data()
            metrics = collector.get_collection_metrics()
            
            if success and metrics:
                logger.info("✅ Collection completed successfully!")
                
                # Show detailed metrics
                logger.info("\n📊 Collection Metrics:")
                logger.info(f"  Duration: {metrics.duration_seconds():.2f} seconds")
                logger.info(f"  Response Time: {metrics.response_time_ms}ms")
                logger.info(f"  Articles Found: {metrics.articles_found}")
                logger.info(f"  Articles New: {metrics.articles_new}")
                logger.info(f"  Articles Updated: {metrics.articles_updated}")
                logger.info(f"  Articles Skipped: {metrics.articles_skipped}")
                
                if metrics.errors:
                    logger.warning(f"  Errors: {len(metrics.errors)}")
                    for error in metrics.errors:
                        logger.warning(f"    - {error}")
                
                # Validate minimum success criteria
                if metrics.articles_found >= 5:
                    logger.info("✅ Minimum article count met")
                else:
                    logger.warning(f"⚠️  Low article count: {metrics.articles_found}")
                
                if metrics.articles_new > 0 or metrics.articles_updated > 0:
                    logger.info("✅ Articles were processed successfully")
                else:
                    logger.warning("⚠️  No articles were processed")
                
                return True
            else:
                logger.error("❌ Collection failed")
                if metrics and metrics.errors:
                    for error in metrics.errors:
                        logger.error(f"  Error: {error}")
                return False
                
    except Exception as e:
        logger.error(f"Full collection test failed: {e}")
        return False


def analyze_database_state():
    """Analyze current database state and data quality."""
    logger.info("=" * 60)
    logger.info("Database State Analysis")
    logger.info("=" * 60)
    
    try:
        with DatabaseManager.get_session() as session:
            site_repo = SiteRepository(session)
            article_repo = ArticleRepository(session)
            snapshot_repo = SnapshotRepository(session)
            stats_repo = CollectionStatsRepository(session)
            
            # Site information
            site = site_repo.get_by_site_id("tecmundo")
            if site:
                logger.info(f"📍 Site: {site.name}")
                logger.info(f"  Status: {'Active' if site.is_active else 'Inactive'}")
                logger.info(f"  Error Count: {site.collection_error_count}")
                logger.info(f"  Last Successful: {site.last_successful_collection}")
                
                # Article statistics
                article_stats = article_repo.get_article_statistics(site.id)
                logger.info(f"\n📄 Articles:")
                logger.info(f"  Total: {article_stats.get('total_articles', 0)}")
                logger.info(f"  Active: {article_stats.get('active_articles', 0)}")
                logger.info(f"  Recent (7d): {article_stats.get('recent_articles_7d', 0)}")
                logger.info(f"  Avg Quality: {article_stats.get('avg_quality_score', 0)}")
                logger.info(f"  Duplicate Rate: {article_stats.get('duplicate_rate', 0):.1f}%")
                logger.info(f"  Unique Authors: {article_stats.get('unique_authors', 0)}")
                logger.info(f"  Unique Categories: {article_stats.get('unique_categories', 0)}")
                
                # Recent snapshots
                recent_snapshots = session.query(snapshot_repo.model).filter(
                    snapshot_repo.model.site_id == site.site_id,
                    snapshot_repo.model.timestamp >= datetime.utcnow() - timedelta(days=1)
                ).count()
                
                logger.info(f"\n📸 Snapshots (24h): {recent_snapshots}")
                
                # Collection statistics
                recent_stats = session.query(stats_repo.model).filter(
                    stats_repo.model.site_id == site.site_id,
                    stats_repo.model.collection_date >= (datetime.utcnow() - timedelta(days=7)).date()
                ).all()
                
                if recent_stats:
                    logger.info(f"\n📈 Recent Collections (7d): {len(recent_stats)}")
                    total_found = sum(s.articles_found for s in recent_stats)
                    total_new = sum(s.articles_new for s in recent_stats)
                    total_updated = sum(s.articles_updated for s in recent_stats)
                    avg_response_time = sum(s.response_time_ms for s in recent_stats) / len(recent_stats)
                    
                    logger.info(f"  Articles Found: {total_found}")
                    logger.info(f"  Articles New: {total_new}")
                    logger.info(f"  Articles Updated: {total_updated}")
                    logger.info(f"  Avg Response Time: {avg_response_time:.0f}ms")
                
                # Sample recent articles
                recent_articles = article_repo.get_recent_articles(site.id, hours=24, limit=5)
                if recent_articles:
                    logger.info(f"\n🔍 Sample Recent Articles:")
                    for i, article in enumerate(recent_articles, 1):
                        author = article.author.name if article.author else "Unknown"
                        category = article.category.name if article.category else "Unknown"
                        logger.info(f"  {i}. {article.title[:60]}...")
                        logger.info(f"     Author: {author}, Category: {category}")
                        logger.info(f"     Quality: {article.quality_score:.1f}, First seen: {article.first_seen}")
            else:
                logger.warning("❌ No Tecmundo site found in database")
        
        return True
        
    except Exception as e:
        logger.error(f"Database analysis failed: {e}")
        return False


def run_continuous_monitoring(minutes: int = 5):
    """Run continuous collection monitoring for specified minutes."""
    logger.info("=" * 60)
    logger.info(f"Starting Continuous Monitoring ({minutes} minutes)")
    logger.info("=" * 60)
    
    import time
    
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=minutes)
    
    collection_count = 0
    successful_collections = 0
    
    try:
        while datetime.now() < end_time:
            collection_count += 1
            logger.info(f"\n🔄 Collection Run #{collection_count}")
            
            try:
                with TecmundoCollector() as collector:
                    success = collector.collect_data()
                    metrics = collector.get_collection_metrics()
                    
                    if success and metrics:
                        successful_collections += 1
                        logger.info(f"✅ Success - New: {metrics.articles_new}, Updated: {metrics.articles_updated}")
                    else:
                        logger.error(f"❌ Failed - Errors: {len(metrics.errors) if metrics else 'Unknown'}")
                
                # Wait before next collection (respect rate limits)
                wait_time = settings.collection.min_request_interval * 2  # Double the minimum interval
                logger.info(f"⏰ Waiting {wait_time}s before next collection...")
                time.sleep(wait_time)
                
            except KeyboardInterrupt:
                logger.info("\n⏹️  Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Collection error: {e}")
        
        # Summary
        success_rate = (successful_collections / collection_count) * 100 if collection_count > 0 else 0
        logger.info(f"\n📊 Monitoring Summary:")
        logger.info(f"  Total Collections: {collection_count}")
        logger.info(f"  Successful: {successful_collections}")
        logger.info(f"  Success Rate: {success_rate:.1f}%")
        
        return success_rate > 80  # Consider success if >80% collections succeeded
        
    except Exception as e:
        logger.error(f"Continuous monitoring failed: {e}")
        return False


def main():
    """Main function with comprehensive testing options."""
    if len(sys.argv) < 2:
        logger.info("Usage: python test_collection.py <test_type>")
        logger.info("Available tests:")
        logger.info("  api          - Test API response structure")
        logger.info("  parse        - Test parsing logic")
        logger.info("  collect      - Run full collection test")
        logger.info("  analyze      - Analyze database state")
        logger.info("  monitor <minutes> - Run continuous monitoring")
        logger.info("  all          - Run all tests")
        sys.exit(1)
    
    test_type = sys.argv[1].lower()
    
    # Configuration info
    logger.info("🔧 Configuration:")
    logger.info(f"  Environment: {settings.environment}")
    logger.info(f"  Database: {settings.database.host}:{settings.database.port}/{settings.database.database}")
    logger.info(f"  API URL: {settings.api.tecmundo_full_url}")
    logger.info(f"  Collection Interval: {settings.collection.interval_hours}h")
    logger.info("")
    
    tests_passed = 0
    total_tests = 0
    
    if test_type in ["api", "all"]:
        total_tests += 1
        if test_api_response():
            tests_passed += 1
    
    if test_type in ["parse", "all"]:
        total_tests += 1
        if test_parsing_logic():
            tests_passed += 1
    
    if test_type in ["collect", "all"]:
        total_tests += 1
        if run_full_collection_test():
            tests_passed += 1
    
    if test_type in ["analyze", "all"]:
        total_tests += 1
        if analyze_database_state():
            tests_passed += 1
    
    if test_type == "monitor":
        minutes = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        total_tests += 1
        if run_continuous_monitoring(minutes):
            tests_passed += 1
    
    # Summary
    if total_tests > 0:
        logger.info("=" * 60)
        logger.info(f"🎯 Test Results: {tests_passed}/{total_tests} passed")
        
        if tests_passed == total_tests:
            logger.info("🎉 All tests passed! Collection system is working properly.")
            sys.exit(0)
        else:
            logger.error("❌ Some tests failed. Check the logs above for details.")
            sys.exit(1)


if __name__ == "__main__":
    main()