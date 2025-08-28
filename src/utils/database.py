"""Database utilities and connection management."""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from src.models.base import SessionLocal, init_db
from .logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """Database connection and session management."""
    
    @staticmethod
    def init_database():
        """Initialize database tables."""
        try:
            logger.info("Initializing database tables...")
            init_db()
            logger.info("Database tables initialized successfully")
        except SQLAlchemyError as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @staticmethod
    @contextmanager
    def get_session() -> Generator[Session, None, None]:
        """Get database session with automatic cleanup."""
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Database session error: {e}")
            session.rollback()
            raise
        finally:
            session.close()
    
    @staticmethod
    def test_connection() -> bool:
        """Test database connection."""
        try:
            with DatabaseManager.get_session() as session:
                session.execute("SELECT 1")
                logger.info("Database connection test successful")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Database connection test failed: {e}")
            return False