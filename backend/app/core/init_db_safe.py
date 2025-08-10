"""Initialize database with parameterized queries and better security"""

from sqlalchemy import text, MetaData
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import engine, Base
from app.models.user import User
from app.models.content import Content
from app.models.study_session import StudySession, study_session_content
from app.models.practice import PracticeSession, Problem
import logging

logger = logging.getLogger(__name__)


def init_db() -> bool:
    """
    Initialize database using SQLAlchemy's DDL abstraction
    
    This approach is safer than raw SQL because:
    1. SQLAlchemy handles SQL injection prevention
    2. DDL is database-agnostic
    3. Proper transaction management
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Use SQLAlchemy's create_all which is safe from SQL injection
        logger.info("Creating database tables...")
        
        # Only create tables if they don't exist
        # This preserves existing data
        Base.metadata.create_all(bind=engine, checkfirst=True)
        
        logger.info("✓ All tables created successfully!")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Database error creating tables: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error creating tables: {e}")
        return False


def verify_tables() -> bool:
    """
    Verify that all required tables exist
    
    Returns:
        bool: True if all tables exist, False otherwise
    """
    try:
        with engine.connect() as conn:
            # Use parameterized query to check table existence
            # Note: We need to use ANY with array for PostgreSQL
            result = conn.execute(
                text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = :schema 
                    AND table_name = ANY(:table_names)
                """),
                {
                    "schema": "public",
                    "table_names": ["users", "content", "study_sessions", 
                                  "practice_sessions", "problems", 
                                  "study_session_content"]
                }
            )
            
            existing_tables = {row[0] for row in result}
            required_tables = {"users", "content", "study_sessions", 
                             "practice_sessions", "problems", 
                             "study_session_content"}
            
            missing_tables = required_tables - existing_tables
            
            if missing_tables:
                logger.error(f"Missing tables: {missing_tables}")
                return False
                
            logger.info("✓ All required tables exist")
            return True
            
    except SQLAlchemyError as e:
        logger.error(f"Database error verifying tables: {e}")
        return False


def create_initial_superuser(email: str, username: str, password: str) -> bool:
    """
    Create initial superuser account with parameterized query
    
    Args:
        email: Superuser email
        username: Superuser username  
        password: Plain text password (will be hashed)
        
    Returns:
        bool: True if created, False otherwise
    """
    try:
        from app.core.security import get_password_hash
        from sqlalchemy.orm import Session
        
        with Session(engine) as session:
            # Check if superuser already exists
            existing = session.query(User).filter(
                (User.email == email) | (User.username == username)
            ).first()
            
            if existing:
                logger.info(f"Superuser already exists: {existing.email}")
                return True
                
            # Create new superuser
            superuser = User(
                email=email,
                username=username,
                full_name="System Administrator",
                hashed_password=get_password_hash(password),
                is_active=True,
                is_superuser=True,
                is_verified=True
            )
            
            session.add(superuser)
            session.commit()
            
            logger.info(f"✓ Superuser created: {email}")
            return True
            
    except SQLAlchemyError as e:
        logger.error(f"Database error creating superuser: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error creating superuser: {e}")
        return False


if __name__ == "__main__":
    # Initialize database
    if init_db():
        # Verify tables
        if verify_tables():
            # Create initial superuser (for development only)
            # In production, use environment variables or management command
            import os
            admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
            admin_username = os.getenv("ADMIN_USERNAME", "admin")
            admin_password = os.getenv("ADMIN_PASSWORD", "changeme123")
            
            create_initial_superuser(admin_email, admin_username, admin_password)