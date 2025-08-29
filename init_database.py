#!/usr/bin/env python3
"""Initialize database on Railway deployment."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("🚀 Initializing database on Railway...")
    
    # Check if DATABASE_URL is set
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("Available vars:", list(os.environ.keys()))
        return
    
    print(f"✅ DATABASE_URL found: {database_url[:50]}...")
    
    try:
        # Import after adding to path
        from src.utils.database import DatabaseManager
        from src.models.base import init_db
        
        print("📊 Testing database connection...")
        if DatabaseManager.test_connection():
            print("✅ Database connection successful")
            
            print("🏗️ Initializing database tables...")
            init_db()
            print("✅ Database tables initialized successfully")
            
            # Create initial data
            print("🌱 Creating initial data...")
            from src.repositories.sites import SiteRepository
            with DatabaseManager.get_session() as session:
                site_repo = SiteRepository(session)
                
                # Check if Tecmundo site exists
                tecmundo = site_repo.get_by_site_id("tecmundo")
                if not tecmundo:
                    from src.models.sites import Site
                    tecmundo = Site(
                        site_id="tecmundo",
                        name="Tecmundo",
                        base_url="https://www.tecmundo.com.br",
                        api_endpoint="/api/posts?endpoint=home-author",
                        is_active=True
                    )
                    site_repo.create(tecmundo)
                    print("✅ Tecmundo site created")
                else:
                    print("✅ Tecmundo site already exists")
                    
            print("🎉 Database initialization complete!")
        else:
            print("❌ Database connection failed")
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()