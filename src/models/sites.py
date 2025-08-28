"""Site model for managing multiple technology sites."""

from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class Site(Base):
    """Model for storing information about technology sites we collect from."""
    
    __tablename__ = "sites"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    site_id = Column(String(50), nullable=False, unique=True, index=True)  # Used in other tables
    base_url = Column(String(500), nullable=False)
    api_endpoints = Column(JSON, nullable=False)  # Store multiple endpoints config
    
    # Site configuration
    rate_limit_per_hour = Column(Integer, default=60, nullable=False)
    request_timeout_ms = Column(Integer, default=30000, nullable=False)
    retry_count = Column(Integer, default=3, nullable=False)
    retry_delay_ms = Column(Integer, default=1000, nullable=False)
    
    # Authentication if needed
    requires_auth = Column(Boolean, default=False, nullable=False)
    auth_config = Column(JSON, nullable=True)  # Store auth configuration
    
    # Site metadata
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # tech_news, developer_blog, etc.
    country = Column(String(10), default='BR', nullable=False)
    language = Column(String(10), default='pt-BR', nullable=False)
    
    # Collection status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    last_successful_collection = Column(
        DateTime(timezone=True),
        nullable=True
    )
    collection_error_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    snapshots = relationship("Snapshot", back_populates="site", cascade="all, delete-orphan")
    articles = relationship("Article", back_populates="site", cascade="all, delete-orphan")
    authors = relationship("Author", back_populates="site", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="site", cascade="all, delete-orphan")
    collection_stats = relationship("CollectionStats", back_populates="site", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Site(id={self.id}, name='{self.name}', site_id='{self.site_id}', active={self.is_active})>"
    
    def increment_error_count(self):
        """Increment collection error count."""
        self.collection_error_count += 1
        
    def reset_error_count(self):
        """Reset collection error count after successful collection."""
        from datetime import datetime
        self.collection_error_count = 0
        self.last_successful_collection = datetime.utcnow()
    
    @property
    def is_healthy(self) -> bool:
        """Check if site collection is healthy (less than 5 consecutive errors)."""
        return self.collection_error_count < 5