"""Main entry point for Termômetro de Tecnologia."""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.logger import get_logger
from src.utils.database import DatabaseManager
from src.collectors.tecmundo import TecmundoCollector
from config.settings import settings

logger = get_logger(__name__)


def test_database_connection():
    """Test database connection."""
    logger.info("Testing database connection...")
    
    if DatabaseManager.test_connection():
        logger.info("✓ Database connection successful")
        return True
    else:
        logger.error("✗ Database connection failed")
        return False


def initialize_database():
    """Initialize database tables."""
    logger.info("Initializing database...")
    
    try:
        DatabaseManager.init_database()
        logger.info("✓ Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        return False


def test_tecmundo_collector():
    """Test Tecmundo data collection with detailed metrics."""
    logger.info("Testing Tecmundo collector...")
    
    try:
        with TecmundoCollector() as collector:
            success = collector.collect_data()
            
            # Get detailed metrics
            metrics = collector.get_collection_metrics()
            
            if success and metrics:
                logger.info("✓ Tecmundo collection successful")
                logger.info(f"  Articles found: {metrics.articles_found}")
                logger.info(f"  Articles new: {metrics.articles_new}")
                logger.info(f"  Articles updated: {metrics.articles_updated}")
                logger.info(f"  Articles skipped: {metrics.articles_skipped}")
                logger.info(f"  Response time: {metrics.response_time_ms}ms")
                logger.info(f"  Duration: {metrics.duration_seconds():.2f}s")
                
                if metrics.errors:
                    logger.warning(f"  Errors encountered: {len(metrics.errors)}")
                    for error in metrics.errors[:3]:  # Show first 3 errors
                        logger.warning(f"    - {error}")
                
                return True
            else:
                logger.error("✗ Tecmundo collection failed")
                if metrics and metrics.errors:
                    for error in metrics.errors:
                        logger.error(f"  Error: {error}")
                return False
                
    except Exception as e:
        logger.error(f"✗ Tecmundo collector test failed: {e}")
        return False


def show_database_statistics():
    """Show database statistics after collection."""
    logger.info("Database Statistics:")
    
    try:
        with DatabaseManager.get_session() as session:
            from src.repositories.articles import ArticleRepository
            from src.repositories.sites import SiteRepository
            from src.repositories.snapshots import SnapshotRepository
            
            article_repo = ArticleRepository(session)
            site_repo = SiteRepository(session)
            snapshot_repo = SnapshotRepository(session)
            
            # Get site statistics
            tecmundo_stats = site_repo.get_site_statistics("tecmundo")
            if tecmundo_stats:
                logger.info(f"  Site: {tecmundo_stats['site_name']}")
                logger.info(f"  Status: {'Active' if tecmundo_stats['is_active'] else 'Inactive'}")
                logger.info(f"  Total articles: {tecmundo_stats['total_articles']}")
                logger.info(f"  Recent articles (7d): {tecmundo_stats['recent_articles']}")
                logger.info(f"  Success rate: {tecmundo_stats['success_rate']:.1f}%")
                logger.info(f"  Error count: {tecmundo_stats['error_count']}")
            
            # Get recent snapshots
            from datetime import datetime, timedelta
            recent_snapshots = session.query(
                snapshot_repo.model
            ).filter(
                snapshot_repo.model.timestamp >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            logger.info(f"  Recent snapshots (24h): {recent_snapshots}")
            
    except Exception as e:
        logger.error(f"Failed to show database statistics: {e}")


def validate_data_quality():
    """Validate the quality of collected data."""
    logger.info("Validating data quality...")
    
    try:
        with DatabaseManager.get_session() as session:
            from src.repositories.articles import ArticleRepository
            
            article_repo = ArticleRepository(session)
            
            # Get site ID for Tecmundo
            from src.repositories.sites import SiteRepository
            site_repo = SiteRepository(session)
            site = site_repo.get_by_site_id("tecmundo")
            
            if not site:
                logger.warning("No Tecmundo site found in database")
                return True
            
            # Get recent articles
            recent_articles = article_repo.get_recent_articles(site.id, hours=24)
            
            if not recent_articles:
                logger.warning("No recent articles found")
                return True
            
            # Analyze data quality
            total_articles = len(recent_articles)
            articles_with_author = sum(1 for a in recent_articles if a.author_id)
            articles_with_category = sum(1 for a in recent_articles if a.category_id)
            articles_with_summary = sum(1 for a in recent_articles if a.summary)
            articles_with_image = sum(1 for a in recent_articles if a.image_url)
            
            quality_scores = [a.quality_score for a in recent_articles if a.quality_score]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
            logger.info(f"  Total recent articles: {total_articles}")
            logger.info(f"  With author: {articles_with_author} ({articles_with_author/total_articles*100:.1f}%)")
            logger.info(f"  With category: {articles_with_category} ({articles_with_category/total_articles*100:.1f}%)")
            logger.info(f"  With summary: {articles_with_summary} ({articles_with_summary/total_articles*100:.1f}%)")
            logger.info(f"  With image: {articles_with_image} ({articles_with_image/total_articles*100:.1f}%)")
            logger.info(f"  Average quality score: {avg_quality:.1f}/100")
            
            # Show sample articles
            logger.info("  Sample articles:")
            for i, article in enumerate(recent_articles[:3]):
                author_name = article.author.name if article.author else "Unknown"
                category_name = article.category.name if article.category else "Unknown"
                logger.info(f"    {i+1}. {article.title[:60]}...")
                logger.info(f"       Author: {author_name}, Category: {category_name}")
                logger.info(f"       Quality: {article.quality_score:.1f}, URL: {article.url[:50]}...")
            
            return True
            
    except Exception as e:
        logger.error(f"Failed to validate data quality: {e}")
        return False


def main():
    """Main function to test the setup."""
    logger.info("=" * 60)
    logger.info("Termômetro de Tecnologia - Environment Setup Test")
    logger.info("=" * 60)
    
    # Show configuration
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database URL: {settings.database.url}")
    logger.info(f"Tecmundo API: {settings.api.tecmundo_full_url}")
    logger.info(f"Collection Interval: {settings.collection.interval_hours} hours")
    logger.info("-" * 60)
    
    # Test steps
    tests = [
        ("Database Connection", test_database_connection),
        ("Database Initialization", initialize_database),
        ("Tecmundo Collector", test_tecmundo_collector),
        ("Database Statistics", lambda: (show_database_statistics(), True)[1]),
        ("Data Quality Validation", validate_data_quality),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"Running: {test_name}")
        try:
            if test_func():
                passed += 1
            else:
                logger.error(f"Test failed: {test_name}")
        except Exception as e:
            logger.error(f"Test error: {test_name} - {e}")
        
        logger.info("-" * 60)
    
    # Summary
    logger.info("=" * 60)
    logger.info(f"Setup Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Environment is ready for development.")
        sys.exit(0)
    else:
        logger.error("❌ Some tests failed. Please check the logs above.")
        sys.exit(1)


if __name__ == "__main__":
    main()