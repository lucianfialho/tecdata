"""Database models for Termômetro de Tecnologia."""

from .base import Base
from .sites import Site
from .authors import Author
from .categories import Category
from .articles import Article
from .article_history import ArticleHistory
from .snapshots import Snapshot
from .collection_stats import CollectionStats

# Keep old import for backward compatibility
from .site_analytics import SiteAnalytics

__all__ = [
    "Base",
    "Site", 
    "Author",
    "Category",
    "Article",
    "ArticleHistory",
    "Snapshot",
    "CollectionStats",
    "SiteAnalytics",  # Legacy
]