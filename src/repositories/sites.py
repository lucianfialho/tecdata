"""Site repository for managing technology sites."""

from typing import List, Optional
from sqlalchemy.orm import Session
from .base import BaseRepository
from ..models.sites import Site


class SiteRepository(BaseRepository[Site]):
    """Repository for Site model operations."""
    
    def __init__(self, session: Session):
        super().__init__(Site, session)
    
    def get_by_site_id(self, site_id: str) -> Optional[Site]:
        """Get site by site_id."""
        return self.get_by_field('site_id', site_id)
    
    def get_active_sites(self) -> List[Site]:
        """Get all active sites."""
        return self.session.query(Site).filter(
            Site.is_active == True,
            Site.is_deleted == False
        ).all()
    
    def get_sites_by_category(self, category: str) -> List[Site]:
        """Get sites by category."""
        return self.get_many_by_field('category', category)
    
    def get_sites_by_country(self, country: str = 'BR') -> List[Site]:
        """Get sites by country."""
        return self.get_many_by_field('country', country)
    
    def get_unhealthy_sites(self) -> List[Site]:
        """Get sites with high error counts."""
        return self.session.query(Site).filter(
            Site.collection_error_count >= 5,
            Site.is_active == True,
            Site.is_deleted == False
        ).all()
    
    def create_site(self, name: str, site_id: str, base_url: str, 
                   api_endpoints: dict, **kwargs) -> Site:
        """Create a new site with required fields."""
        return self.create(
            name=name,
            site_id=site_id,
            base_url=base_url,
            api_endpoints=api_endpoints,
            **kwargs
        )
    
    def update_collection_status(self, site_id: str, success: bool, 
                               error_message: str = None) -> Optional[Site]:
        """Update site collection status."""
        site = self.get_by_site_id(site_id)
        if not site:
            return None
        
        if success:
            site.reset_error_count()
        else:
            site.increment_error_count()
        
        # Disable site if too many consecutive errors
        if site.collection_error_count >= 10:
            site.is_active = False
        
        self.session.flush()
        return site
    
    def toggle_site_status(self, site_id: str, active: bool) -> Optional[Site]:
        """Enable or disable a site."""
        site = self.get_by_site_id(site_id)
        if not site:
            return None
        
        site.is_active = active
        if active:
            site.collection_error_count = 0  # Reset errors when reactivating
        
        self.session.flush()
        return site
    
    def get_site_statistics(self, site_id: str) -> dict:
        """Get comprehensive statistics for a site."""
        site = self.get_by_site_id(site_id)
        if not site:
            return {}
        
        from ..models.articles import Article
        from ..models.snapshots import Snapshot
        from datetime import datetime, timedelta
        
        # Get counts
        total_articles = self.session.query(Article).filter_by(
            site_id=site.id, is_deleted=False
        ).count()
        
        total_snapshots = self.session.query(Snapshot).filter_by(
            site_id=site.id
        ).count()
        
        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_articles = self.session.query(Article).filter(
            Article.site_id == site.id,
            Article.first_seen >= week_ago,
            Article.is_deleted == False
        ).count()
        
        recent_snapshots = self.session.query(Snapshot).filter(
            Snapshot.site_id == site.id,
            Snapshot.timestamp >= week_ago
        ).count()
        
        # Success rate (last 100 snapshots)
        recent_snapshots_query = self.session.query(Snapshot).filter(
            Snapshot.site_id == site.id
        ).order_by(Snapshot.timestamp.desc()).limit(100)
        
        successful_snapshots = sum(
            1 for s in recent_snapshots_query if s.is_successful
        )
        total_recent = recent_snapshots_query.count()
        success_rate = (successful_snapshots / total_recent * 100) if total_recent > 0 else 0
        
        return {
            'site_name': site.name,
            'site_id': site.site_id,
            'is_active': site.is_active,
            'is_healthy': site.is_healthy,
            'total_articles': total_articles,
            'total_snapshots': total_snapshots,
            'recent_articles': recent_articles,
            'recent_snapshots': recent_snapshots,
            'success_rate': success_rate,
            'error_count': site.collection_error_count,
            'last_successful_collection': site.last_successful_collection,
        }