"""Author model for managing article authors."""

from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class Author(Base):
    """Model for storing author information across sites."""
    
    __tablename__ = "authors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    
    # Site-specific information
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)
    external_author_id = Column(String(100), nullable=True, index=True)  # Author ID from source site
    
    # Author profile information
    bio = Column(Text, nullable=True)
    profile_url = Column(String(500), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    social_links = Column(JSON, nullable=True)  # Twitter, LinkedIn, etc.
    
    # Author metadata
    email = Column(String(255), nullable=True)
    job_title = Column(String(200), nullable=True)
    company = Column(String(200), nullable=True)
    location = Column(String(100), nullable=True)
    
    # Statistics (will be updated by aggregation jobs)
    total_articles = Column(Integer, default=0, nullable=False)
    first_article_date = Column(DateTime(timezone=True), nullable=True)
    last_article_date = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    site = relationship("Site", back_populates="authors")
    articles = relationship("Article", back_populates="author")
    
    def __repr__(self):
        return f"<Author(id={self.id}, name='{self.name}', site_id={self.site_id}, articles={self.total_articles})>"
    
    @classmethod
    def get_or_create_by_name_and_site(cls, session, name: str, site_id: int, **kwargs):
        """Get existing author or create new one by name and site."""
        author = session.query(cls).filter_by(name=name, site_id=site_id).first()
        if not author:
            author = cls(name=name, site_id=site_id, **kwargs)
            session.add(author)
            session.flush()  # Get the ID
        return author
    
    def update_article_stats(self, session):
        """Update author statistics based on their articles."""
        from .articles import Article
        
        articles_query = session.query(Article).filter_by(
            author_id=self.id,
            is_deleted=False
        )
        
        self.total_articles = articles_query.count()
        
        if self.total_articles > 0:
            first_article = articles_query.order_by(Article.first_seen.asc()).first()
            last_article = articles_query.order_by(Article.last_seen.desc()).first()
            
            self.first_article_date = first_article.first_seen
            self.last_article_date = last_article.last_seen