#!/usr/bin/env python3
"""
Monitoring script for Railway deployment - checks system health and performance.
Can be used for automated monitoring or manual health checks.
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.utils.logger import get_logger
from src.utils.database import DatabaseManager
from config.settings import settings

# Initialize logger
logger = get_logger(__name__)


def check_database_health():
    """Check database connection and basic health."""
    try:
        if not DatabaseManager.test_connection():
            return {
                "status": "unhealthy",
                "error": "Database connection failed"
            }
        
        with DatabaseManager.get_session() as session:
            # Test basic query
            result = session.execute("SELECT 1").fetchone()
            if not result:
                return {
                    "status": "unhealthy",
                    "error": "Database query test failed"
                }
        
        return {"status": "healthy"}
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def get_collection_stats():
    """Get collection statistics and health."""
    try:
        with DatabaseManager.get_session() as session:
            from src.repositories.sites import SiteRepository
            from src.repositories.articles import ArticleRepository
            from src.repositories.snapshots import SnapshotRepository
            
            site_repo = SiteRepository(session)
            article_repo = ArticleRepository(session)
            snapshot_repo = SnapshotRepository(session)
            
            # Get Tecmundo statistics
            tecmundo_stats = site_repo.get_site_statistics("tecmundo")
            site = site_repo.get_by_site_id("tecmundo")
            
            if not site:
                return {
                    "status": "warning",
                    "message": "Tecmundo site not found"
                }
            
            # Get recent activity
            recent_articles = article_repo.get_recent_articles(site.id, hours=24)
            recent_snapshots = session.query(
                snapshot_repo.model
            ).filter(
                snapshot_repo.model.timestamp >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            # Calculate health score
            health_score = 100
            warnings = []
            
            # Check if collection is too old
            if site.last_successful_collection:
                hours_since_last = (datetime.utcnow() - site.last_successful_collection).total_seconds() / 3600
                expected_interval = settings.collection.interval_hours
                
                if hours_since_last > expected_interval * 2:
                    health_score -= 30
                    warnings.append(f"Last collection was {hours_since_last:.1f} hours ago (expected every {expected_interval}h)")
            else:
                health_score -= 50
                warnings.append("No successful collections recorded")
            
            # Check recent activity
            if len(recent_articles) == 0:
                health_score -= 20
                warnings.append("No articles collected in last 24 hours")
            
            if recent_snapshots == 0:
                health_score -= 20
                warnings.append("No snapshots recorded in last 24 hours")
            
            # Check success rate
            if tecmundo_stats:
                success_rate = tecmundo_stats.get("success_rate", 0)
                if success_rate < 80:
                    health_score -= 30
                    warnings.append(f"Low success rate: {success_rate:.1f}%")
            
            status = "healthy" if health_score >= 80 else ("warning" if health_score >= 50 else "critical")
            
            return {
                "status": status,
                "health_score": health_score,
                "warnings": warnings,
                "stats": {
                    "site_active": site.is_active,
                    "last_collection": site.last_successful_collection.isoformat() if site.last_successful_collection else None,
                    "total_articles": tecmundo_stats.get("total_articles", 0) if tecmundo_stats else 0,
                    "recent_articles_24h": len(recent_articles),
                    "recent_snapshots_24h": recent_snapshots,
                    "success_rate": tecmundo_stats.get("success_rate", 0) if tecmundo_stats else 0,
                    "error_count": tecmundo_stats.get("error_count", 0) if tecmundo_stats else 0
                }
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def check_api_connectivity():
    """Check if external APIs are accessible."""
    try:
        import requests
        
        # Test Tecmundo API
        response = requests.get(
            settings.api.tecmundo_full_url,
            timeout=settings.api.request_timeout,
            headers={"User-Agent": "TecData-Monitor/1.0"}
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                articles_count = len(data.get("posts", []))
                return {
                    "status": "healthy",
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "articles_available": articles_count
                }
            except Exception:
                return {
                    "status": "warning",
                    "message": "API responded but data format unexpected",
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
        else:
            return {
                "status": "unhealthy",
                "error": f"API returned status {response.status_code}",
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
            
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def generate_health_report():
    """Generate comprehensive health report."""
    logger.info("Generating health report...")
    
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
        "checks": {}
    }
    
    # Database health
    logger.info("Checking database health...")
    report["checks"]["database"] = check_database_health()
    
    # Collection stats (only if database is healthy)
    if report["checks"]["database"]["status"] == "healthy":
        logger.info("Checking collection statistics...")
        report["checks"]["collection"] = get_collection_stats()
    else:
        report["checks"]["collection"] = {
            "status": "skipped",
            "reason": "Database unhealthy"
        }
    
    # API connectivity
    logger.info("Checking API connectivity...")
    report["checks"]["api"] = check_api_connectivity()
    
    # Overall health
    statuses = [check["status"] for check in report["checks"].values() if check["status"] != "skipped"]
    
    if "critical" in statuses or "unhealthy" in statuses:
        report["overall_status"] = "critical"
    elif "warning" in statuses:
        report["overall_status"] = "warning"
    elif all(status == "healthy" for status in statuses):
        report["overall_status"] = "healthy"
    else:
        report["overall_status"] = "unknown"
    
    return report


def main():
    """Main monitoring function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor Termômetro de Tecnologia system health")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--quiet", action="store_true", help="Suppress log output")
    
    args = parser.parse_args()
    
    if not args.quiet:
        logger.info("=" * 60)
        logger.info("Termômetro de Tecnologia - Health Monitor")
        logger.info("=" * 60)
    
    # Generate health report
    report = generate_health_report()
    
    if args.json:
        # Output JSON for programmatic use
        print(json.dumps(report, indent=2))
    else:
        # Human-readable output
        print(f"\n{'='*60}")
        print(f"HEALTH REPORT - {report['timestamp']}")
        print(f"Environment: {report['environment']}")
        print(f"Overall Status: {report['overall_status'].upper()}")
        print(f"{'='*60}")
        
        for check_name, check_result in report["checks"].items():
            print(f"\n{check_name.title()} Check:")
            print(f"  Status: {check_result['status'].upper()}")
            
            if check_result.get("error"):
                print(f"  Error: {check_result['error']}")
            
            if check_result.get("warnings"):
                for warning in check_result["warnings"]:
                    print(f"  Warning: {warning}")
            
            if check_result.get("stats"):
                print("  Statistics:")
                for key, value in check_result["stats"].items():
                    print(f"    {key}: {value}")
            
            if check_result.get("health_score"):
                print(f"  Health Score: {check_result['health_score']}/100")
            
            if check_result.get("response_time_ms"):
                print(f"  Response Time: {check_result['response_time_ms']:.0f}ms")
        
        print(f"\n{'='*60}")
    
    # Exit with appropriate code
    if report["overall_status"] == "critical":
        sys.exit(2)
    elif report["overall_status"] == "warning":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()