"""Minimal database initialization without model imports"""

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


def init_db_minimal(engine, Base) -> bool:
    """
    Initialize database with minimal dependencies
    
    Args:
        engine: SQLAlchemy engine
        Base: SQLAlchemy declarative base
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Creating database tables (minimal mode)...")
        
        # Import models here to avoid circular imports
        try:
            # Try to import models
            from app.models import user, content, study_session, practice
            logger.info("Models imported successfully")
        except ImportError as e:
            logger.warning(f"Could not import models: {e}")
            logger.info("Continuing without models - tables may need manual creation")
        
        # Create all tables
        Base.metadata.create_all(bind=engine, checkfirst=True)
        
        logger.info("✓ Database initialization complete!")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


def check_database_connection(engine) -> bool:
    """
    Check if database is accessible
    
    Args:
        engine: SQLAlchemy engine
        
    Returns:
        bool: True if connected, False otherwise
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("✓ Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False