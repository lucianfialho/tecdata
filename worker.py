"""
Worker process for periodic data collection - Railway deployment.
"""

import sys
import asyncio
import signal
from datetime import datetime, timedelta
from pathlib import Path
import time

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.logger import get_logger
from src.utils.database import DatabaseManager
from src.collectors.tecmundo import TecmundoCollector
from config.settings import settings

# Initialize logger
logger = get_logger(__name__)

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_requested = True


class CollectionWorker:
    """Worker class for periodic data collection."""
    
    def __init__(self):
        self.is_running = False
        self.last_collection = None
        self.collection_count = 0
        
    def should_collect(self) -> bool:
        """Check if it's time for a new collection."""
        if self.last_collection is None:
            return True
        
        elapsed = datetime.utcnow() - self.last_collection
        interval = timedelta(hours=settings.collection.interval_hours)
        
        return elapsed >= interval
    
    def run_collection(self) -> bool:
        """Run a single data collection cycle."""
        try:
            logger.info("Starting data collection cycle")
            
            # Test database connection first
            if not DatabaseManager.test_connection():
                logger.error("Database connection failed, skipping collection")
                return False
            
            # Initialize database if needed
            try:
                DatabaseManager.init_database()
            except Exception as e:
                logger.warning(f"Database initialization warning: {e}")
            
            # Run Tecmundo collection
            with TecmundoCollector() as collector:
                success = collector.collect_data()
                metrics = collector.get_collection_metrics()
                
                if success and metrics:
                    logger.info("✓ Collection completed successfully")
                    logger.info(f"  Articles found: {metrics.articles_found}")
                    logger.info(f"  Articles new: {metrics.articles_new}")
                    logger.info(f"  Articles updated: {metrics.articles_updated}")
                    logger.info(f"  Articles skipped: {metrics.articles_skipped}")
                    logger.info(f"  Response time: {metrics.response_time_ms}ms")
                    logger.info(f"  Duration: {metrics.duration_seconds():.2f}s")
                    
                    self.last_collection = datetime.utcnow()
                    self.collection_count += 1
                    
                    if metrics.errors:
                        logger.warning(f"  Collection had {len(metrics.errors)} errors")
                        for error in metrics.errors[:3]:  # Log first 3 errors
                            logger.warning(f"    - {error}")
                    
                    return True
                else:
                    logger.error("✗ Collection failed")
                    if metrics and metrics.errors:
                        for error in metrics.errors:
                            logger.error(f"  Error: {error}")
                    return False
                    
        except Exception as e:
            logger.error(f"Collection cycle failed: {e}")
            return False
    
    def get_next_collection_time(self) -> datetime:
        """Get the next scheduled collection time."""
        if self.last_collection is None:
            return datetime.utcnow()
        
        return self.last_collection + timedelta(hours=settings.collection.interval_hours)
    
    async def run_forever(self):
        """Main worker loop."""
        self.is_running = True
        logger.info("Worker started")
        logger.info(f"Collection interval: {settings.collection.interval_hours} hours")
        logger.info(f"Database URL configured: {bool(settings.database.url)}")
        
        # Run initial collection if database is ready
        logger.info("Running initial collection check...")
        if self.should_collect():
            self.run_collection()
        else:
            logger.info("Skipping initial collection - too soon since last run")
        
        while self.is_running and not shutdown_requested:
            try:
                if self.should_collect():
                    logger.info(f"Collection #{self.collection_count + 1} starting...")
                    success = self.run_collection()
                    
                    if success:
                        logger.info(f"Collection #{self.collection_count} completed successfully")
                    else:
                        logger.error(f"Collection #{self.collection_count + 1} failed")
                else:
                    # Log status periodically
                    next_collection = self.get_next_collection_time()
                    time_until_next = next_collection - datetime.utcnow()
                    
                    if time_until_next.total_seconds() > 0:
                        hours = int(time_until_next.total_seconds() // 3600)
                        minutes = int((time_until_next.total_seconds() % 3600) // 60)
                        logger.info(f"Next collection in {hours}h {minutes}m (at {next_collection.strftime('%H:%M:%S')})")
                
                # Sleep for 5 minutes between checks
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(60)  # Sleep 1 minute on error
        
        logger.info("Worker stopped")
        self.is_running = False


async def main():
    """Main entry point."""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    logger.info("=" * 60)
    logger.info("Termômetro de Tecnologia - Worker Process")
    logger.info("=" * 60)
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Collection interval: {settings.collection.interval_hours} hours")
    logger.info(f"Database configured: {bool(settings.database.url)}")
    
    # Test database connection
    logger.info("Testing database connection...")
    if DatabaseManager.test_connection():
        logger.info("✓ Database connection successful")
    else:
        logger.error("✗ Database connection failed")
        logger.error("Worker cannot start without database connection")
        sys.exit(1)
    
    # Start the worker
    worker = CollectionWorker()
    
    try:
        await worker.run_forever()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Worker crashed: {e}")
        sys.exit(1)
    finally:
        logger.info("Worker shutdown complete")


if __name__ == "__main__":
    # Run the worker
    asyncio.run(main())