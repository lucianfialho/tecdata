"""Site analytics model for aggregated metrics."""

from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.sql import func
from .base import Base


class SiteAnalytics(Base):
    """Model for storing aggregated site analytics by period."""
    
    __tablename__ = "site_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(50), nullable=False, index=True)
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), nullable=False, index=True)  # hour, day, week, month
    
    # Metrics
    total_articles = Column(Integer, default=0)
    new_articles = Column(Integer, default=0)
    unique_authors = Column(Integer, default=0)
    unique_categories = Column(Integer, default=0)
    avg_response_time_ms = Column(Float, nullable=True)
    success_rate = Column(Float, nullable=True)  # Percentage of successful requests
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return (
            f"<SiteAnalytics(site={self.site_id}, period={self.period_type}, "
            f"articles={self.total_articles})>"
        )