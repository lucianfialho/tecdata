"""Collection statistics model for aggregated metrics."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Index, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class CollectionStats(Base):
    """Model for storing aggregated collection statistics by period."""
    
    __tablename__ = "collection_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)
    
    # Time period
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), nullable=False, index=True)  # hour, day, week, month
    
    # Collection metrics
    total_requests = Column(Integer, default=0, nullable=False)
    successful_requests = Column(Integer, default=0, nullable=False)
    failed_requests = Column(Integer, default=0, nullable=False)
    avg_response_time_ms = Column(Float, nullable=True)
    max_response_time_ms = Column(Integer, nullable=True)
    min_response_time_ms = Column(Integer, nullable=True)
    total_response_size_bytes = Column(Integer, default=0, nullable=False)
    
    # Data processing metrics
    total_articles_found = Column(Integer, default=0, nullable=False)
    new_articles_created = Column(Integer, default=0, nullable=False)
    existing_articles_updated = Column(Integer, default=0, nullable=False)
    duplicate_articles_found = Column(Integer, default=0, nullable=False)
    processing_errors = Column(Integer, default=0, nullable=False)
    
    # Content metrics
    unique_authors_found = Column(Integer, default=0, nullable=False)
    unique_categories_found = Column(Integer, default=0, nullable=False)
    total_word_count = Column(Integer, default=0, nullable=False)
    avg_article_quality_score = Column(Float, nullable=True)
    
    # Error tracking
    error_rate = Column(Float, nullable=True)  # Percentage of failed requests
    error_types = Column(JSON, nullable=True)  # Count of different error types
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Quality metrics
    data_quality_score = Column(Float, nullable=True)  # Average quality score
    validation_error_count = Column(Integer, default=0, nullable=False)
    content_freshness_score = Column(Float, nullable=True)  # How fresh is the content
    
    # Performance indexes
    __table_args__ = (
        Index('idx_collection_stats_site_period', 'site_id', 'period_start', 'period_type'),
        Index('idx_collection_stats_period_type', 'period_type', 'period_start'),
    )
    
    # Relationships
    site = relationship("Site", back_populates="collection_stats")
    
    def __repr__(self):
        return (
            f"<CollectionStats(site_id={self.site_id}, period={self.period_type}, "
            f"start={self.period_start}, articles={self.total_articles_found})>"
        )
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def new_article_rate(self) -> float:
        """Calculate percentage of new articles vs total found."""
        if self.total_articles_found == 0:
            return 0.0
        return (self.new_articles_created / self.total_articles_found) * 100
    
    @property
    def avg_response_size_kb(self) -> float:
        """Average response size in KB."""
        if self.total_requests == 0:
            return 0.0
        return (self.total_response_size_bytes / self.total_requests) / 1024
    
    def calculate_error_rate(self):
        """Calculate and update error rate."""
        if self.total_requests > 0:
            self.error_rate = (self.failed_requests / self.total_requests) * 100
        else:
            self.error_rate = 0.0
    
    def calculate_content_freshness_score(self, session):
        """Calculate freshness score based on recent articles."""
        from .articles import Article
        from datetime import datetime, timedelta
        
        # Get articles created in this period
        articles_in_period = session.query(Article).filter(
            Article.site_id == self.site_id,
            Article.first_seen >= self.period_start,
            Article.first_seen < self.period_end
        ).all()
        
        if not articles_in_period:
            self.content_freshness_score = 0.0
            return
        
        # Calculate based on how recent the published dates are
        now = datetime.utcnow()
        total_freshness = 0.0
        
        for article in articles_in_period:
            if article.published_at:
                days_old = (now - article.published_at).days
                # Fresher articles get higher scores (max 100 for articles published today)
                freshness = max(0, 100 - (days_old * 2))  # Lose 2 points per day
                total_freshness += freshness
        
        self.content_freshness_score = total_freshness / len(articles_in_period)
    
    @classmethod
    def create_period_stats(cls, session, site_id: int, period_start: datetime, 
                          period_end: datetime, period_type: str):
        """Create statistics for a specific period."""
        from .snapshots import Snapshot
        from .articles import Article
        from datetime import datetime
        
        # Get snapshots in period
        snapshots = session.query(Snapshot).filter(
            Snapshot.site_id == site_id,
            Snapshot.timestamp >= period_start,
            Snapshot.timestamp < period_end
        ).all()
        
        # Calculate snapshot metrics
        total_requests = len(snapshots)
        successful_requests = len([s for s in snapshots if s.is_successful])
        failed_requests = total_requests - successful_requests
        
        response_times = [s.response_time_ms for s in snapshots if s.response_time_ms]
        avg_response_time = sum(response_times) / len(response_times) if response_times else None
        max_response_time = max(response_times) if response_times else None
        min_response_time = min(response_times) if response_times else None
        
        total_response_size = sum(s.response_size_bytes or 0 for s in snapshots)
        
        # Get articles in period
        articles_in_period = session.query(Article).filter(
            Article.site_id == site_id,
            Article.first_seen >= period_start,
            Article.first_seen < period_end,
            Article.is_deleted == False
        ).all()
        
        # Calculate article metrics
        total_articles_found = len(articles_in_period)
        new_articles = len([a for a in articles_in_period if a.first_seen == a.last_seen])
        updated_articles = total_articles_found - new_articles
        
        # Get unique counts
        unique_authors = len(set(a.author_id for a in articles_in_period if a.author_id))
        unique_categories = len(set(a.category_id for a in articles_in_period if a.category_id))
        
        # Calculate quality metrics
        quality_scores = [a.quality_score for a in articles_in_period if a.quality_score > 0]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else None
        
        # Create stats record
        stats = cls(
            site_id=site_id,
            period_start=period_start,
            period_end=period_end,
            period_type=period_type,
            
            # Request metrics
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time_ms=avg_response_time,
            max_response_time_ms=max_response_time,
            min_response_time_ms=min_response_time,
            total_response_size_bytes=total_response_size,
            
            # Article metrics
            total_articles_found=total_articles_found,
            new_articles_created=new_articles,
            existing_articles_updated=updated_articles,
            unique_authors_found=unique_authors,
            unique_categories_found=unique_categories,
            avg_article_quality_score=avg_quality,
        )
        
        # Calculate derived metrics
        stats.calculate_error_rate()
        stats.calculate_content_freshness_score(session)
        
        # Calculate average data quality from snapshots
        data_quality_scores = [s.data_quality_score for s in snapshots if s.data_quality_score]
        if data_quality_scores:
            stats.data_quality_score = sum(data_quality_scores) / len(data_quality_scores)
        
        session.add(stats)
        session.flush()
        
        return stats
    
    @classmethod
    def get_latest_stats(cls, session, site_id: int, period_type: str, limit: int = 10):
        """Get the most recent statistics for a site and period type."""
        return session.query(cls).filter_by(
            site_id=site_id,
            period_type=period_type
        ).order_by(
            cls.period_start.desc()
        ).limit(limit).all()
    
    @classmethod
    def get_stats_summary(cls, session, site_id: int, days: int = 7):
        """Get a summary of statistics for the last N days."""
        from datetime import datetime, timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        stats = session.query(cls).filter(
            cls.site_id == site_id,
            cls.period_start >= start_date,
            cls.period_type == 'day'
        ).all()
        
        if not stats:
            return None
        
        return {
            'total_requests': sum(s.total_requests for s in stats),
            'avg_success_rate': sum(s.success_rate for s in stats) / len(stats),
            'total_articles': sum(s.total_articles_found for s in stats),
            'total_new_articles': sum(s.new_articles_created for s in stats),
            'avg_response_time': sum(s.avg_response_time_ms or 0 for s in stats) / len([s for s in stats if s.avg_response_time_ms]),
            'avg_quality_score': sum(s.avg_article_quality_score or 0 for s in stats) / len([s for s in stats if s.avg_article_quality_score]),
        }