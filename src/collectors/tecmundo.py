"""Tecmundo API collector implementation with comprehensive data parsing and persistence."""

import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass
from urllib.parse import urlparse, urljoin

from config.settings import settings
from .base import BaseCollector
from src.utils.logger import get_logger
from src.utils.database import DatabaseManager
from src.repositories.sites import SiteRepository
from src.repositories.articles import ArticleRepository
from src.repositories.authors import AuthorRepository
from src.repositories.categories import CategoryRepository
from src.repositories.snapshots import SnapshotRepository
from src.repositories.collection_stats import CollectionStatsRepository

logger = get_logger(__name__)


@dataclass
class CollectionMetrics:
    """Metrics for a collection run."""
    start_time: datetime
    end_time: Optional[datetime] = None
    articles_found: int = 0
    articles_new: int = 0
    articles_updated: int = 0
    articles_skipped: int = 0
    errors: List[str] = None
    response_time_ms: int = 0
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    def duration_seconds(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


class TecmundoCollector(BaseCollector):
    """Advanced data collector for Tecmundo website with comprehensive parsing and persistence."""
    
    SITE_ID = "tecmundo"
    BASE_URL = "https://www.tecmundo.com.br"
    
    def __init__(self):
        super().__init__(site_id=self.SITE_ID)
        self.metrics = None
        self._site = None
        
    def get_api_url(self) -> str:
        """Get Tecmundo API URL."""
        return settings.api.tecmundo_full_url
    
    def collect_data(self) -> bool:
        """Enhanced collection with comprehensive metrics and persistence logic."""
        self.metrics = CollectionMetrics(start_time=datetime.now(timezone.utc))
        
        try:
            logger.info(f"Starting enhanced data collection for {self.site_id}")
            
            # Initialize repositories and site
            if not self._initialize_collection():
                return False
            
            # Make API request with detailed timing
            response_data = self._fetch_data()
            if not response_data:
                return False
            
            # Store raw snapshot first
            self._store_enhanced_snapshot(response_data)
            
            # Parse and process articles
            articles_data = self.parse_response(response_data)
            self._process_articles(articles_data)
            
            # Update collection statistics
            self._update_collection_stats()
            
            self.metrics.end_time = datetime.now(timezone.utc)
            
            logger.info(
                f"Collection completed for {self.site_id}: "
                f"{self.metrics.articles_new} new, {self.metrics.articles_updated} updated, "
                f"{self.metrics.articles_skipped} skipped in {self.metrics.duration_seconds():.2f}s"
            )
            
            return True
            
        except Exception as e:
            self._handle_collection_error(e)
            return False
    
    def _initialize_collection(self) -> bool:
        """Initialize database session and ensure site exists."""
        try:
            with DatabaseManager.get_session() as session:
                site_repo = SiteRepository(session)
                
                # Get or create site
                self._site = site_repo.get_by_site_id(self.SITE_ID)
                if not self._site:
                    logger.info(f"Creating new site record for {self.SITE_ID}")
                    self._site = site_repo.create_site(
                        name="Tecmundo",
                        site_id=self.SITE_ID,
                        base_url=self.BASE_URL,
                        api_endpoints={
                            "posts": settings.api.tecmundo_endpoint
                        },
                        description="Portal de tecnologia brasileiro",
                        category="technology",
                        country="BR",
                        language="pt-BR"
                    )
                    session.commit()
                
                if not self._site.is_active:
                    logger.warning(f"Site {self.SITE_ID} is inactive, skipping collection")
                    return False
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
            return False
    
    def _fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch data from API with enhanced error handling and metrics."""
        try:
            url = self.get_api_url()
            logger.debug(f"Fetching data from: {url}")
            
            start_time = time.time()
            response = self.http_client.get(url)
            self.metrics.response_time_ms = int((time.time() - start_time) * 1000)
            
            # Validate response
            if response.status_code != 200:
                error_msg = f"API returned status {response.status_code}"
                self.metrics.errors.append(error_msg)
                logger.error(error_msg)
                return None
            
            # Parse JSON
            try:
                data = response.json()
                logger.debug(f"Successfully parsed JSON response ({len(str(data))} chars)")
                return data
            except ValueError as e:
                error_msg = f"Invalid JSON response: {e}"
                self.metrics.errors.append(error_msg)
                logger.error(error_msg)
                return None
                
        except Exception as e:
            error_msg = f"Failed to fetch data: {e}"
            self.metrics.errors.append(error_msg)
            logger.error(error_msg)
            return None
    
    def _store_enhanced_snapshot(self, data: Dict[str, Any]):
        """Store snapshot with enhanced metadata."""
        try:
            with DatabaseManager.get_session() as session:
                snapshot_repo = SnapshotRepository(session)
                
                # Calculate data quality metrics
                quality_metrics = self._calculate_data_quality(data)
                
                snapshot = snapshot_repo.create(
                    site_id=self._site.site_id,
                    endpoint=self.get_api_url(),
                    raw_data=data,
                    response_status=200,
                    response_time_ms=self.metrics.response_time_ms,
                    articles_found=quality_metrics.get('articles_found', 0),
                    articles_valid=quality_metrics.get('articles_valid', 0),
                    data_quality_score=quality_metrics.get('quality_score', 0.0)
                )
                session.commit()
                logger.debug(f"Stored snapshot with ID: {snapshot.id}")
                
        except Exception as e:
            logger.error(f"Failed to store enhanced snapshot: {e}")
    
    def _calculate_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate data quality metrics from raw API response."""
        try:
            articles = self._extract_articles_list(data)
            articles_found = len(articles)
            
            if articles_found == 0:
                return {
                    'articles_found': 0,
                    'articles_valid': 0,
                    'quality_score': 0.0
                }
            
            # Count articles with required fields
            valid_articles = 0
            for article in articles:
                if self._has_required_fields(article):
                    valid_articles += 1
            
            quality_score = (valid_articles / articles_found) * 100
            
            return {
                'articles_found': articles_found,
                'articles_valid': valid_articles,
                'quality_score': round(quality_score, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate data quality: {e}")
            return {'articles_found': 0, 'articles_valid': 0, 'quality_score': 0.0}
    
    def _has_required_fields(self, article: Dict[str, Any]) -> bool:
        """Check if article has minimum required fields."""
        required_fields = ['id', 'title']
        for field in required_fields:
            if not self._extract_field(article, [field]):
                return False
        return True
    
    def parse_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Enhanced parsing with better error handling and data validation."""
        articles = []
        
        try:
            posts = self._extract_articles_list(data)
            self.metrics.articles_found = len(posts)
            
            logger.debug(f"Found {len(posts)} posts in response")
            
            for i, post in enumerate(posts):
                try:
                    article_data = self._parse_single_post(post)
                    if article_data:
                        articles.append(article_data)
                    else:
                        self.metrics.articles_skipped += 1
                        
                except Exception as e:
                    error_msg = f"Failed to parse post {i}: {e}"
                    logger.warning(error_msg)
                    self.metrics.errors.append(error_msg)
                    self.metrics.articles_skipped += 1
            
            logger.info(f"Successfully parsed {len(articles)} articles from {len(posts)} posts")
            
        except Exception as e:
            error_msg = f"Failed to parse Tecmundo response: {e}"
            logger.error(error_msg)
            self.metrics.errors.append(error_msg)
            
            if isinstance(data, dict):
                logger.debug(f"Available keys: {list(data.keys())[:10]}")
        
        return articles
    
    def _extract_articles_list(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract articles list from various possible response structures."""
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Try common keys for posts/articles
            for key in ['posts', 'articles', 'data', 'items', 'results', 'content']:
                if key in data and isinstance(data[key], list):
                    return data[key]
            
            # Check for nested structures
            for key, value in data.items():
                if isinstance(value, dict) and 'posts' in value:
                    return value['posts']
                elif isinstance(value, dict) and 'data' in value and isinstance(value['data'], list):
                    return value['data']
            
            # If no list found, maybe the whole dict is one post
            if 'title' in data or 'id' in data:
                return [data]
        
        return []
    
    def _parse_single_post(self, post: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Enhanced parsing of individual posts with better field extraction."""
        try:
            # Extract ID with more comprehensive search
            external_id = self._extract_external_id(post)
            if not external_id:
                logger.debug("No ID found in post, skipping")
                return None
            
            # Extract title with better handling
            title = self._extract_title(post)
            if not title:
                logger.debug(f"No title found for post {external_id}, skipping")
                return None
            
            # Extract other fields with enhanced logic
            article_data = {
                'external_id': external_id,
                'title': self._clean_text(title, max_length=500),
                'author': self._extract_author(post),
                'category': self._extract_category(post),
                'url': self._extract_url(post),
                'summary': self._extract_summary(post),
                'image_url': self._extract_image_url(post),
                'published_at': self._extract_published_date(post),
                'word_count': self._estimate_word_count(post),
                'raw_data': post  # Store original for debugging
            }
            
            # Validate and normalize URL
            article_data['url'] = self._normalize_url(article_data['url'])
            
            logger.debug(f"Parsed article: {title[:50]}...")
            return article_data
            
        except Exception as e:
            logger.error(f"Failed to parse single post: {e}")
            return None
    
    def _extract_external_id(self, post: Dict[str, Any]) -> Optional[str]:
        """Extract external ID with comprehensive field checking."""
        id_fields = ['id', 'post_id', 'ID', 'guid', 'slug', 'permalink', 'url']
        
        for field in id_fields:
            value = self._extract_field(post, [field])
            if value:
                # Clean and validate ID
                clean_id = str(value).strip()
                if clean_id:
                    # Extract ID from URL if necessary
                    if field in ['url', 'permalink', 'guid'] and '/' in clean_id:
                        url_parts = clean_id.rstrip('/').split('/')
                        clean_id = url_parts[-1] if url_parts[-1] else url_parts[-2]
                    return clean_id
        return None
    
    def _extract_title(self, post: Dict[str, Any]) -> Optional[str]:
        """Extract title with better nested object handling."""
        title_fields = ['title', 'post_title', 'name', 'headline', 'subject']
        
        for field in title_fields:
            if field in post:
                value = post[field]
                
                if isinstance(value, dict):
                    # Handle WordPress-style nested objects
                    for key in ['rendered', 'raw', 'plain', 'value']:
                        if key in value and value[key]:
                            return str(value[key]).strip()
                elif isinstance(value, str) and value.strip():
                    return value.strip()
                elif value:
                    return str(value).strip()
        
        return None
    
    def _extract_author(self, post: Dict[str, Any]) -> Optional[str]:
        """Extract author with enhanced field checking."""
        author_fields = [
            'author', 'post_author', 'author_name', 'by', 'created_by',
            'writer', 'journalist', 'redator'
        ]
        
        for field in author_fields:
            value = self._extract_field(post, [field])
            if value:
                # Handle author objects
                if isinstance(post.get(field), dict):
                    author_obj = post[field]
                    for key in ['name', 'display_name', 'nickname', 'login']:
                        if key in author_obj and author_obj[key]:
                            return str(author_obj[key]).strip()
                return str(value).strip()
        
        return None
    
    def _extract_category(self, post: Dict[str, Any]) -> Optional[str]:
        """Extract category with comprehensive field mapping."""
        category_fields = [
            'category', 'categories', 'tag', 'tags', 'section', 'channel',
            'topic', 'subject', 'type', 'content_type'
        ]
        
        for field in category_fields:
            value = self._extract_field(post, [field])
            if value:
                # Handle category arrays or objects
                if isinstance(post.get(field), list) and post[field]:
                    first_cat = post[field][0]
                    if isinstance(first_cat, dict):
                        return str(first_cat.get('name', first_cat.get('title', first_cat))).strip()
                    return str(first_cat).strip()
                elif isinstance(post.get(field), dict):
                    cat_obj = post[field]
                    for key in ['name', 'title', 'label', 'slug']:
                        if key in cat_obj and cat_obj[key]:
                            return str(cat_obj[key]).strip()
                return str(value).strip()
        
        return "Tecnologia"  # Default category
    
    def _extract_url(self, post: Dict[str, Any]) -> Optional[str]:
        """Extract URL with validation and normalization."""
        url_fields = ['url', 'link', 'permalink', 'guid', 'href']
        
        for field in url_fields:
            value = self._extract_field(post, [field])
            if value:
                url = str(value).strip()
                if url.startswith(('http://', 'https://')):
                    return url
                elif url.startswith('/'):
                    return urljoin(self.BASE_URL, url)
        
        return None
    
    def _extract_summary(self, post: Dict[str, Any]) -> Optional[str]:
        """Extract summary/excerpt with length limits."""
        summary_fields = [
            'summary', 'excerpt', 'description', 'content', 'lead',
            'subtitle', 'abstract', 'preview'
        ]
        
        for field in summary_fields:
            value = self._extract_field(post, [field])
            if value:
                summary = str(value).strip()
                # Clean HTML tags if present
                import re
                summary = re.sub(r'<[^>]+>', '', summary)
                summary = re.sub(r'\s+', ' ', summary).strip()
                
                if len(summary) > 10:  # Minimum meaningful length
                    return self._clean_text(summary, max_length=1000)
        
        return None
    
    def _extract_image_url(self, post: Dict[str, Any]) -> Optional[str]:
        """Extract image URL with comprehensive field checking."""
        image_fields = [
            'image', 'featured_image', 'thumbnail', 'cover_image', 'picture',
            'photo', 'media', 'featured_media'
        ]
        
        for field in image_fields:
            value = self._extract_field(post, [field])
            if value:
                if isinstance(post.get(field), dict):
                    img_obj = post[field]
                    for key in ['url', 'src', 'source_url', 'link', 'href']:
                        if key in img_obj and img_obj[key]:
                            url = str(img_obj[key]).strip()
                            if self._is_valid_image_url(url):
                                return self._normalize_url(url)
                else:
                    url = str(value).strip()
                    if self._is_valid_image_url(url):
                        return self._normalize_url(url)
        
        return None
    
    def _extract_published_date(self, post: Dict[str, Any]) -> Optional[datetime]:
        """Extract published date with various format handling."""
        date_fields = [
            'published_at', 'date', 'created_at', 'publication_date',
            'post_date', 'publish_date', 'timestamp'
        ]
        
        for field in date_fields:
            value = self._extract_field(post, [field])
            if value:
                try:
                    # Handle different date formats
                    from dateutil.parser import parse
                    return parse(str(value))
                except:
                    continue
        
        # Fallback to current time if no date found
        return datetime.now(timezone.utc)
    
    def _estimate_word_count(self, post: Dict[str, Any]) -> Optional[int]:
        """Estimate word count from available content."""
        content_fields = ['content', 'body', 'text', 'summary', 'excerpt']
        
        total_words = 0
        for field in content_fields:
            value = self._extract_field(post, [field])
            if value:
                # Simple word count estimation
                import re
                text = re.sub(r'<[^>]+>', '', str(value))  # Remove HTML
                words = len(re.findall(r'\b\w+\b', text))
                total_words += words
        
        return total_words if total_words > 0 else None
    
    def _is_valid_image_url(self, url: str) -> bool:
        """Check if URL looks like a valid image URL."""
        if not url or not isinstance(url, str):
            return False
        
        # Check for image extensions
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
        url_lower = url.lower()
        
        # Direct extension check
        if any(url_lower.endswith(ext) for ext in image_extensions):
            return True
        
        # Check for image indicators in URL
        image_indicators = ['image', 'img', 'photo', 'pic', 'thumb']
        if any(indicator in url_lower for indicator in image_indicators):
            return True
        
        return False
    
    def _normalize_url(self, url: Optional[str]) -> Optional[str]:
        """Normalize URL to absolute form."""
        if not url:
            return None
        
        url = url.strip()
        
        # Already absolute
        if url.startswith(('http://', 'https://')):
            return url
        
        # Relative URL
        if url.startswith('/'):
            return urljoin(self.BASE_URL, url)
        
        # Protocol-relative URL
        if url.startswith('//'):
            return 'https:' + url
        
        return url
    
    def _clean_text(self, text: str, max_length: int = None) -> str:
        """Clean and normalize text content."""
        if not text:
            return text
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Truncate if necessary
        if max_length and len(text) > max_length:
            text = text[:max_length - 3] + "..."
        
        return text
    
    def _process_articles(self, articles_data: List[Dict[str, Any]]):
        """Process parsed articles with comprehensive persistence logic."""
        if not articles_data:
            logger.warning("No articles to process")
            return
        
        try:
            with DatabaseManager.get_session() as session:
                # Initialize repositories
                article_repo = ArticleRepository(session)
                author_repo = AuthorRepository(session)
                category_repo = CategoryRepository(session)
                
                for article_data in articles_data:
                    try:
                        self._process_single_article(
                            article_data, article_repo, author_repo, category_repo
                        )
                    except Exception as e:
                        error_msg = f"Failed to process article {article_data.get('external_id')}: {e}"
                        logger.error(error_msg)
                        self.metrics.errors.append(error_msg)
                        self.metrics.articles_skipped += 1
                
                # Commit all changes
                session.commit()
                logger.info(
                    f"Processed {self.metrics.articles_new} new and "
                    f"{self.metrics.articles_updated} updated articles"
                )
                
        except Exception as e:
            logger.error(f"Failed to process articles: {e}")
            self.metrics.errors.append(f"Article processing failed: {e}")
    
    def _process_single_article(
        self,
        article_data: Dict[str, Any],
        article_repo: ArticleRepository,
        author_repo: AuthorRepository,
        category_repo: CategoryRepository
    ):
        """Process a single article with full normalization and relationship handling."""
        
        # Check if article already exists
        existing_article = article_repo.find_by_external_id(
            article_data['external_id'], self._site.id
        )
        
        # Get or create author
        author_id = None
        if article_data.get('author'):
            author = author_repo.get_or_create_by_name_and_site(
                article_data['author'], self._site.id
            )
            author_id = author.id
        
        # Get or create category
        category_id = None
        if article_data.get('category'):
            category = category_repo.get_or_create_by_name_and_site(
                article_data['category'], self._site.id
            )
            category_id = category.id
        
        # Calculate quality score
        quality_score = self._calculate_article_quality(article_data)
        
        if existing_article:
            # Update existing article
            updates = {
                'last_seen': datetime.now(timezone.utc),
                'title': article_data['title'],
                'summary': article_data.get('summary'),
                'url': article_data.get('url'),
                'image_url': article_data.get('image_url'),
                'author_id': author_id,
                'category_id': category_id,
                'word_count': article_data.get('word_count'),
                'quality_score': quality_score,
                'raw_data': article_data.get('raw_data')
            }
            
            # Only update if there are actual changes
            has_changes = False
            for field, new_value in updates.items():
                if field == 'last_seen':  # Always update last_seen
                    has_changes = True
                    continue
                current_value = getattr(existing_article, field)
                if current_value != new_value:
                    has_changes = True
                    break
            
            if has_changes:
                article_repo.update_article_with_history(
                    existing_article.id, updates, change_source='collection'
                )
                self.metrics.articles_updated += 1
            else:
                # Just update last_seen
                existing_article.update_last_seen()
                
        else:
            # Create new article
            article = article_repo.create_article(
                external_id=article_data['external_id'],
                site_id=self._site.id,
                title=article_data['title'],
                url=article_data.get('url'),
                summary=article_data.get('summary'),
                image_url=article_data.get('image_url'),
                author_id=author_id,
                category_id=category_id,
                published_at=article_data.get('published_at'),
                word_count=article_data.get('word_count'),
                quality_score=quality_score,
                raw_data=article_data.get('raw_data')
            )
            self.metrics.articles_new += 1
    
    def _calculate_article_quality(self, article_data: Dict[str, Any]) -> float:
        """Calculate quality score for an article based on available data."""
        score = 0.0
        
        # Required fields (40 points)
        if article_data.get('title'):
            score += 20
        if article_data.get('external_id'):
            score += 20
        
        # Important fields (30 points)
        if article_data.get('author'):
            score += 10
        if article_data.get('category'):
            score += 10
        if article_data.get('url'):
            score += 10
        
        # Additional content (30 points)
        if article_data.get('summary'):
            score += 10
        if article_data.get('image_url'):
            score += 10
        if article_data.get('published_at'):
            score += 5
        if article_data.get('word_count', 0) > 50:
            score += 5
        
        return min(score, 100.0)  # Cap at 100
    
    def _update_collection_stats(self):
        """Update collection statistics for monitoring and analysis."""
        try:
            with DatabaseManager.get_session() as session:
                stats_repo = CollectionStatsRepository(session)
                
                # Create collection stats record
                stats_repo.create(
                    site_id=self._site.site_id,
                    collection_date=self.metrics.start_time.date(),
                    articles_found=self.metrics.articles_found,
                    articles_new=self.metrics.articles_new,
                    articles_updated=self.metrics.articles_updated,
                    articles_skipped=self.metrics.articles_skipped,
                    response_time_ms=self.metrics.response_time_ms,
                    success=len(self.metrics.errors) == 0,
                    error_count=len(self.metrics.errors),
                    errors=self.metrics.errors if self.metrics.errors else None
                )
                
                session.commit()
                logger.debug("Updated collection statistics")
                
        except Exception as e:
            logger.error(f"Failed to update collection stats: {e}")
    
    def _handle_collection_error(self, error: Exception):
        """Handle collection errors with proper logging and metrics."""
        self.metrics.end_time = datetime.now(timezone.utc)
        error_msg = f"Collection failed: {error}"
        self.metrics.errors.append(error_msg)
        
        logger.error(error_msg)
        
        # Update site error count
        try:
            with DatabaseManager.get_session() as session:
                site_repo = SiteRepository(session)
                site_repo.update_collection_status(
                    self.SITE_ID, success=False, error_message=str(error)
                )
                session.commit()
        except Exception as e:
            logger.error(f"Failed to update site status: {e}")
    
    def _extract_field(self, post: Dict[str, Any], field_names: List[str]) -> Optional[str]:
        """Enhanced field extraction with better type handling."""
        for field_name in field_names:
            if field_name in post:
                value = post[field_name]
                
                # Handle different value types
                if isinstance(value, dict):
                    # Try common nested keys
                    for nested_key in ['rendered', 'raw', 'value', 'name', 'title', 'plain']:
                        if nested_key in value and value[nested_key]:
                            result = str(value[nested_key]).strip()
                            if result:
                                return result
                elif isinstance(value, list) and value:
                    # Take first non-empty item from list
                    for item in value:
                        if isinstance(item, dict):
                            for key in ['name', 'title', 'value', 'label']:
                                if key in item and item[key]:
                                    result = str(item[key]).strip()
                                    if result:
                                        return result
                        elif item:
                            result = str(item).strip()
                            if result:
                                return result
                elif value:
                    result = str(value).strip()
                    if result:
                        return result
        
        return None
    
    def get_collection_metrics(self) -> Optional[CollectionMetrics]:
        """Get metrics from the last collection run."""
        return self.metrics