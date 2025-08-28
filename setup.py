#!/usr/bin/env python3
"""
Setup script for Termômetro de Tecnologia project.
Can run with or without Docker depending on availability.
"""

import sys
import subprocess
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.logger import get_logger

logger = get_logger(__name__)


def check_docker():
    """Check if Docker is running."""
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def start_docker_services():
    """Start Docker Compose services."""
    try:
        logger.info("Starting Docker services...")
        result = subprocess.run(
            ["docker-compose", "up", "-d"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            logger.info("✓ Docker services started successfully")
            return True
        else:
            logger.error(f"✗ Docker services failed: {result.stderr}")
            return False
            
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.error(f"✗ Docker command failed: {e}")
        return False


def test_database_with_docker():
    """Test database connection when Docker is available."""
    try:
        from src.utils.database import DatabaseManager
        
        logger.info("Testing database connection...")
        if DatabaseManager.test_connection():
            logger.info("✓ Database connection successful")
            
            # Initialize database tables
            logger.info("Initializing database tables...")
            DatabaseManager.init_database()
            logger.info("✓ Database tables initialized")
            
            return True
        else:
            logger.error("✗ Database connection failed")
            return False
            
    except Exception as e:
        logger.error(f"✗ Database test failed: {e}")
        return False


def test_api_collection():
    """Test API data collection."""
    try:
        from src.collectors.tecmundo import TecmundoCollector
        
        logger.info("Testing Tecmundo data collection...")
        
        with TecmundoCollector() as collector:
            # Get API URL and test the endpoint
            url = collector.get_api_url()
            logger.info(f"Testing API endpoint: {url}")
            
            # Make a request to get data
            response = collector.http_client.get(url)
            data = response.json()
            
            # Parse the response
            articles = collector.parse_response(data)
            
            logger.info(f"✓ Successfully parsed {len(articles)} articles")
            
            if articles:
                # Show sample article
                sample = articles[0]
                logger.info(f"Sample article: {sample.get('title', 'No title')[:50]}...")
            
            return True
            
    except Exception as e:
        logger.error(f"✗ API collection test failed: {e}")
        return False


def main():
    """Main setup function."""
    logger.info("=" * 60)
    logger.info("Termômetro de Tecnologia - Project Setup")
    logger.info("=" * 60)
    
    # Check Docker availability
    docker_available = check_docker()
    logger.info(f"Docker available: {'Yes' if docker_available else 'No'}")
    
    success = True
    
    # Test 1: Basic API functionality (no database required)
    logger.info("\n1. Testing API Collection (without database)")
    logger.info("-" * 40)
    if not test_api_collection():
        success = False
    
    # Test 2: Database functionality (only if Docker is available)
    if docker_available:
        logger.info("\n2. Testing Database Functionality")
        logger.info("-" * 40)
        
        # Start Docker services
        if start_docker_services():
            import time
            logger.info("Waiting 10 seconds for database to be ready...")
            time.sleep(10)
            
            if not test_database_with_docker():
                success = False
        else:
            logger.warning("Docker services failed to start, skipping database tests")
    else:
        logger.info("\n2. Docker not available - skipping database tests")
        logger.info("-" * 40)
        logger.info("To enable database functionality:")
        logger.info("1. Install Docker Desktop")
        logger.info("2. Start Docker")
        logger.info("3. Run: docker-compose up -d")
        logger.info("4. Run this setup script again")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("SETUP SUMMARY")
    logger.info("=" * 60)
    
    if success:
        logger.info("🎉 Project setup completed successfully!")
        logger.info("\nNext Steps:")
        logger.info("1. Review the API collection results above")
        if docker_available:
            logger.info("2. Access Adminer at http://localhost:8080 to view database")
            logger.info("3. Run: python main.py (for full database testing)")
        else:
            logger.info("2. Set up Docker for database functionality")
        logger.info("4. Start developing your data collection pipeline")
    else:
        logger.error("❌ Setup completed with some issues")
        logger.error("Please check the logs above for details")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)