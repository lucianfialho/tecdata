"""Category model for managing article categories."""

from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, UniqueConstraint, Boolean, DateTime, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class Category(Base):
    """Model for storing article categories per site."""
    
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    
    # Site-specific information
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)
    external_category_id = Column(String(100), nullable=True, index=True)  # Category ID from source site
    
    # Category metadata
    display_name = Column(String(200), nullable=True)  # Formatted name for display
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code for UI
    icon = Column(String(50), nullable=True)  # Icon identifier
    
    # Category hierarchy (for nested categories)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    hierarchy_path = Column(String(500), nullable=True, index=True)  # e.g., "tech/mobile/android"
    level = Column(Integer, default=0, nullable=False)  # 0 = root, 1 = child, etc.
    
    # Category configuration
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    sort_order = Column(Integer, default=0, nullable=False)  # For ordering in UI
    
    # Statistics (updated by aggregation jobs)
    total_articles = Column(Integer, default=0, nullable=False)
    recent_articles_count = Column(Integer, default=0, nullable=False)  # Last 30 days
    first_article_date = Column(DateTime(timezone=True), nullable=True)
    last_article_date = Column(DateTime(timezone=True), nullable=True)
    
    # SEO and content analysis
    keywords = Column(JSON, nullable=True)  # Associated keywords for NLP
    trending_score = Column(Float, default=0.0, nullable=False)  # Calculated trending score
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint('name', 'site_id', name='uq_category_name_site'),
    )
    
    # Relationships
    site = relationship("Site", back_populates="categories")
    articles = relationship("Article", back_populates="category")
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', site_id={self.site_id}, articles={self.total_articles})>"
    
    @classmethod
    def get_or_create_by_name_and_site(cls, session, name: str, site_id: int, **kwargs):
        """Get existing category or create new one by name and site."""
        category = session.query(cls).filter_by(name=name, site_id=site_id).first()
        if not category:
            # Set display_name if not provided
            if 'display_name' not in kwargs:
                kwargs['display_name'] = name.title()
            
            category = cls(name=name, site_id=site_id, **kwargs)
            session.add(category)
            session.flush()  # Get the ID
        return category
    
    def update_hierarchy_path(self):
        """Update hierarchy path based on parent relationships."""
        if self.parent_id:
            parent_path = self.parent.hierarchy_path or self.parent.name
            self.hierarchy_path = f"{parent_path}/{self.name}"
            self.level = self.parent.level + 1
        else:
            self.hierarchy_path = self.name
            self.level = 0
    
    def update_article_stats(self, session):
        """Update category statistics based on articles."""
        from .articles import Article
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        articles_query = session.query(Article).filter_by(
            category_id=self.id,
            is_deleted=False
        )
        
        self.total_articles = articles_query.count()
        
        # Recent articles (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        self.recent_articles_count = articles_query.filter(
            Article.first_seen >= thirty_days_ago
        ).count()
        
        if self.total_articles > 0:
            first_article = articles_query.order_by(Article.first_seen.asc()).first()
            last_article = articles_query.order_by(Article.last_seen.desc()).first()
            
            self.first_article_date = first_article.first_seen
            self.last_article_date = last_article.last_seen
    
    def calculate_trending_score(self, session):
        """Calculate trending score based on recent activity."""
        from datetime import datetime, timedelta
        
        # Simple trending calculation: recent articles / total articles with time decay
        if self.total_articles == 0:
            self.trending_score = 0.0
            return
        
        # Weight recent articles more heavily
        recent_ratio = self.recent_articles_count / self.total_articles
        
        # Time decay based on last article
        if self.last_article_date:
            days_since_last = (datetime.utcnow() - self.last_article_date).days
            time_factor = max(0.1, 1.0 - (days_since_last / 30.0))  # Decay over 30 days
        else:
            time_factor = 0.1
        
        self.trending_score = recent_ratio * time_factor * 100  # Scale to 0-100
    
    @property
    def full_path(self) -> str:
        """Get the full category path for display."""
        return self.hierarchy_path or self.name