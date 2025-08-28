"""Base collector class for data collection from tech sites."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import time
from src.utils.http_client import HTTPClient
from src.utils.database import DatabaseManager
from src.utils.logger import get_logger
from src.models.snapshots import Snapshot
from src.models.articles import Article

logger = get_logger(__name__)


class BaseCollector(ABC):
    """Base class for site data collectors."""
    
    def __init__(self, site_id: str):
        self.site_id = site_id
        self.http_client = HTTPClient()
    
    @abstractmethod
    def get_api_url(self) -> str:
        """Get the API URL for this collector."""
        pass
    
    @abstractmethod
    def parse_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse API response into article data."""
        pass
    
    def collect_data(self) -> bool:
        """Collect data from the site and store in database."""
        start_time = time.time()
        
        try:
            logger.info(f"Starting data collection for {self.site_id}")
            
            # Make API request
            url = self.get_api_url()
            response = self.http_client.get(url)
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Parse JSON response
            data = response.json()
            
            # Store raw snapshot
            self._store_snapshot(
                data=data,
                response_status=response.status_code,
                response_time_ms=response_time_ms
            )
            
            # Parse and store articles
            articles_data = self.parse_response(data)
            stored_count = self._store_articles(articles_data)
            
            logger.info(
                f"Collection completed for {self.site_id}: "
                f"{stored_count} articles processed in {response_time_ms}ms"
            )
            
            return True
            
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Collection failed for {self.site_id}: {e}")
            
            # Store failed snapshot
            self._store_snapshot(
                data={},
                response_status=0,
                response_time_ms=response_time_ms,
                error_message=str(e)
            )
            
            return False
    
    def _store_snapshot(
        self,
        data: Dict[str, Any],
        response_status: int,
        response_time_ms: int,
        error_message: Optional[str] = None
    ):
        """Store raw API snapshot."""
        try:
            with DatabaseManager.get_session() as session:
                snapshot = Snapshot(
                    site_id=self.site_id,
                    endpoint=self.get_api_url(),
                    raw_data=data,
                    response_status=response_status,
                    response_time_ms=response_time_ms,
                    error_message=error_message
                )
                session.add(snapshot)
                session.commit()
                logger.debug(f"Snapshot stored with ID: {snapshot.id}")
        except Exception as e:
            logger.error(f"Failed to store snapshot: {e}")
    
    def _store_articles(self, articles_data: List[Dict[str, Any]]) -> int:
        """Store parsed articles."""
        stored_count = 0
        
        try:
            with DatabaseManager.get_session() as session:
                for article_data in articles_data:
                    # Check if article already exists
                    existing = session.query(Article).filter_by(
                        external_id=article_data.get('external_id'),
                        site_id=self.site_id
                    ).first()
                    
                    if existing:
                        # Update last_seen timestamp
                        existing.last_seen = datetime.utcnow()
                        logger.debug(f"Updated article: {existing.title[:50]}")
                    else:
                        # Create new article
                        article = Article(
                            external_id=article_data.get('external_id'),
                            site_id=self.site_id,
                            title=article_data.get('title', ''),
                            author=article_data.get('author'),
                            category=article_data.get('category'),
                            url=article_data.get('url'),
                            summary=article_data.get('summary'),
                            image_url=article_data.get('image_url')
                        )
                        session.add(article)
                        stored_count += 1
                        logger.debug(f"Stored new article: {article.title[:50]}")
                
                session.commit()
                
        except Exception as e:
            logger.error(f"Failed to store articles: {e}")
        
        return stored_count
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.http_client.close()