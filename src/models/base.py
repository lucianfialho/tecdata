"""Base model configuration for SQLAlchemy 2.0+."""

from datetime import datetime
from typing import Any
from sqlalchemy import Column, DateTime, create_engine, Boolean
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from config.settings import settings

# Create the SQLAlchemy engine
engine = create_engine(
    settings.database.url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=300,
    future=True,  # Enable SQLAlchemy 2.0 behavior
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,  # Enable SQLAlchemy 2.0 behavior
)


@as_declarative()
class Base:
    """Base class for all database models with common fields."""
    
    id: Any
    __name__: str
    
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        # Convert CamelCase to snake_case and add 's'
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
        return name + 's' if not name.endswith('s') else name
    
    # Common timestamp fields
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True
    )
    
    # Soft delete support
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    def soft_delete(self) -> None:
        """Mark record as deleted without physically removing it."""
        from datetime import datetime
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={getattr(self, 'id', None)})>"


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)