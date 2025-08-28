"""Snapshot repository for managing API snapshots."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from .base import BaseRepository
from ..models.snapshots import Snapshot


class SnapshotRepository(BaseRepository[Snapshot]):
    """Repository for Snapshot model operations."""
    
    def __init__(self, session: Session):
        super().__init__(Snapshot, session)
    
    def create_snapshot(self, site_id: int, endpoint: str, response_status: int,
                       raw_data: dict, **kwargs) -> Snapshot:
        """Create a new snapshot with required fields."""
        return self.create(
            site_id=site_id,
            endpoint=endpoint,
            response_status=response_status,
            raw_data=raw_data,
            **kwargs
        )
    
    def get_latest_successful(self, site_id: int, endpoint: str) -> Optional[Snapshot]:
        """Get the most recent successful snapshot for a site/endpoint."""
        return Snapshot.get_latest_successful_snapshot(self.session, site_id, endpoint)
    
    def get_recent_snapshots(self, site_id: int, hours: int = 24, limit: int = 50) -> List[Snapshot]:
        """Get recent snapshots for a site."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return self.session.query(Snapshot).filter(
            Snapshot.site_id == site_id,
            Snapshot.timestamp >= cutoff_time
        ).order_by(desc(Snapshot.timestamp)).limit(limit).all()
    
    def get_error_snapshots(self, site_id: int, hours: int = 24) -> List[Snapshot]:
        """Get recent error snapshots for a site."""
        return Snapshot.get_error_snapshots(self.session, site_id, hours)
    
    def get_snapshots_by_batch(self, batch_id: str) -> List[Snapshot]:
        """Get all snapshots from a collection batch."""
        return self.get_many_by_field('collection_batch_id', batch_id)
    
    def get_snapshots_by_endpoint(self, site_id: int, endpoint: str, 
                                 limit: int = 50) -> List[Snapshot]:
        """Get snapshots for a specific endpoint."""
        return self.session.query(Snapshot).filter(
            Snapshot.site_id == site_id,
            Snapshot.endpoint == endpoint
        ).order_by(desc(Snapshot.timestamp)).limit(limit).all()
    
    def get_performance_metrics(self, site_id: int, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics for a site."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        snapshots = self.session.query(Snapshot).filter(
            Snapshot.site_id == site_id,
            Snapshot.timestamp >= cutoff_time
        ).all()
        
        if not snapshots:
            return {}
        
        # Calculate metrics
        total_requests = len(snapshots)
        successful_requests = len([s for s in snapshots if s.is_successful])
        failed_requests = total_requests - successful_requests
        
        # Response time metrics
        response_times = [s.response_time_ms for s in snapshots if s.response_time_ms]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        
        # Data quality metrics
        quality_scores = [s.data_quality_score for s in snapshots if s.data_quality_score]
        avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Error breakdown
        error_types = {}
        for snapshot in snapshots:
            if not snapshot.is_successful:
                status = snapshot.response_status
                error_types[status] = error_types.get(status, 0) + 1
        
        return {
            'period_hours': hours,
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'success_rate': (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            'avg_response_time_ms': round(avg_response_time, 2),
            'max_response_time_ms': max_response_time,
            'min_response_time_ms': min_response_time,
            'avg_quality_score': round(avg_quality_score, 2),
            'error_breakdown': error_types,
        }
    
    def get_data_volume_stats(self, site_id: int, days: int = 7) -> Dict[str, Any]:
        """Get data volume statistics."""
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        snapshots = self.session.query(Snapshot).filter(
            Snapshot.site_id == site_id,
            Snapshot.timestamp >= cutoff_time,
            Snapshot.response_status.between(200, 299)  # Only successful requests
        ).all()
        
        if not snapshots:
            return {}
        
        # Volume metrics
        total_size = sum(s.response_size_bytes or 0 for s in snapshots)
        total_processed = sum(s.processed_count for s in snapshots)
        
        # Daily breakdown
        daily_stats = {}
        for snapshot in snapshots:
            day = snapshot.timestamp.date()
            if day not in daily_stats:
                daily_stats[day] = {'requests': 0, 'processed_items': 0, 'total_size': 0}
            
            daily_stats[day]['requests'] += 1
            daily_stats[day]['processed_items'] += snapshot.processed_count
            daily_stats[day]['total_size'] += snapshot.response_size_bytes or 0
        
        return {
            'period_days': days,
            'total_snapshots': len(snapshots),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'total_processed_items': total_processed,
            'avg_items_per_request': round(total_processed / len(snapshots), 2),
            'avg_size_per_request': round(total_size / len(snapshots), 2),
            'daily_breakdown': {str(k): v for k, v in daily_stats.items()}
        }
    
    def cleanup_old_snapshots(self, days_to_keep: int = 90) -> int:
        """Clean up old snapshots, keeping only recent ones."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Count snapshots to be deleted
        count = self.session.query(Snapshot).filter(
            Snapshot.timestamp < cutoff_date
        ).count()
        
        # Delete old snapshots
        self.session.query(Snapshot).filter(
            Snapshot.timestamp < cutoff_date
        ).delete()
        
        return count
    
    def get_retry_snapshots(self, parent_snapshot_id: int) -> List[Snapshot]:
        """Get all retry snapshots for a parent snapshot."""
        return self.get_many_by_field('parent_snapshot_id', parent_snapshot_id)
    
    def mark_as_processed(self, snapshot_id: int, processed_count: int) -> Optional[Snapshot]:
        """Mark snapshot as processed with item count."""
        return self.update(snapshot_id, processed_count=processed_count)
    
    def update_quality_score(self, snapshot_id: int) -> Optional[Snapshot]:
        """Update the quality score for a snapshot."""
        snapshot = self.get_by_id(snapshot_id)
        if not snapshot:
            return None
        
        quality_score = snapshot.calculate_data_quality_score()
        snapshot.data_quality_score = quality_score
        
        self.session.flush()
        return snapshot
    
    def get_collection_timeline(self, site_id: int, days: int = 7) -> List[Dict[str, Any]]:
        """Get a timeline of collections for visualization."""
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        snapshots = self.session.query(Snapshot).filter(
            Snapshot.site_id == site_id,
            Snapshot.timestamp >= cutoff_time
        ).order_by(asc(Snapshot.timestamp)).all()
        
        timeline = []
        for snapshot in snapshots:
            timeline.append({
                'timestamp': snapshot.timestamp.isoformat(),
                'endpoint': snapshot.endpoint,
                'status': snapshot.response_status,
                'success': snapshot.is_successful,
                'response_time_ms': snapshot.response_time_ms,
                'processed_count': snapshot.processed_count,
                'quality_score': snapshot.data_quality_score,
            })
        
        return timeline