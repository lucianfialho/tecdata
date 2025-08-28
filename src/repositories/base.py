"""Base repository with common CRUD operations."""

from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Base repository class with common CRUD operations."""
    
    def __init__(self, model: Type[T], session: Session):
        self.model = model
        self.session = session
    
    def create(self, **kwargs) -> T:
        """Create a new record."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        self.session.flush()  # Get the ID without committing
        return instance
    
    def get_by_id(self, id: int) -> Optional[T]:
        """Get record by ID."""
        return self.session.query(self.model).filter(
            self.model.id == id,
            getattr(self.model, 'is_deleted', False) == False
        ).first()
    
    def get_all(self, limit: int = None, offset: int = None, 
                include_deleted: bool = False) -> List[T]:
        """Get all records with optional pagination."""
        query = self.session.query(self.model)
        
        if not include_deleted and hasattr(self.model, 'is_deleted'):
            query = query.filter(self.model.is_deleted == False)
        
        if offset:
            query = query.offset(offset)
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_by_field(self, field: str, value: Any) -> Optional[T]:
        """Get record by specific field."""
        query = self.session.query(self.model).filter(
            getattr(self.model, field) == value
        )
        
        if hasattr(self.model, 'is_deleted'):
            query = query.filter(self.model.is_deleted == False)
            
        return query.first()
    
    def get_many_by_field(self, field: str, value: Any, limit: int = None) -> List[T]:
        """Get multiple records by specific field."""
        query = self.session.query(self.model).filter(
            getattr(self.model, field) == value
        )
        
        if hasattr(self.model, 'is_deleted'):
            query = query.filter(self.model.is_deleted == False)
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def update(self, id: int, **kwargs) -> Optional[T]:
        """Update record by ID."""
        instance = self.get_by_id(id)
        if not instance:
            return None
        
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        
        # Update timestamp if model has it
        if hasattr(instance, 'updated_at'):
            instance.updated_at = datetime.utcnow()
        
        self.session.flush()
        return instance
    
    def delete(self, id: int, soft_delete: bool = True) -> bool:
        """Delete record by ID."""
        instance = self.get_by_id(id)
        if not instance:
            return False
        
        if soft_delete and hasattr(instance, 'soft_delete'):
            instance.soft_delete()
        else:
            self.session.delete(instance)
        
        self.session.flush()
        return True
    
    def count(self, include_deleted: bool = False) -> int:
        """Count total records."""
        query = self.session.query(self.model)
        
        if not include_deleted and hasattr(self.model, 'is_deleted'):
            query = query.filter(self.model.is_deleted == False)
            
        return query.count()
    
    def exists(self, **kwargs) -> bool:
        """Check if record exists with given criteria."""
        query = self.session.query(self.model).filter_by(**kwargs)
        
        if hasattr(self.model, 'is_deleted'):
            query = query.filter(self.model.is_deleted == False)
            
        return query.first() is not None
    
    def bulk_create(self, records: List[Dict[str, Any]]) -> List[T]:
        """Create multiple records in batch."""
        instances = []
        
        try:
            for record_data in records:
                instance = self.model(**record_data)
                instances.append(instance)
                self.session.add(instance)
            
            self.session.flush()
            return instances
            
        except IntegrityError as e:
            self.session.rollback()
            raise e
    
    def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """Update multiple records in batch."""
        updated_count = 0
        
        for update_data in updates:
            record_id = update_data.pop('id')
            if self.update(record_id, **update_data):
                updated_count += 1
        
        return updated_count
    
    def get_recent(self, hours: int = 24, limit: int = None) -> List[T]:
        """Get recently created records."""
        from datetime import datetime, timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        query = self.session.query(self.model)
        
        if hasattr(self.model, 'created_at'):
            query = query.filter(self.model.created_at >= cutoff_time)
        elif hasattr(self.model, 'timestamp'):
            query = query.filter(self.model.timestamp >= cutoff_time)
        else:
            # Fallback to all records if no timestamp field
            pass
        
        if hasattr(self.model, 'is_deleted'):
            query = query.filter(self.model.is_deleted == False)
        
        if limit:
            query = query.limit(limit)
            
        return query.order_by(
            getattr(self.model, 'created_at', getattr(self.model, 'timestamp', self.model.id)).desc()
        ).all()
    
    def search(self, search_term: str, fields: List[str], limit: int = 50) -> List[T]:
        """Search records by text in specified fields."""
        if not search_term or not fields:
            return []
        
        from sqlalchemy import or_
        
        query = self.session.query(self.model)
        
        # Build OR conditions for all specified fields
        conditions = []
        for field in fields:
            if hasattr(self.model, field):
                field_attr = getattr(self.model, field)
                conditions.append(field_attr.ilike(f'%{search_term}%'))
        
        if conditions:
            query = query.filter(or_(*conditions))
        
        if hasattr(self.model, 'is_deleted'):
            query = query.filter(self.model.is_deleted == False)
        
        return query.limit(limit).all()
    
    def commit(self):
        """Commit current transaction."""
        self.session.commit()
    
    def rollback(self):
        """Rollback current transaction."""
        self.session.rollback()
    
    def flush(self):
        """Flush changes to database without committing."""
        self.session.flush()
    
    def refresh(self, instance: T) -> T:
        """Refresh instance from database."""
        self.session.refresh(instance)
        return instance