#!/usr/bin/env python3
"""
Pre-deployment check script - validates that all requirements are met before Railway deploy.
Run this locally before pushing to Railway to catch issues early.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


def check_file_exists(file_path, description):
    """Check if a file exists."""
    if Path(file_path).exists():
        logger.info(f"✓ {description}: {file_path}")
        return True
    else:
        logger.error(f"✗ {description} missing: {file_path}")
        return False


def check_dependencies():
    """Check if all required dependencies are installed."""
    logger.info("Checking Python dependencies...")
    
    required_packages = [
        ("requests", "HTTP requests"),
        ("sqlalchemy", "Database ORM"),
        ("psycopg2", "PostgreSQL adapter"),
        ("pandas", "Data processing"),
        ("pydantic", "Data validation"),
        ("pydantic_settings", "Settings management"),
        ("loguru", "Logging"),
        ("alembic", "Database migrations"),
        ("fastapi", "Web framework"),
        ("uvicorn", "ASGI server"),
    ]
    
    missing_packages = []
    
    for package, description in required_packages:
        try:
            if package == "psycopg2":
                import psycopg2  # Try the actual package name
            else:
                __import__(package)
            logger.info(f"✓ {description}: {package}")
        except ImportError:
            logger.error(f"✗ {description} missing: {package}")
            missing_packages.append(package)
    
    return len(missing_packages) == 0


def check_configuration():
    """Check configuration files and settings."""
    logger.info("Checking configuration...")
    
    try:
        from config.settings import settings
        
        # Check that settings load properly
        logger.info(f"✓ Settings loaded successfully")
        logger.info(f"  Environment: {settings.environment}")
        logger.info(f"  Database configured: {bool(settings.database.url or (settings.database.host and settings.database.database))}")
        logger.info(f"  API URL: {settings.api.tecmundo_full_url}")
        logger.info(f"  Collection interval: {settings.collection.interval_hours}h")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Configuration check failed: {e}")
        return False


def check_database_models():
    """Check that database models can be imported."""
    logger.info("Checking database models...")
    
    try:
        from src.models.sites import Site
        from src.models.articles import Article
        from src.models.authors import Author
        from src.models.categories import Category
        from src.models.snapshots import Snapshot
        
        logger.info("✓ All database models imported successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Database model import failed: {e}")
        return False


def check_collectors():
    """Check that data collectors can be imported."""
    logger.info("Checking data collectors...")
    
    try:
        from src.collectors.tecmundo import TecmundoCollector
        
        logger.info("✓ TecmundoCollector imported successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Collector import failed: {e}")
        return False


def check_repositories():
    """Check that repositories can be imported."""
    logger.info("Checking repositories...")
    
    try:
        from src.repositories.sites import SiteRepository
        from src.repositories.articles import ArticleRepository
        from src.repositories.authors import AuthorRepository
        from src.repositories.categories import CategoryRepository
        from src.repositories.snapshots import SnapshotRepository
        
        logger.info("✓ All repositories imported successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Repository import failed: {e}")
        return False


def check_deployment_files():
    """Check that all deployment files are present."""
    logger.info("Checking deployment files...")
    
    deployment_files = [
        ("railway.toml", "Railway configuration"),
        ("Procfile", "Process definitions"),
        ("nixpacks.toml", "Build configuration"),
        ("app.py", "Web service"),
        ("worker.py", "Worker service"),
        ("scripts/deploy.py", "Deployment script"),
        ("scripts/railway_setup.py", "Railway setup script"),
        ("scripts/monitor.py", "Monitoring script"),
        ("requirements.txt", "Python dependencies"),
        (".env.railway", "Environment template"),
        ("RAILWAY_DEPLOY.md", "Deployment documentation"),
    ]
    
    all_present = True
    for file_path, description in deployment_files:
        if not check_file_exists(file_path, description):
            all_present = False
    
    return all_present


def check_alembic_setup():
    """Check Alembic migration setup."""
    logger.info("Checking Alembic setup...")
    
    try:
        # Check alembic.ini exists
        if not Path("alembic.ini").exists():
            logger.error("✗ alembic.ini not found")
            return False
        
        # Check migrations directory
        if not Path("migrations").exists():
            logger.error("✗ migrations directory not found")
            return False
        
        # Check if we can import alembic config
        from alembic.config import Config
        config = Config("alembic.ini")
        
        logger.info("✓ Alembic configuration valid")
        return True
        
    except Exception as e:
        logger.error(f"✗ Alembic setup check failed: {e}")
        return False


def check_api_connectivity():
    """Check if we can reach the Tecmundo API."""
    logger.info("Checking API connectivity...")
    
    try:
        import requests
        from config.settings import settings
        
        response = requests.get(
            settings.api.tecmundo_full_url,
            timeout=10,
            headers={"User-Agent": "TecData-PreDeploy/1.0"}
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                posts_count = len(data.get("posts", []))
                logger.info(f"✓ API reachable - {posts_count} posts available")
                return True
            except Exception:
                logger.warning("⚠ API reachable but response format unexpected")
                return True
        else:
            logger.warning(f"⚠ API returned status {response.status_code}")
            return True  # Not critical for pre-deploy
            
    except Exception as e:
        logger.warning(f"⚠ API connectivity check failed: {e} (not critical for deploy)")
        return True  # Not critical for pre-deploy


def main():
    """Main pre-deployment check."""
    logger.info("=" * 60)
    logger.info("Pre-Deployment Check - Termômetro de Tecnologia")
    logger.info("=" * 60)
    
    # All checks to run
    checks = [
        ("Dependencies", check_dependencies),
        ("Configuration", check_configuration),
        ("Database Models", check_database_models),
        ("Data Collectors", check_collectors),
        ("Repositories", check_repositories),
        ("Deployment Files", check_deployment_files),
        ("Alembic Setup", check_alembic_setup),
        ("API Connectivity", check_api_connectivity),
    ]
    
    passed = 0
    total = len(checks)
    critical_failed = False
    
    for check_name, check_func in checks:
        logger.info(f"\nRunning check: {check_name}")
        logger.info("-" * 40)
        
        try:
            if check_func():
                passed += 1
            else:
                if check_name in ["Dependencies", "Configuration", "Deployment Files", "Alembic Setup"]:
                    critical_failed = True
        except Exception as e:
            logger.error(f"Check '{check_name}' crashed: {e}")
            if check_name in ["Dependencies", "Configuration", "Deployment Files"]:
                critical_failed = True
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("PRE-DEPLOYMENT CHECK SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Checks passed: {passed}/{total}")
    
    if passed == total:
        logger.info("🎉 All checks passed! Ready for Railway deployment.")
        logger.info("\nNext steps:")
        logger.info("1. Commit and push all changes to Git")
        logger.info("2. Create Railway project and connect repository")
        logger.info("3. Add PostgreSQL database service")
        logger.info("4. Configure environment variables")
        logger.info("5. Deploy and monitor logs")
        sys.exit(0)
    elif critical_failed:
        logger.error("❌ Critical checks failed! Fix issues before deploying.")
        logger.error("\nCritical issues must be resolved before Railway deployment.")
        sys.exit(1)
    else:
        logger.warning("⚠ Some non-critical checks failed. Review warnings above.")
        logger.warning("You can proceed with deployment but monitor closely.")
        sys.exit(0)


if __name__ == "__main__":
    main()