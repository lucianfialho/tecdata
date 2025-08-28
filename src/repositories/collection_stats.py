"""Collection statistics repository for managing aggregated metrics."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func
from .base import BaseRepository
from ..models.collection_stats import CollectionStats


class CollectionStatsRepository(BaseRepository[CollectionStats]):
    """Repository for CollectionStats model operations."""
    
    def __init__(self, session: Session):
        super().__init__(CollectionStats, session)
    
    def create_period_stats(self, site_id: int, period_start: datetime, 
                          period_end: datetime, period_type: str) -> CollectionStats:
        """Create statistics for a specific period."""
        return CollectionStats.create_period_stats(
            self.session, site_id, period_start, period_end, period_type
        )
    
    def get_latest_stats(self, site_id: int, period_type: str, 
                        limit: int = 10) -> List[CollectionStats]:
        """Get the most recent statistics for a site and period type."""
        return CollectionStats.get_latest_stats(self.session, site_id, period_type, limit)
    
    def get_stats_summary(self, site_id: int, days: int = 7) -> Optional[Dict[str, Any]]:
        """Get a summary of statistics for the last N days."""
        return CollectionStats.get_stats_summary(self.session, site_id, days)
    
    def get_stats_by_period(self, site_id: int, period_type: str, 
                           start_date: datetime = None, end_date: datetime = None) -> List[CollectionStats]:
        """Get statistics for a specific time range."""
        query = self.session.query(CollectionStats).filter(
            CollectionStats.site_id == site_id,
            CollectionStats.period_type == period_type
        )
        
        if start_date:
            query = query.filter(CollectionStats.period_start >= start_date)
        
        if end_date:
            query = query.filter(CollectionStats.period_end <= end_date)
        
        return query.order_by(asc(CollectionStats.period_start)).all()
    
    def get_performance_trends(self, site_id: int, days: int = 30) -> Dict[str, Any]:
        """Get performance trends over time."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        stats = self.get_stats_by_period(site_id, 'day', start_date, end_date)
        
        if not stats:
            return {}
        
        # Calculate trends
        success_rates = [s.success_rate for s in stats]
        response_times = [s.avg_response_time_ms for s in stats if s.avg_response_time_ms]
        quality_scores = [s.data_quality_score for s in stats if s.data_quality_score]
        article_counts = [s.new_articles_created for s in stats]
        
        # Calculate averages and trends
        avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        total_new_articles = sum(article_counts)
        
        # Calculate trend direction (simple linear regression slope)
        def calculate_trend(values: List[float]) -> str:
            if len(values) < 2:
                return 'stable'
            
            n = len(values)
            x_sum = sum(range(n))
            y_sum = sum(values)
            xy_sum = sum(i * values[i] for i in range(n))
            x2_sum = sum(i ** 2 for i in range(n))
            
            slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum ** 2)
            
            if slope > 0.1:
                return 'improving'
            elif slope < -0.1:
                return 'declining'
            else:
                return 'stable'
        
        return {
            'period_days': days,
            'total_periods': len(stats),
            'avg_success_rate': round(avg_success_rate, 2),
            'avg_response_time_ms': round(avg_response_time, 2),
            'avg_quality_score': round(avg_quality_score, 2),
            'total_new_articles': total_new_articles,
            'success_rate_trend': calculate_trend(success_rates),
            'response_time_trend': calculate_trend(response_times),
            'quality_trend': calculate_trend(quality_scores),
            'article_creation_trend': calculate_trend(article_counts),
        }
    
    def get_comparison_stats(self, site_ids: List[int], period_type: str = 'day', 
                           days: int = 7) -> Dict[int, Dict[str, Any]]:
        """Compare statistics across multiple sites."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        comparison = {}
        
        for site_id in site_ids:
            stats = self.get_stats_by_period(site_id, period_type, start_date, end_date)
            
            if not stats:
                comparison[site_id] = {'error': 'No data available'}
                continue
            
            # Aggregate metrics
            total_requests = sum(s.total_requests for s in stats)
            total_successful = sum(s.successful_requests for s in stats)
            total_articles = sum(s.new_articles_created for s in stats)
            
            response_times = [s.avg_response_time_ms for s in stats if s.avg_response_time_ms]
            quality_scores = [s.data_quality_score for s in stats if s.data_quality_score]
            
            comparison[site_id] = {
                'total_requests': total_requests,
                'success_rate': (total_successful / total_requests * 100) if total_requests > 0 else 0,
                'total_new_articles': total_articles,
                'avg_response_time_ms': sum(response_times) / len(response_times) if response_times else 0,
                'avg_quality_score': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
                'data_points': len(stats),
            }
        
        return comparison
    
    def get_hourly_patterns(self, site_id: int, days: int = 7) -> List[Dict[str, Any]]:
        """Get hourly collection patterns."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        stats = self.get_stats_by_period(site_id, 'hour', start_date, end_date)
        
        # Group by hour of day
        hourly_patterns = {}
        for stat in stats:
            hour = stat.period_start.hour
            if hour not in hourly_patterns:
                hourly_patterns[hour] = {
                    'requests': [],
                    'success_rates': [],
                    'response_times': [],
                    'new_articles': []
                }
            
            hourly_patterns[hour]['requests'].append(stat.total_requests)
            hourly_patterns[hour]['success_rates'].append(stat.success_rate)
            if stat.avg_response_time_ms:
                hourly_patterns[hour]['response_times'].append(stat.avg_response_time_ms)
            hourly_patterns[hour]['new_articles'].append(stat.new_articles_created)
        
        # Calculate averages for each hour
        patterns = []
        for hour in range(24):
            if hour in hourly_patterns:
                data = hourly_patterns[hour]
                patterns.append({
                    'hour': hour,
                    'avg_requests': sum(data['requests']) / len(data['requests']),
                    'avg_success_rate': sum(data['success_rates']) / len(data['success_rates']),
                    'avg_response_time': sum(data['response_times']) / len(data['response_times']) if data['response_times'] else 0,
                    'avg_new_articles': sum(data['new_articles']) / len(data['new_articles']),
                    'data_points': len(data['requests'])
                })
            else:
                patterns.append({
                    'hour': hour,
                    'avg_requests': 0,
                    'avg_success_rate': 0,
                    'avg_response_time': 0,
                    'avg_new_articles': 0,
                    'data_points': 0
                })
        
        return patterns
    
    def get_error_analysis(self, site_id: int, days: int = 30) -> Dict[str, Any]:
        """Analyze error patterns and types."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        stats = self.get_stats_by_period(site_id, 'day', start_date, end_date)
        
        if not stats:
            return {}
        
        # Aggregate error information
        total_requests = sum(s.total_requests for s in stats)
        total_errors = sum(s.failed_requests for s in stats)
        total_retries = sum(s.retry_count for s in stats)
        
        # Collect error types from JSON fields
        error_type_counts = {}
        for stat in stats:
            if stat.error_types:
                for error_type, count in stat.error_types.items():
                    error_type_counts[error_type] = error_type_counts.get(error_type, 0) + count
        
        # Find periods with high error rates
        high_error_periods = []
        for stat in stats:
            if stat.total_requests > 0:
                error_rate = (stat.failed_requests / stat.total_requests) * 100
                if error_rate > 20:  # More than 20% errors
                    high_error_periods.append({
                        'period_start': stat.period_start,
                        'error_rate': error_rate,
                        'failed_requests': stat.failed_requests,
                        'total_requests': stat.total_requests
                    })
        
        return {
            'period_days': days,
            'total_requests': total_requests,
            'total_errors': total_errors,
            'overall_error_rate': (total_errors / total_requests * 100) if total_requests > 0 else 0,
            'total_retries': total_retries,
            'error_type_breakdown': error_type_counts,
            'high_error_periods': high_error_periods,
            'avg_retries_per_day': total_retries / len(stats) if stats else 0,
        }
    
    def cleanup_old_stats(self, days_to_keep: int = 365) -> int:
        """Clean up old statistics, keeping only recent ones."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Count stats to be deleted
        count = self.session.query(CollectionStats).filter(
            CollectionStats.period_start < cutoff_date
        ).count()
        
        # Delete old stats
        self.session.query(CollectionStats).filter(
            CollectionStats.period_start < cutoff_date
        ).delete()
        
        return count
    
    def generate_missing_stats(self, site_id: int, period_type: str, 
                             start_date: datetime, end_date: datetime) -> int:
        """Generate statistics for missing periods."""
        from datetime import timedelta
        
        # Determine period increment
        if period_type == 'hour':
            increment = timedelta(hours=1)
        elif period_type == 'day':
            increment = timedelta(days=1)
        elif period_type == 'week':
            increment = timedelta(weeks=1)
        elif period_type == 'month':
            increment = timedelta(days=30)
        else:
            raise ValueError(f"Invalid period_type: {period_type}")
        
        created_count = 0
        current_date = start_date
        
        while current_date < end_date:
            period_end = current_date + increment
            
            # Check if stats already exist for this period
            existing = self.session.query(CollectionStats).filter(
                CollectionStats.site_id == site_id,
                CollectionStats.period_type == period_type,
                CollectionStats.period_start == current_date
            ).first()
            
            if not existing:
                # Create stats for this period
                stats = self.create_period_stats(site_id, current_date, period_end, period_type)
                if stats:
                    created_count += 1
            
            current_date = period_end
        
        return created_count