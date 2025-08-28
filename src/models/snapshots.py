"""Snapshot model for storing raw API responses."""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, ForeignKey, Index, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class Snapshot(Base):
    """Model for storing raw API snapshots with timestamp."""
    
    __tablename__ = "snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Site relationship
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)
    
    # Request details
    endpoint = Column(String(255), nullable=False, index=True)
    method = Column(String(10), default='GET', nullable=False)
    request_headers = Column(JSON, nullable=True)
    request_params = Column(JSON, nullable=True)
    
    # Response details
    response_status = Column(Integer, nullable=False, index=True)
    response_headers = Column(JSON, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    response_size_bytes = Column(Integer, nullable=True)
    
    # Data and processing
    raw_data = Column(JSON, nullable=False)
    processed_count = Column(Integer, default=0, nullable=False)  # Number of items processed
    error_message = Column(Text, nullable=True)
    
    # Data quality metrics
    data_quality_score = Column(Float, nullable=True)  # 0-100 score
    validation_errors = Column(JSON, nullable=True)  # Schema validation errors
    
    # Collection metadata
    collection_batch_id = Column(String(100), nullable=True, index=True)  # Group related snapshots
    retry_count = Column(Integer, default=0, nullable=False)
    is_retry = Column(Boolean, default=False, nullable=False)
    parent_snapshot_id = Column(Integer, ForeignKey("snapshots.id"), nullable=True)  # For retries
    
    # Performance indexes
    __table_args__ = (
        Index('idx_snapshot_site_timestamp', 'site_id', 'timestamp'),
        Index('idx_snapshot_status_timestamp', 'response_status', 'timestamp'),
        Index('idx_snapshot_batch_timestamp', 'collection_batch_id', 'timestamp'),
    )
    
    # Relationships
    site = relationship("Site", back_populates="snapshots")
    parent_snapshot = relationship("Snapshot", remote_side=[id], back_populates="retry_snapshots")
    retry_snapshots = relationship("Snapshot", back_populates="parent_snapshot")
    
    def __repr__(self):
        return f"<Snapshot(id={self.id}, site_id={self.site_id}, status={self.response_status}, timestamp={self.timestamp})>"
    
    @property
    def is_successful(self) -> bool:
        """Check if the snapshot represents a successful API call."""
        return 200 <= self.response_status < 300
    
    @property
    def is_client_error(self) -> bool:
        """Check if the snapshot represents a client error (4xx)."""
        return 400 <= self.response_status < 500
    
    @property
    def is_server_error(self) -> bool:
        """Check if the snapshot represents a server error (5xx)."""
        return self.response_status >= 500
    
    def calculate_data_quality_score(self) -> float:
        """Calculate a quality score for the collected data."""
        score = 100.0
        
        # Deduct points for errors
        if not self.is_successful:
            score -= 50.0
        
        # Deduct points for empty data
        if not self.raw_data or (isinstance(self.raw_data, (list, dict)) and len(self.raw_data) == 0):
            score -= 30.0
        
        # Deduct points for validation errors
        if self.validation_errors and len(self.validation_errors) > 0:
            score -= min(20.0, len(self.validation_errors) * 2)
        
        # Deduct points for slow response
        if self.response_time_ms and self.response_time_ms > 10000:  # > 10 seconds
            score -= 10.0
        
        return max(0.0, score)
    
    @classmethod
    def get_latest_successful_snapshot(cls, session, site_id: int, endpoint: str):
        """Get the most recent successful snapshot for a site/endpoint."""
        return session.query(cls).filter_by(
            site_id=site_id,
            endpoint=endpoint
        ).filter(
            cls.response_status >= 200,
            cls.response_status < 300
        ).order_by(
            cls.timestamp.desc()
        ).first()
    
    @classmethod
    def get_error_snapshots(cls, session, site_id: int, hours: int = 24):
        """Get recent error snapshots for a site."""
        from datetime import datetime, timedelta
        
        return session.query(cls).filter(
            cls.site_id == site_id,
            cls.response_status >= 400,
            cls.timestamp >= datetime.utcnow() - timedelta(hours=hours)
        ).order_by(cls.timestamp.desc()).all()