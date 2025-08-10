"""
Database configuration and session management
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import QueuePool
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create sync engine with proper connection pooling
# Note: Using QueuePool instead of NullPool for production performance
engine = create_engine(
    settings.DATABASE_URL_SQLALCHEMY,
    echo=settings.DEBUG,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_POOL_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=settings.DB_POOL_PRE_PING,
    poolclass=QueuePool,  # Production-ready connection pooling
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_pool_status() -> dict:
    """
    Get database connection pool status for monitoring
    
    Returns:
        Dictionary containing pool statistics
    """
    pool = engine.pool
    checked_in = pool.checkedin()
    checked_out = pool.checkedout()
    overflow = pool.overflow()
    pool_size = pool.size()
    
    return {
        "pool_size": pool_size,
        "checked_in": checked_in,
        "checked_out": checked_out,
        "overflow": overflow,
        "invalid": 0,  # QueuePool doesn't have invalidated() method
        "total_connections": pool_size + overflow,
        "available_connections": checked_in,
        "pool_status": "healthy" if checked_in >= 0 else "warning"
    }


def close_db() -> None:
    """Close database connections"""
    logger.info("Disposing database connection pool")
    engine.dispose()


def test_database_connection() -> bool:
    """
    Test database connectivity
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False