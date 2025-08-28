#!/usr/bin/env python3
"""Database initialization script for Termômetro de Tecnologia.

This script:
1. Creates the database schema using Alembic migrations
2. Runs initial seed data
3. Validates the setup

Usage:
    python scripts/init_db.py [--reset] [--seed-only]
    
Options:
    --reset     Drop all tables and recreate from scratch
    --seed-only Only run seed data, don't run migrations
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.base import engine, SessionLocal, Base
from src.models import *  # Import all models to register them
from src.repositories import *
from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


def drop_all_tables():
    """Drop all tables in the database."""
    logger.info("Dropping all tables...")
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("✓ All tables dropped successfully")
    except Exception as e:
        logger.error(f"✗ Error dropping tables: {e}")
        raise


def create_all_tables():
    """Create all tables using SQLAlchemy metadata."""
    logger.info("Creating all tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✓ All tables created successfully")
    except Exception as e:
        logger.error(f"✗ Error creating tables: {e}")
        raise


def run_alembic_migrations():
    """Run Alembic migrations to create/update database schema."""
    logger.info("Running Alembic migrations...")
    try:
        import subprocess
        result = subprocess.run([
            'alembic', 'upgrade', 'head'
        ], cwd=project_root, capture_output=True, text=True, check=True)
        logger.info("✓ Migrations completed successfully")
        if result.stdout:
            logger.debug(f"Migration output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ Error running migrations: {e}")
        if e.stderr:
            logger.error(f"Migration error: {e.stderr}")
        raise
    except FileNotFoundError:
        logger.warning("Alembic not found, falling back to SQLAlchemy table creation")
        create_all_tables()


def seed_initial_data():
    """Insert initial seed data."""
    logger.info("Seeding initial data...")
    session = SessionLocal()
    
    try:
        # Create site repository
        site_repo = SiteRepository(session)
        
        # Check if Tecmundo site already exists
        existing_site = site_repo.get_by_site_id('tecmundo')
        if existing_site:
            logger.info("✓ Tecmundo site already exists, skipping seed")
            return
        
        # Create Tecmundo site
        tecmundo_site = site_repo.create_site(
            name="Tecmundo",
            site_id="tecmundo",
            base_url="https://www.tecmundo.com.br",
            api_endpoints={
                "home_author": "/api/posts?endpoint=home-author",
                "categories": "/api/categories", 
                "authors": "/api/authors"
            },
            rate_limit_per_hour=60,
            request_timeout_ms=30000,
            retry_count=3,
            retry_delay_ms=1000,
            requires_auth=False,
            description="Portal brasileiro de tecnologia com notícias, reviews e análises",
            category="tech_news",
            country="BR",
            language="pt-BR"
        )
        
        session.commit()
        logger.info(f"✓ Created Tecmundo site with ID: {tecmundo_site.id}")
        
        # Create some default categories for Tecmundo
        category_repo = CategoryRepository(session)
        
        default_categories = [
            {"name": "tecnologia", "display_name": "Tecnologia", "description": "Notícias gerais de tecnologia"},
            {"name": "smartphones", "display_name": "Smartphones", "description": "Notícias sobre smartphones e dispositivos móveis"},
            {"name": "games", "display_name": "Games", "description": "Notícias sobre jogos e gaming"},
            {"name": "ciencia", "display_name": "Ciência", "description": "Notícias sobre ciência e descobertas"},
            {"name": "internet", "display_name": "Internet", "description": "Notícias sobre internet e redes sociais"},
            {"name": "gadgets", "display_name": "Gadgets", "description": "Reviews e notícias sobre gadgets"},
        ]
        
        for cat_data in default_categories:
            category = category_repo.get_or_create_by_name_and_site(
                name=cat_data["name"],
                site_id=tecmundo_site.id,
                display_name=cat_data["display_name"],
                description=cat_data["description"],
                sort_order=len(default_categories)
            )
            logger.debug(f"✓ Created/found category: {category.name}")
        
        session.commit()
        logger.info(f"✓ Created {len(default_categories)} default categories")
        
    except Exception as e:
        session.rollback()
        logger.error(f"✗ Error seeding data: {e}")
        raise
    finally:
        session.close()


def validate_setup():
    """Validate that the database setup is correct."""
    logger.info("Validating database setup...")
    session = SessionLocal()
    
    try:
        # Test basic connectivity
        site_repo = SiteRepository(session)
        sites = site_repo.get_all(limit=10)
        logger.info(f"✓ Database connectivity OK, found {len(sites)} sites")
        
        # Test repositories
        snapshot_repo = SnapshotRepository(session)
        article_repo = ArticleRepository(session) 
        author_repo = AuthorRepository(session)
        category_repo = CategoryRepository(session)
        stats_repo = CollectionStatsRepository(session)
        
        # Test basic queries
        categories = category_repo.get_all(limit=10)
        logger.info(f"✓ Found {len(categories)} categories")
        
        # Test functions (if PostgreSQL)
        if "postgresql" in settings.database.url:
            try:
                result = session.execute("SELECT get_article_stats()").fetchall()
                logger.info("✓ Database functions working")
            except Exception as e:
                logger.warning(f"Database functions may not be available: {e}")
        
        logger.info("✓ Database validation completed successfully")
        
    except Exception as e:
        logger.error(f"✗ Database validation failed: {e}")
        raise
    finally:
        session.close()


def main():
    """Main function to initialize the database."""
    parser = argparse.ArgumentParser(description="Initialize Termômetro de Tecnologia database")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables")
    parser.add_argument("--seed-only", action="store_true", help="Only run seed data")
    parser.add_argument("--no-seed", action="store_true", help="Skip seed data")
    parser.add_argument("--no-validate", action="store_true", help="Skip validation")
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Initializing Termômetro de Tecnologia Database")
    logger.info("=" * 60)
    logger.info(f"Database URL: {settings.database.url}")
    
    try:
        if args.reset:
            logger.warning("RESET MODE: This will destroy all existing data!")
            response = input("Are you sure you want to continue? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Operation cancelled")
                return
            drop_all_tables()
        
        if not args.seed_only:
            run_alembic_migrations()
        
        if not args.no_seed:
            seed_initial_data()
        
        if not args.no_validate:
            validate_setup()
        
        logger.info("=" * 60)
        logger.info("✓ Database initialization completed successfully!")
        logger.info("=" * 60)
        logger.info("Next steps:")
        logger.info("1. Start the Docker containers: docker compose up -d")
        logger.info("2. Run the collector: python main.py")
        logger.info("3. Check the database with Adminer: http://localhost:8080")
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error("✗ Database initialization failed!")
        logger.error("=" * 60)
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()