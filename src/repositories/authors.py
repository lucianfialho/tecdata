"""Author repository for managing article authors."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from .base import BaseRepository
from ..models.authors import Author


class AuthorRepository(BaseRepository[Author]):
    """Repository for Author model operations."""
    
    def __init__(self, session: Session):
        super().__init__(Author, session)
    
    def get_or_create_by_name_and_site(self, name: str, site_id: int, **kwargs) -> Author:
        """Get existing author or create new one."""
        return Author.get_or_create_by_name_and_site(self.session, name, site_id, **kwargs)
    
    def get_authors_by_site(self, site_id: int, limit: int = 50) -> List[Author]:
        """Get authors for a specific site."""
        return self.session.query(Author).filter(
            Author.site_id == site_id,
            Author.is_deleted == False
        ).order_by(desc(Author.total_articles)).limit(limit).all()
    
    def get_most_active_authors(self, site_id: int = None, days: int = 30, 
                               limit: int = 20) -> List[Author]:
        """Get most active authors by recent article count."""
        from ..models.articles import Article
        
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        # Subquery to count recent articles per author
        recent_article_counts = self.session.query(
            Article.author_id,
            func.count(Article.id).label('recent_count')
        ).filter(
            Article.first_seen >= cutoff_time,
            Article.is_deleted == False,
            Article.is_active == True
        ).group_by(Article.author_id).subquery()
        
        # Join with authors and order by recent activity
        query = self.session.query(Author).join(
            recent_article_counts, 
            Author.id == recent_article_counts.c.author_id
        ).filter(Author.is_deleted == False)
        
        if site_id:
            query = query.filter(Author.site_id == site_id)
        
        return query.order_by(
            desc(recent_article_counts.c.recent_count)
        ).limit(limit).all()
    
    def get_author_statistics(self, author_id: int) -> Dict[str, Any]:
        """Get comprehensive statistics for an author."""
        author = self.get_by_id(author_id)
        if not author:
            return {}
        
        from ..models.articles import Article
        
        # Get all articles by this author
        articles = self.session.query(Article).filter(
            Article.author_id == author_id,
            Article.is_deleted == False
        ).all()
        
        if not articles:
            return {
                'author_name': author.name,
                'total_articles': 0,
                'active_articles': 0,
            }
        
        # Calculate metrics
        active_articles = len([a for a in articles if a.is_active])
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_articles = len([a for a in articles if a.first_seen >= thirty_days_ago])
        
        # Quality metrics
        quality_scores = [a.quality_score for a in articles if a.quality_score > 0]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Content metrics
        word_counts = [a.word_count for a in articles if a.word_count]
        avg_word_count = sum(word_counts) / len(word_counts) if word_counts else 0
        total_words = sum(word_counts)
        
        # Category diversity
        unique_categories = len(set(a.category_id for a in articles if a.category_id))
        
        # Publication pattern
        publication_dates = [a.published_at for a in articles if a.published_at]
        if publication_dates:
            first_publication = min(publication_dates)
            last_publication = max(publication_dates)
            days_active = (last_publication - first_publication).days
            avg_articles_per_week = (len(articles) / (days_active / 7)) if days_active > 0 else 0
        else:
            first_publication = None
            last_publication = None
            avg_articles_per_week = 0
        
        return {
            'author_name': author.name,
            'author_id': author_id,
            'site_id': author.site_id,
            'total_articles': len(articles),
            'active_articles': active_articles,
            'recent_articles_30d': recent_articles,
            'avg_quality_score': round(avg_quality, 2),
            'avg_word_count': round(avg_word_count, 0),
            'total_words_written': total_words,
            'unique_categories': unique_categories,
            'first_publication': first_publication,
            'last_publication': last_publication,
            'avg_articles_per_week': round(avg_articles_per_week, 2),
            'bio': author.bio,
            'profile_url': author.profile_url,
        }
    
    def search_authors(self, search_term: str, site_id: int = None, 
                      limit: int = 20) -> List[Author]:
        """Search authors by name."""
        query = self.session.query(Author).filter(
            Author.name.ilike(f'%{search_term}%'),
            Author.is_deleted == False
        )
        
        if site_id:
            query = query.filter(Author.site_id == site_id)
        
        return query.order_by(desc(Author.total_articles)).limit(limit).all()
    
    def get_prolific_authors(self, site_id: int = None, min_articles: int = 10) -> List[Author]:
        """Get authors with many articles."""
        query = self.session.query(Author).filter(
            Author.total_articles >= min_articles,
            Author.is_deleted == False
        )
        
        if site_id:
            query = query.filter(Author.site_id == site_id)
        
        return query.order_by(desc(Author.total_articles)).all()
    
    def update_author_stats(self, author_id: int) -> Optional[Author]:
        """Update author statistics based on their articles."""
        author = self.get_by_id(author_id)
        if not author:
            return None
        
        author.update_article_stats(self.session)
        self.session.flush()
        return author
    
    def bulk_update_stats(self, site_id: int = None) -> int:
        """Update statistics for all authors."""
        query = self.session.query(Author).filter(Author.is_deleted == False)
        
        if site_id:
            query = query.filter(Author.site_id == site_id)
        
        authors = query.all()
        updated_count = 0
        
        for author in authors:
            author.update_article_stats(self.session)
            updated_count += 1
        
        self.session.flush()
        return updated_count
    
    def get_author_timeline(self, author_id: int, days: int = 90) -> List[Dict[str, Any]]:
        """Get publication timeline for an author."""
        from ..models.articles import Article
        
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        articles = self.session.query(Article).filter(
            Article.author_id == author_id,
            Article.first_seen >= cutoff_time,
            Article.is_deleted == False
        ).order_by(Article.first_seen).all()
        
        # Group by week
        weekly_counts = {}
        for article in articles:
            # Get the start of the week (Monday)
            week_start = article.first_seen - timedelta(days=article.first_seen.weekday())
            week_key = week_start.date()
            
            if week_key not in weekly_counts:
                weekly_counts[week_key] = {
                    'articles': 0, 
                    'total_words': 0,
                    'categories': set()
                }
            
            weekly_counts[week_key]['articles'] += 1
            weekly_counts[week_key]['total_words'] += article.word_count or 0
            if article.category_id:
                weekly_counts[week_key]['categories'].add(article.category_id)
        
        # Convert to timeline format
        timeline = []
        for week_start, stats in weekly_counts.items():
            timeline.append({
                'week_start': week_start.isoformat(),
                'articles_published': stats['articles'],
                'total_words': stats['total_words'],
                'categories_covered': len(stats['categories']),
            })
        
        return sorted(timeline, key=lambda x: x['week_start'])
    
    def get_author_collaborations(self, author_id: int) -> List[Dict[str, Any]]:
        """Find other authors who write about similar topics."""
        from ..models.articles import Article
        
        author = self.get_by_id(author_id)
        if not author:
            return []
        
        # Get categories this author writes about
        author_categories = self.session.query(Article.category_id).filter(
            Article.author_id == author_id,
            Article.category_id.isnot(None),
            Article.is_deleted == False
        ).distinct().subquery()
        
        # Find other authors writing in the same categories
        similar_authors = self.session.query(
            Author,
            func.count(Article.id).label('shared_articles')
        ).join(Article).filter(
            Author.id != author_id,
            Author.site_id == author.site_id,  # Same site
            Author.is_deleted == False,
            Article.category_id.in_(author_categories),
            Article.is_deleted == False
        ).group_by(Author.id).order_by(
            desc('shared_articles')
        ).limit(10).all()
        
        collaborations = []
        for similar_author, shared_count in similar_authors:
            collaborations.append({
                'author_id': similar_author.id,
                'author_name': similar_author.name,
                'shared_category_articles': shared_count,
                'total_articles': similar_author.total_articles,
            })
        
        return collaborations