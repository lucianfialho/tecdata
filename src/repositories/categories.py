"""Category repository for managing article categories."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from .base import BaseRepository
from ..models.categories import Category


class CategoryRepository(BaseRepository[Category]):
    """Repository for Category model operations."""
    
    def __init__(self, session: Session):
        super().__init__(Category, session)
    
    def get_or_create_by_name_and_site(self, name: str, site_id: int, **kwargs) -> Category:
        """Get existing category or create new one."""
        return Category.get_or_create_by_name_and_site(self.session, name, site_id, **kwargs)
    
    def get_categories_by_site(self, site_id: int, active_only: bool = True) -> List[Category]:
        """Get categories for a specific site."""
        query = self.session.query(Category).filter(
            Category.site_id == site_id,
            Category.is_deleted == False
        )
        
        if active_only:
            query = query.filter(Category.is_active == True)
        
        return query.order_by(
            Category.sort_order.asc(),
            Category.name.asc()
        ).all()
    
    def get_root_categories(self, site_id: int) -> List[Category]:
        """Get top-level categories (no parent)."""
        return self.session.query(Category).filter(
            Category.site_id == site_id,
            Category.parent_id.is_(None),
            Category.is_active == True,
            Category.is_deleted == False
        ).order_by(Category.sort_order.asc()).all()
    
    def get_child_categories(self, parent_id: int) -> List[Category]:
        """Get child categories of a parent category."""
        return self.session.query(Category).filter(
            Category.parent_id == parent_id,
            Category.is_active == True,
            Category.is_deleted == False
        ).order_by(Category.sort_order.asc()).all()
    
    def get_category_hierarchy(self, site_id: int) -> List[Dict[str, Any]]:
        """Get complete category hierarchy for a site."""
        root_categories = self.get_root_categories(site_id)
        
        def build_hierarchy(category: Category) -> Dict[str, Any]:
            children = self.get_child_categories(category.id)
            
            return {
                'id': category.id,
                'name': category.name,
                'display_name': category.display_name,
                'level': category.level,
                'total_articles': category.total_articles,
                'recent_articles': category.recent_articles_count,
                'trending_score': category.trending_score,
                'children': [build_hierarchy(child) for child in children]
            }
        
        return [build_hierarchy(category) for category in root_categories]
    
    def get_trending_categories(self, site_id: int = None, days: int = 7, 
                              limit: int = 10) -> List[Category]:
        """Get trending categories based on recent activity."""
        query = self.session.query(Category).filter(
            Category.is_active == True,
            Category.is_deleted == False,
            Category.recent_articles_count > 0
        )
        
        if site_id:
            query = query.filter(Category.site_id == site_id)
        
        # Update trending scores first
        categories = query.all()
        for category in categories:
            category.calculate_trending_score(self.session)
        
        self.session.flush()
        
        # Return top trending
        return query.order_by(
            desc(Category.trending_score),
            desc(Category.recent_articles_count)
        ).limit(limit).all()
    
    def get_most_active_categories(self, site_id: int = None, limit: int = 20) -> List[Category]:
        """Get categories with the most articles."""
        query = self.session.query(Category).filter(
            Category.is_active == True,
            Category.is_deleted == False,
            Category.total_articles > 0
        )
        
        if site_id:
            query = query.filter(Category.site_id == site_id)
        
        return query.order_by(desc(Category.total_articles)).limit(limit).all()
    
    def search_categories(self, search_term: str, site_id: int = None) -> List[Category]:
        """Search categories by name or display name."""
        from sqlalchemy import or_
        
        query = self.session.query(Category).filter(
            or_(
                Category.name.ilike(f'%{search_term}%'),
                Category.display_name.ilike(f'%{search_term}%'),
                Category.description.ilike(f'%{search_term}%')
            ),
            Category.is_active == True,
            Category.is_deleted == False
        )
        
        if site_id:
            query = query.filter(Category.site_id == site_id)
        
        return query.order_by(desc(Category.total_articles)).all()
    
    def get_category_statistics(self, category_id: int, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive statistics for a category."""
        category = self.get_by_id(category_id)
        if not category:
            return {}
        
        from ..models.articles import Article
        
        # Get articles in this category
        articles = self.session.query(Article).filter(
            Article.category_id == category_id,
            Article.is_deleted == False
        ).all()
        
        if not articles:
            return {
                'category_name': category.name,
                'total_articles': 0,
                'active_articles': 0,
            }
        
        # Recent activity
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        recent_articles = len([a for a in articles if a.first_seen >= cutoff_time])
        
        # Quality metrics
        quality_scores = [a.quality_score for a in articles if a.quality_score > 0]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Content metrics
        word_counts = [a.word_count for a in articles if a.word_count]
        avg_word_count = sum(word_counts) / len(word_counts) if word_counts else 0
        total_words = sum(word_counts)
        
        # Author diversity
        unique_authors = len(set(a.author_id for a in articles if a.author_id))
        
        # Publication pattern
        publication_dates = [a.published_at for a in articles if a.published_at]
        if publication_dates:
            first_publication = min(publication_dates)
            last_publication = max(publication_dates)
        else:
            first_publication = None
            last_publication = None
        
        return {
            'category_name': category.name,
            'display_name': category.display_name,
            'category_id': category_id,
            'site_id': category.site_id,
            'level': category.level,
            'hierarchy_path': category.hierarchy_path,
            'total_articles': len(articles),
            'active_articles': len([a for a in articles if a.is_active]),
            'recent_articles': recent_articles,
            'trending_score': category.trending_score,
            'avg_quality_score': round(avg_quality, 2),
            'avg_word_count': round(avg_word_count, 0),
            'total_words': total_words,
            'unique_authors': unique_authors,
            'first_publication': first_publication,
            'last_publication': last_publication,
            'description': category.description,
        }
    
    def update_category_stats(self, category_id: int) -> Optional[Category]:
        """Update category statistics based on articles."""
        category = self.get_by_id(category_id)
        if not category:
            return None
        
        category.update_article_stats(self.session)
        category.calculate_trending_score(self.session)
        
        self.session.flush()
        return category
    
    def bulk_update_stats(self, site_id: int = None) -> int:
        """Update statistics for all categories."""
        query = self.session.query(Category).filter(Category.is_deleted == False)
        
        if site_id:
            query = query.filter(Category.site_id == site_id)
        
        categories = query.all()
        updated_count = 0
        
        for category in categories:
            category.update_article_stats(self.session)
            category.calculate_trending_score(self.session)
            updated_count += 1
        
        self.session.flush()
        return updated_count
    
    def get_category_timeline(self, category_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Get publication timeline for a category."""
        from ..models.articles import Article
        
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        articles = self.session.query(Article).filter(
            Article.category_id == category_id,
            Article.first_seen >= cutoff_time,
            Article.is_deleted == False
        ).order_by(Article.first_seen).all()
        
        # Group by day
        daily_counts = {}
        for article in articles:
            day = article.first_seen.date()
            if day not in daily_counts:
                daily_counts[day] = {
                    'articles': 0, 
                    'total_words': 0,
                    'authors': set()
                }
            
            daily_counts[day]['articles'] += 1
            daily_counts[day]['total_words'] += article.word_count or 0
            if article.author_id:
                daily_counts[day]['authors'].add(article.author_id)
        
        # Convert to timeline format
        timeline = []
        for day, stats in daily_counts.items():
            timeline.append({
                'date': day.isoformat(),
                'articles_published': stats['articles'],
                'total_words': stats['total_words'],
                'unique_authors': len(stats['authors']),
            })
        
        return sorted(timeline, key=lambda x: x['date'])
    
    def create_subcategory(self, parent_id: int, name: str, **kwargs) -> Optional[Category]:
        """Create a subcategory under a parent category."""
        parent = self.get_by_id(parent_id)
        if not parent:
            return None
        
        # Create the subcategory
        subcategory = self.create(
            name=name,
            site_id=parent.site_id,
            parent_id=parent_id,
            **kwargs
        )
        
        # Update hierarchy information
        subcategory.update_hierarchy_path()
        
        self.session.flush()
        return subcategory
    
    def move_category(self, category_id: int, new_parent_id: int = None) -> Optional[Category]:
        """Move a category to a different parent or make it root-level."""
        category = self.get_by_id(category_id)
        if not category:
            return None
        
        category.parent_id = new_parent_id
        category.update_hierarchy_path()
        
        # Update all child categories' hierarchy paths
        children = self.get_child_categories(category_id)
        for child in children:
            child.update_hierarchy_path()
        
        self.session.flush()
        return category
    
    def get_empty_categories(self, site_id: int = None) -> List[Category]:
        """Get categories with no articles."""
        query = self.session.query(Category).filter(
            Category.total_articles == 0,
            Category.is_deleted == False
        )
        
        if site_id:
            query = query.filter(Category.site_id == site_id)
        
        return query.all()