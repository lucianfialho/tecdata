#!/usr/bin/env python3
"""
Deployment script for Railway - handles database migrations and initialization.
This script runs during the 'release' phase of Railway deployment.
"""

import sys
import os
import time
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.utils.logger import get_logger
from src.utils.database import DatabaseManager
from config.settings import settings

# Initialize logger
logger = get_logger(__name__)


def wait_for_database(max_attempts=30, delay=5):
    """Wait for database to be ready."""
    logger.info("Waiting for database to be ready...")
    
    for attempt in range(max_attempts):
        try:
            if DatabaseManager.test_connection():
                logger.info("✓ Database is ready")
                return True
        except Exception as e:
            logger.info(f"Database not ready (attempt {attempt + 1}/{max_attempts}): {e}")
        
        if attempt < max_attempts - 1:
            time.sleep(delay)
    
    logger.error("✗ Database failed to become ready")
    return False


def run_migrations():
    """Run Alembic database migrations."""
    logger.info("Running database migrations...")
    
    try:
        # Import alembic
        from alembic.config import Config
        from alembic import command
        
        # Set up alembic config
        alembic_cfg = Config("alembic.ini")
        
        # Set the database URL for migrations
        alembic_cfg.set_main_option("sqlalchemy.url", settings.database.url)
        
        # Run migrations to latest
        command.upgrade(alembic_cfg, "head")
        
        logger.info("✓ Database migrations completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Database migrations failed: {e}")
        return False


def initialize_database():
    """Initialize database with required data."""
    logger.info("Initializing database...")
    
    try:
        DatabaseManager.init_database()
        logger.info("✓ Database initialization completed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        return False


def verify_deployment():
    """Verify deployment is working correctly."""
    logger.info("Verifying deployment...")
    
    try:
        # Test database connection
        if not DatabaseManager.test_connection():
            logger.error("✗ Database connection test failed")
            return False
        
        # Test that we can query basic tables
        with DatabaseManager.get_session() as session:
            from src.repositories.sites import SiteRepository
            
            site_repo = SiteRepository(session)
            sites = site_repo.get_all()
            
            logger.info(f"✓ Found {len(sites)} sites in database")
            
            # Ensure Tecmundo site exists
            tecmundo_site = site_repo.get_by_site_id("tecmundo")
            if not tecmundo_site:
                logger.warning("Tecmundo site not found - this might be expected for a fresh deployment")
            else:
                logger.info("✓ Tecmundo site found in database")
        
        logger.info("✓ Deployment verification successful")
        return True
        
    except Exception as e:
        logger.error(f"✗ Deployment verification failed: {e}")
        return False


def main():
    """Main deployment function."""
    logger.info("=" * 60)
    logger.info("Railway Deployment Script")
    logger.info("=" * 60)
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database URL configured: {bool(settings.database.url)}")
    logger.info("-" * 60)
    
    # Check environment variables
    required_vars = ["DATABASE_URL"]
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)
    
    # Deployment steps
    steps = [
        ("Wait for Database", lambda: wait_for_database()),
        ("Run Migrations", run_migrations),
        ("Initialize Database", initialize_database),
        ("Verify Deployment", verify_deployment),
    ]
    
    logger.info("Starting deployment process...")
    
    for step_name, step_func in steps:
        logger.info(f"Step: {step_name}")
        
        try:
            if not step_func():
                logger.error(f"Deployment failed at step: {step_name}")
                sys.exit(1)
        except Exception as e:
            logger.error(f"Deployment step '{step_name}' crashed: {e}")
            sys.exit(1)
        
        logger.info(f"✓ {step_name} completed")
        logger.info("-" * 60)
    
    logger.info("🎉 Deployment completed successfully!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()