#!/usr/bin/env python3
"""
Railway setup script - initializes the database and creates initial data.
Run this script after first deployment to set up the system.
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.utils.logger import get_logger
from src.utils.database import DatabaseManager
from config.settings import settings

# Initialize logger
logger = get_logger(__name__)


def setup_railway_database():
    """Set up database for Railway deployment."""
    logger.info("Setting up Railway database...")
    
    try:
        # Test connection
        if not DatabaseManager.test_connection():
            logger.error("Database connection failed")
            return False
        
        logger.info("✓ Database connection successful")
        
        # Initialize database
        DatabaseManager.init_database()
        logger.info("✓ Database tables created/updated")
        
        # Create initial site record for Tecmundo
        with DatabaseManager.get_session() as session:
            from src.repositories.sites import SiteRepository
            
            site_repo = SiteRepository(session)
            
            # Check if Tecmundo site exists
            existing_site = site_repo.get_by_site_id("tecmundo")
            
            if not existing_site:
                # Create Tecmundo site
                from src.models.sites import Site
                
                tecmundo_site = Site(
                    site_id="tecmundo",
                    name="Tecmundo",
                    base_url="https://www.tecmundo.com.br",
                    api_endpoint="/api/posts?endpoint=home-author",
                    is_active=True,
                    collection_interval_hours=settings.collection.interval_hours
                )
                
                session.add(tecmundo_site)
                session.commit()
                
                logger.info("✓ Tecmundo site created")
            else:
                logger.info("✓ Tecmundo site already exists")
        
        logger.info("✓ Railway database setup completed")
        return True
        
    except Exception as e:
        logger.error(f"Railway database setup failed: {e}")
        return False


def run_test_collection():
    """Run a test collection to verify everything is working."""
    logger.info("Running test collection...")
    
    try:
        from src.collectors.tecmundo import TecmundoCollector
        
        with TecmundoCollector() as collector:
            success = collector.collect_data()
            metrics = collector.get_collection_metrics()
            
            if success and metrics:
                logger.info("✓ Test collection successful")
                logger.info(f"  Articles found: {metrics.articles_found}")
                logger.info(f"  Articles new: {metrics.articles_new}")
                logger.info(f"  Response time: {metrics.response_time_ms}ms")
                return True
            else:
                logger.warning("Test collection completed with issues")
                if metrics and metrics.errors:
                    for error in metrics.errors:
                        logger.warning(f"  Warning: {error}")
                return False
                
    except Exception as e:
        logger.error(f"Test collection failed: {e}")
        return False


def main():
    """Main setup function."""
    logger.info("=" * 60)
    logger.info("Railway Setup Script")
    logger.info("=" * 60)
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database URL configured: {bool(settings.database.url)}")
    logger.info("-" * 60)
    
    # Setup steps
    steps = [
        ("Database Setup", setup_railway_database),
        ("Test Collection", run_test_collection),
    ]
    
    passed = 0
    total = len(steps)
    
    for step_name, step_func in steps:
        logger.info(f"Running: {step_name}")
        
        try:
            if step_func():
                passed += 1
                logger.info(f"✓ {step_name} completed successfully")
            else:
                logger.warning(f"⚠ {step_name} completed with warnings")
        except Exception as e:
            logger.error(f"✗ {step_name} failed: {e}")
        
        logger.info("-" * 60)
    
    logger.info("=" * 60)
    logger.info(f"Setup Results: {passed}/{total} steps completed successfully")
    
    if passed == total:
        logger.info("🎉 Railway setup completed successfully!")
        logger.info("Your Termômetro de Tecnologia system is ready to collect data.")
    else:
        logger.warning("⚠ Setup completed with some warnings - check logs above")
    
    logger.info("=" * 60)


if __name__ == "__main__":
    main()