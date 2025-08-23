"""
Configuration settings for AI Study Architect - Complete version
"""

from typing import Any, Optional, List, Union
from urllib.parse import quote_plus
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, field_validator, Field
import os


class Settings(BaseSettings):
    """Application settings with validation"""
    
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / ".env"),  # Explicit path to backend/.env
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra fields in .env
    )
    
    # API Settings
    API_VERSION: str = "v1"
    PROJECT_NAME: str = "AI Study Architect"
    DEBUG: bool = False
    SECRET_KEY: str
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"
    
    # JWT Security Settings
    JWT_SECRET_KEY: str = Field(..., description="Secret key for JWT token signing")
    JWT_ALGORITHM: str = Field(default="RS256", description="Algorithm for JWT token signing")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiration time in minutes")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiration time in days")
    
    # Database
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None
    
    # Database Connection Pool Settings
    DB_POOL_SIZE: int = Field(default=20, description="Database connection pool size")
    DB_POOL_MAX_OVERFLOW: int = Field(default=0, description="Max overflow connections")
    DB_POOL_TIMEOUT: int = Field(default=30, description="Pool checkout timeout in seconds")
    DB_POOL_RECYCLE: int = Field(default=3600, description="Connection recycle time in seconds")
    DB_POOL_PRE_PING: bool = Field(default=True, description="Enable connection pre-ping")
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # Celery
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    
    # CORS - Use str and parse in validator
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = Field(
        default="http://localhost:3000,http://localhost:5173,https://www.aistudyarchitect.com,https://aistudyarchitect.com,https://ai-study-architect.vercel.app",
        description="Comma-separated list of allowed origins"
    )
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        elif isinstance(v, list):
            return v
        return v
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 52428800  # 50MB
    ALLOWED_UPLOAD_EXTENSIONS: Union[str, List[str]] = Field(
        default="pdf,docx,pptx,txt,md,jpg,jpeg,png,mp3,mp4,wav",
        description="Comma-separated list of allowed extensions"
    )
    UPLOAD_DIR: str = "uploads"
    
    @field_validator("ALLOWED_UPLOAD_EXTENSIONS", mode="before")
    @classmethod
    def parse_upload_extensions(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        elif isinstance(v, list):
            return v
        return v
    
    # Rate Limiting
    RATE_LIMIT_DEFAULT: int = 60
    RATE_LIMIT_UPLOAD: int = 10
    RATE_LIMIT_AI_GENERATION: int = 20
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Testing
    TEST_DATABASE_URL: Optional[str] = None
    TEST_REDIS_URL: Optional[str] = None
    
    @property
    def DATABASE_URL_SQLALCHEMY(self) -> str:
        """Get the DATABASE_URL as a string for SQLAlchemy"""
        # Check if we have a DATABASE_URL (from Render or other deployment)
        if os.getenv("DATABASE_URL"):
            # Parse Render's postgres:// to postgresql://
            db_url = os.getenv("DATABASE_URL")
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
            # Use psycopg2 on Render instead of pg8000
            db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return db_url
        
        # Local development: construct URL with proper encoding
        # Only do this if we have the individual components
        if self.POSTGRES_PASSWORD and self.POSTGRES_USER:
            encoded_password = quote_plus(self.POSTGRES_PASSWORD)
            encoded_user = quote_plus(self.POSTGRES_USER)
            return f"postgresql+pg8000://{encoded_user}:{encoded_password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        
        # Fallback - should not reach here in normal operation
        raise ValueError("No database configuration found. Set either DATABASE_URL or POSTGRES_* environment variables.")


# Create settings instance
settings = Settings()