"""Article repository for managing processed articles."""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc, func
from .base import BaseRepository
from ..models.articles import Article
from ..models.article_history import ArticleHistory


class ArticleRepository(BaseRepository[Article]):
    """Repository for Article model operations."""
    
    def __init__(self, session: Session):
        super().__init__(Article, session)
    
    def create_article(self, external_id: str, site_id: int, title: str, 
                      url: str, **kwargs) -> Article:
        """Create a new article with required fields."""
        article = self.create(
            external_id=external_id,
            site_id=site_id,
            title=title,
            url=url,
            **kwargs
        )
        
        # Extract slug from URL if not provided
        if not article.slug:
            article.extract_slug_from_url()
        
        # Calculate reading time if word count is provided
        if article.word_count:
            article.calculate_reading_time()
        
        return article
    
    def find_by_external_id(self, external_id: str, site_id: int) -> Optional[Article]:
        """Find article by external ID and site."""
        return Article.find_by_external_id(self.session, external_id, site_id)
    
    def get_articles_by_site(self, site_id: int, limit: int = 50, 
                           include_inactive: bool = False) -> List[Article]:
        """Get articles for a specific site."""
        query = self.session.query(Article).filter(
            Article.site_id == site_id,
            Article.is_deleted == False
        )
        
        if not include_inactive:
            query = query.filter(Article.is_active == True)
        
        return query.order_by(desc(Article.first_seen)).limit(limit).all()
    
    def get_recent_articles(self, site_id: int = None, hours: int = 24, 
                          limit: int = 50) -> List[Article]:
        """Get recently discovered articles."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = self.session.query(Article).filter(
            Article.first_seen >= cutoff_time,
            Article.is_deleted == False,
            Article.is_active == True
        )
        
        if site_id:
            query = query.filter(Article.site_id == site_id)
        
        return query.order_by(desc(Article.first_seen)).limit(limit).all()
    
    def get_articles_by_author(self, author_id: int, limit: int = 50) -> List[Article]:
        """Get articles by a specific author."""
        return self.session.query(Article).filter(
            Article.author_id == author_id,
            Article.is_deleted == False,
            Article.is_active == True
        ).order_by(desc(Article.published_at)).limit(limit).all()
    
    def get_articles_by_category(self, category_id: int, limit: int = 50) -> List[Article]:
        """Get articles in a specific category."""
        return self.session.query(Article).filter(
            Article.category_id == category_id,
            Article.is_deleted == False,
            Article.is_active == True
        ).order_by(desc(Article.published_at)).limit(limit).all()
    
    def search_articles(self, search_term: str, site_id: int = None, 
                       limit: int = 50) -> List[Article]:
        """Search articles by title, summary, or content."""
        return self.search(search_term, ['title', 'summary', 'content_excerpt'], limit)
    
    def get_duplicate_articles(self, site_id: int = None) -> List[Article]:
        """Get articles marked as duplicates."""
        query = self.session.query(Article).filter(
            Article.is_duplicate == True,
            Article.is_deleted == False
        )
        
        if site_id:
            query = query.filter(Article.site_id == site_id)
        
        return query.order_by(desc(Article.first_seen)).all()
    
    def find_potential_duplicates(self, article: Article, similarity_threshold: float = 0.8) -> List[Article]:
        """Find potential duplicate articles based on title similarity."""
        # Simple implementation - in production, you might use more sophisticated methods
        words = set(article.title.lower().split())
        
        candidates = self.session.query(Article).filter(
            Article.site_id != article.site_id,  # Different sites
            Article.is_deleted == False,
            Article.is_active == True,
            Article.id != article.id
        ).all()
        
        potential_duplicates = []
        
        for candidate in candidates:
            candidate_words = set(candidate.title.lower().split())
            
            # Calculate Jaccard similarity
            intersection = len(words.intersection(candidate_words))
            union = len(words.union(candidate_words))
            
            if union > 0:
                similarity = intersection / union
                if similarity >= similarity_threshold:
                    potential_duplicates.append(candidate)
        
        return potential_duplicates
    
    def update_article_with_history(self, article_id: int, updates: Dict[str, Any], 
                                   change_source: str = 'collection') -> Optional[Article]:
        """Update article and track changes in history."""
        article = self.get_by_id(article_id)
        if not article:
            return None
        
        # Track changes before updating
        for field, new_value in updates.items():
            if hasattr(article, field):
                old_value = getattr(article, field)
                if old_value != new_value:
                    # Create history record
                    ArticleHistory.create_change_record(
                        self.session,
                        article_id=article_id,
                        field_name=field,
                        old_value=old_value,
                        new_value=new_value,
                        change_source=change_source
                    )
        
        # Update the article
        return self.update(article_id, **updates)
    
    def get_trending_articles(self, site_id: int = None, days: int = 7, 
                            limit: int = 20) -> List[Article]:
        """Get trending articles based on recent discovery and quality."""
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        query = self.session.query(Article).filter(
            Article.first_seen >= cutoff_time,
            Article.is_deleted == False,
            Article.is_active == True,
            Article.quality_score > 50  # Only high-quality articles
        )
        
        if site_id:
            query = query.filter(Article.site_id == site_id)
        
        # Order by quality score and recency
        return query.order_by(
            desc(Article.quality_score),
            desc(Article.first_seen)
        ).limit(limit).all()
    
    def get_article_statistics(self, site_id: int = None) -> Dict[str, Any]:
        """Get comprehensive article statistics."""
        query = self.session.query(Article).filter(Article.is_deleted == False)
        
        if site_id:
            query = query.filter(Article.site_id == site_id)
        
        articles = query.all()
        
        if not articles:
            return {}
        
        # Basic counts
        total_articles = len(articles)
        active_articles = len([a for a in articles if a.is_active])
        duplicate_articles = len([a for a in articles if a.is_duplicate])
        
        # Quality metrics
        quality_scores = [a.quality_score for a in articles if a.quality_score > 0]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Content metrics
        word_counts = [a.word_count for a in articles if a.word_count]
        avg_word_count = sum(word_counts) / len(word_counts) if word_counts else 0
        
        # Time-based metrics
        recent_articles = len([a for a in articles 
                             if a.first_seen >= datetime.utcnow() - timedelta(days=7)])
        
        # Author and category diversity
        unique_authors = len(set(a.author_id for a in articles if a.author_id))
        unique_categories = len(set(a.category_id for a in articles if a.category_id))
        
        return {
            'total_articles': total_articles,
            'active_articles': active_articles,
            'duplicate_articles': duplicate_articles,
            'duplicate_rate': (duplicate_articles / total_articles * 100) if total_articles > 0 else 0,
            'recent_articles_7d': recent_articles,
            'avg_quality_score': round(avg_quality, 2),
            'avg_word_count': round(avg_word_count, 0),
            'unique_authors': unique_authors,
            'unique_categories': unique_categories,
        }
    
    def get_content_timeline(self, site_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily article publication timeline."""
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        articles = self.session.query(Article).filter(
            Article.site_id == site_id,
            Article.first_seen >= cutoff_time,
            Article.is_deleted == False
        ).all()
        
        # Group by day
        daily_counts = {}
        for article in articles:
            day = article.first_seen.date()
            if day not in daily_counts:
                daily_counts[day] = {'new_articles': 0, 'total_words': 0}
            
            daily_counts[day]['new_articles'] += 1
            daily_counts[day]['total_words'] += article.word_count or 0
        
        # Convert to list and sort
        timeline = []
        for date, stats in daily_counts.items():
            timeline.append({
                'date': date.isoformat(),
                'new_articles': stats['new_articles'],
                'total_words': stats['total_words'],
                'avg_words_per_article': stats['total_words'] // stats['new_articles'] if stats['new_articles'] > 0 else 0
            })
        
        return sorted(timeline, key=lambda x: x['date'])
    
    def mark_as_duplicate(self, article_id: int, original_article_id: int) -> Optional[Article]:
        """Mark article as duplicate of another."""
        article = self.get_by_id(article_id)
        if not article:
            return None
        
        article.mark_as_duplicate(original_article_id)
        
        # Create history record
        ArticleHistory.create_change_record(
            self.session,
            article_id=article_id,
            field_name='duplicate_status',
            old_value='unique',
            new_value=f'duplicate_of_{original_article_id}',
            change_source='manual'
        )
        
        self.session.flush()
        return article
    
    def get_articles_with_relations(self, site_id: int, limit: int = 50) -> List[Article]:
        """Get articles with their related author and category data."""
        return self.session.query(Article).options(
            joinedload(Article.author),
            joinedload(Article.category),
            joinedload(Article.site)
        ).filter(
            Article.site_id == site_id,
            Article.is_deleted == False,
            Article.is_active == True
        ).order_by(desc(Article.first_seen)).limit(limit).all()