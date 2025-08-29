"""
Web application for health checks and monitoring - Railway deployment.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from src.utils.logger import get_logger
from src.utils.database import DatabaseManager
from config.settings import settings

# Initialize logger
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Termômetro de Tecnologia",
    description="Tech content monitoring and analysis system",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://tecdata.railway.app"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Termômetro de Tecnologia API",
        "version": "1.0.0",
        "environment": settings.environment,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Railway."""
    try:
        # Test database connection
        db_healthy = DatabaseManager.test_connection()
        
        # Get basic system info
        health_data = {
            "status": "healthy" if db_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "environment": settings.environment,
            "database": {
                "connected": db_healthy,
                "url_configured": bool(settings.database.url)
            },
            "services": {
                "web": True,
                "database": db_healthy
            }
        }
        
        # Add database statistics if connected
        if db_healthy:
            try:
                with DatabaseManager.get_session() as session:
                    from src.repositories.sites import SiteRepository
                    from src.repositories.articles import ArticleRepository
                    
                    site_repo = SiteRepository(session)
                    article_repo = ArticleRepository(session)
                    
                    # Get Tecmundo statistics
                    tecmundo_stats = site_repo.get_site_statistics("tecmundo")
                    
                    # Get recent articles count
                    site = site_repo.get_by_site_id("tecmundo")
                    recent_articles = 0
                    if site:
                        articles = article_repo.get_recent_articles(site.id, hours=24)
                        recent_articles = len(articles) if articles else 0
                    
                    health_data["statistics"] = {
                        "site_active": tecmundo_stats.get("is_active", False) if tecmundo_stats else False,
                        "total_articles": tecmundo_stats.get("total_articles", 0) if tecmundo_stats else 0,
                        "recent_articles_24h": recent_articles,
                        "success_rate": tecmundo_stats.get("success_rate", 0) if tecmundo_stats else 0,
                    }
                    
            except Exception as e:
                logger.warning(f"Could not get database statistics: {e}")
                health_data["statistics"] = {"error": "Could not retrieve statistics"}
        
        status_code = 200 if db_healthy else 503
        return JSONResponse(content=health_data, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            },
            status_code=503
        )


@app.get("/metrics")
async def get_metrics():
    """Get application metrics."""
    try:
        if not DatabaseManager.test_connection():
            raise HTTPException(status_code=503, detail="Database not available")
        
        with DatabaseManager.get_session() as session:
            from src.repositories.sites import SiteRepository
            from src.repositories.articles import ArticleRepository
            from src.repositories.snapshots import SnapshotRepository
            
            site_repo = SiteRepository(session)
            article_repo = ArticleRepository(session)
            snapshot_repo = SnapshotRepository(session)
            
            # Get site metrics
            site_metrics = []
            sites = site_repo.get_all_active()
            
            for site in sites:
                stats = site_repo.get_site_statistics(site.site_id)
                if stats:
                    site_metrics.append({
                        "site_id": site.site_id,
                        "name": site.name,
                        "total_articles": stats.get("total_articles", 0),
                        "recent_articles": stats.get("recent_articles", 0),
                        "success_rate": stats.get("success_rate", 0),
                        "last_collection": site.last_successful_collection.isoformat() if site.last_successful_collection else None
                    })
            
            # Get recent snapshots count
            recent_snapshots = session.query(
                snapshot_repo.model
            ).filter(
                snapshot_repo.model.timestamp >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "sites": site_metrics,
                "snapshots_24h": recent_snapshots,
                "environment": settings.environment
            }
            
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_status():
    """Get detailed application status."""
    try:
        db_connected = DatabaseManager.test_connection()
        
        status_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": settings.environment,
            "services": {
                "database": {
                    "status": "connected" if db_connected else "disconnected",
                    "url_configured": bool(settings.database.url)
                },
                "collection": {
                    "interval_hours": settings.collection.interval_hours,
                    "requests_per_minute": settings.collection.requests_per_minute
                },
                "api": {
                    "tecmundo_url": settings.api.tecmundo_full_url,
                    "timeout": settings.api.request_timeout,
                    "max_retries": settings.api.max_retries
                }
            }
        }
        
        if db_connected:
            try:
                with DatabaseManager.get_session() as session:
                    from src.repositories.sites import SiteRepository
                    
                    site_repo = SiteRepository(session)
                    sites = site_repo.get_all_active()
                    
                    status_data["sites"] = [
                        {
                            "site_id": site.site_id,
                            "name": site.name,
                            "is_active": site.is_active,
                            "last_collection": site.last_successful_collection.isoformat() if site.last_successful_collection else None
                        }
                        for site in sites
                    ]
                    
            except Exception as e:
                status_data["sites_error"] = str(e)
        
        return status_data
        
    except Exception as e:
        logger.error(f"Status endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Get port from environment (Railway sets this)
    port = int(os.environ.get("PORT", 8000))
    
    logger.info(f"Starting web server on port {port}")
    logger.info(f"PORT environment variable: {os.environ.get('PORT', 'not set')}")
    logger.info(f"All environment variables: {dict(os.environ)}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database URL configured: {bool(settings.database.url)}")
    
    # Run the server
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )