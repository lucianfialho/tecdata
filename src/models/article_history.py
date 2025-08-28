"""Article history model for tracking changes over time."""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey, Index, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class ArticleHistory(Base):
    """Model for tracking changes to articles over time."""
    
    __tablename__ = "article_history"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False, index=True)
    
    # What changed
    change_type = Column(String(50), nullable=False, index=True)  # title, summary, author, category, etc.
    field_name = Column(String(100), nullable=False)  # Specific field that changed
    old_value = Column(Text, nullable=True)  # Previous value
    new_value = Column(Text, nullable=True)  # New value
    
    # Change metadata
    change_timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    change_source = Column(String(100), nullable=False)  # 'collection', 'manual_edit', 'batch_update'
    change_reason = Column(String(200), nullable=True)  # Optional reason for change
    
    # Additional context
    snapshot_id = Column(Integer, ForeignKey("snapshots.id"), nullable=True, index=True)  # Link to snapshot that triggered change
    change_metadata = Column(JSON, nullable=True)  # Additional context data
    
    # Change significance
    is_significant = Column(Boolean, default=True, nullable=False, index=True)  # Filter minor changes
    confidence_score = Column(Float, nullable=True)  # How confident we are in this change
    
    # Table constraints for performance
    __table_args__ = (
        Index('idx_article_history_article_timestamp', 'article_id', 'change_timestamp'),
        Index('idx_article_history_type_timestamp', 'change_type', 'change_timestamp'),
    )
    
    # Relationships
    article = relationship("Article", back_populates="history")
    snapshot = relationship("Snapshot")
    
    def __repr__(self):
        return f"<ArticleHistory(id={self.id}, article_id={self.article_id}, type='{self.change_type}', field='{self.field_name}')>"
    
    @classmethod
    def create_change_record(cls, session, article_id: int, field_name: str, old_value, new_value, 
                           change_source: str = 'collection', **kwargs):
        """Create a new change record for an article field."""
        
        # Determine change type based on field name
        change_type_mapping = {
            'title': 'content',
            'summary': 'content', 
            'content_excerpt': 'content',
            'author_id': 'metadata',
            'category_id': 'metadata',
            'published_at': 'metadata',
            'image_url': 'media',
            'images': 'media',
            'tags': 'analysis',
            'keywords': 'analysis',
            'topics': 'analysis',
            'url': 'reference',
            'canonical_url': 'reference'
        }
        
        change_type = change_type_mapping.get(field_name, 'other')
        
        # Determine if change is significant
        is_significant = cls._is_change_significant(field_name, old_value, new_value)
        
        # Convert values to strings for storage
        old_str = str(old_value) if old_value is not None else None
        new_str = str(new_value) if new_value is not None else None
        
        history_record = cls(
            article_id=article_id,
            change_type=change_type,
            field_name=field_name,
            old_value=old_str,
            new_value=new_str,
            change_source=change_source,
            is_significant=is_significant,
            **kwargs
        )
        
        session.add(history_record)
        return history_record
    
    @staticmethod
    def _is_change_significant(field_name: str, old_value, new_value) -> bool:
        """Determine if a change is significant enough to track."""
        
        # Always track these fields
        significant_fields = {'title', 'author_id', 'category_id', 'published_at', 'url'}
        if field_name in significant_fields:
            return True
        
        # For text fields, check if change is substantial
        if field_name in {'summary', 'content_excerpt'}:
            if not old_value or not new_value:
                return True
            
            # Simple heuristic: significant if more than 10% different
            old_len = len(str(old_value))
            new_len = len(str(new_value))
            if old_len == 0:
                return new_len > 0
            
            length_diff = abs(old_len - new_len) / old_len
            return length_diff > 0.1
        
        # For other fields, any change is significant
        return old_value != new_value
    
    @classmethod
    def get_article_timeline(cls, session, article_id: int, limit: int = 50):
        """Get timeline of changes for an article."""
        return session.query(cls).filter_by(
            article_id=article_id
        ).order_by(
            cls.change_timestamp.desc()
        ).limit(limit).all()
    
    @classmethod
    def get_recent_changes(cls, session, hours: int = 24, change_types: list = None):
        """Get recent changes across all articles."""
        from datetime import datetime, timedelta
        
        query = session.query(cls).filter(
            cls.change_timestamp >= datetime.utcnow() - timedelta(hours=hours)
        )
        
        if change_types:
            query = query.filter(cls.change_type.in_(change_types))
        
        return query.order_by(cls.change_timestamp.desc()).all()
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the change."""
        summaries = {
            'content': f"Content updated: {self.field_name}",
            'metadata': f"Metadata changed: {self.field_name}",
            'media': f"Media updated: {self.field_name}",
            'analysis': f"Analysis updated: {self.field_name}",
            'reference': f"Reference updated: {self.field_name}"
        }
        
        return summaries.get(self.change_type, f"Field updated: {self.field_name}")