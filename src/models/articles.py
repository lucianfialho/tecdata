"""Article model for storing processed article data."""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey, UniqueConstraint, Index, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class Article(Base):
    """Model for storing processed article information."""
    
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), nullable=False, index=True)  # ID from source site
    
    # Site and content relationships
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("authors.id"), nullable=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    
    # Article content
    title = Column(String(500), nullable=False, index=True)
    slug = Column(String(500), nullable=True, index=True)  # URL-friendly version
    summary = Column(Text, nullable=True)
    content_excerpt = Column(Text, nullable=True)  # First few paragraphs
    
    # URLs and media
    url = Column(Text, nullable=False)
    canonical_url = Column(Text, nullable=True)  # For duplicate detection
    image_url = Column(Text, nullable=True)
    images = Column(JSON, nullable=True)  # Additional images
    
    # Article metadata
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)  # Original publish date
    word_count = Column(Integer, nullable=True)
    reading_time_minutes = Column(Integer, nullable=True)
    language = Column(String(10), default='pt-BR', nullable=False)
    
    # Content analysis (for future NLP processing)
    tags = Column(JSON, nullable=True)  # Extracted tags
    keywords = Column(JSON, nullable=True)  # Extracted keywords
    sentiment_score = Column(Float, nullable=True)  # -1 to 1
    topics = Column(JSON, nullable=True)  # AI-extracted topics
    
    # Tracking timestamps
    first_seen = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True)
    last_updated = Column(DateTime(timezone=True), nullable=True)  # When content was last updated
    
    # Status and quality
    is_active = Column(Boolean, default=True, index=True)
    is_duplicate = Column(Boolean, default=False, nullable=False, index=True)
    duplicate_of_id = Column(Integer, ForeignKey("articles.id"), nullable=True, index=True)
    quality_score = Column(Float, default=0.0, nullable=False)  # Content quality 0-100
    
    # Collection metadata
    collection_errors = Column(JSON, nullable=True)  # Track any collection issues
    raw_data = Column(JSON, nullable=True)  # Original data from API for debugging
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint('external_id', 'site_id', name='uq_article_external_site'),
        Index('idx_article_site_published', 'site_id', 'published_at'),
        Index('idx_article_site_first_seen', 'site_id', 'first_seen'),
        Index('idx_article_active_published', 'is_active', 'published_at'),
    )
    
    # Relationships
    site = relationship("Site", back_populates="articles")
    author = relationship("Author", back_populates="articles")
    category = relationship("Category", back_populates="articles")
    duplicate_of = relationship("Article", remote_side=[id], back_populates="duplicates")
    duplicates = relationship("Article", back_populates="duplicate_of")
    history = relationship("ArticleHistory", back_populates="article", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title[:50]}...', site_id={self.site_id})>"
    
    @classmethod
    def find_by_external_id(cls, session, external_id: str, site_id: int):
        """Find article by external ID and site."""
        return session.query(cls).filter_by(
            external_id=external_id, 
            site_id=site_id,
            is_deleted=False
        ).first()
    
    def mark_as_duplicate(self, original_article_id: int):
        """Mark this article as a duplicate of another."""
        self.is_duplicate = True
        self.duplicate_of_id = original_article_id
        self.is_active = False
    
    def calculate_reading_time(self):
        """Estimate reading time based on word count (250 words per minute)."""
        if self.word_count:
            self.reading_time_minutes = max(1, round(self.word_count / 250))
    
    def update_last_seen(self):
        """Update the last_seen timestamp to now."""
        from datetime import datetime
        self.last_seen = datetime.utcnow()
    
    def extract_slug_from_url(self):
        """Extract a slug from the article URL."""
        if self.url:
            # Simple slug extraction from URL
            import re
            from urllib.parse import urlparse
            path = urlparse(self.url).path
            # Remove leading/trailing slashes and file extensions
            slug = re.sub(r'^/|/$|\.html?$', '', path)
            # Replace special characters with hyphens
            slug = re.sub(r'[^a-zA-Z0-9\-_]', '-', slug)
            # Remove multiple consecutive hyphens
            slug = re.sub(r'-+', '-', slug)
            self.slug = slug[:500] if slug else None