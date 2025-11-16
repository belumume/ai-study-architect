"""
Content model for user-uploaded study materials
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text, Float, JSON, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class ContentType(str, enum.Enum):
    """Types of content that can be uploaded"""
    PDF = "pdf"
    DOCUMENT = "document"  # docx, txt, md
    PRESENTATION = "presentation"  # pptx
    IMAGE = "image"  # jpg, png
    AUDIO = "audio"  # mp3, wav
    VIDEO = "video"  # mp4
    NOTE = "note"  # user-created text note


class ProcessingStatus(str, enum.Enum):
    """Content processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Content(Base):
    """Content model for study materials"""
    
    __tablename__ = "content"
    
    # Add table-level constraints
    __table_args__ = (
        CheckConstraint(
            "content_type IN ('pdf', 'document', 'presentation', 'image', 'audio', 'video', 'note')",
            name="content_type_check"
        ),
        CheckConstraint(
            "processing_status IN ('pending', 'processing', 'completed', 'failed')",
            name="processing_status_check"
        ),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Content metadata
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content_type = Column(
        String(50), 
        nullable=False,
        # Validate using CHECK constraint instead of ENUM
        # This avoids the CREATE TYPE permission issue
    )
    
    # File information
    file_path = Column(String(500), nullable=True)  # Path to uploaded file
    file_size = Column(Integer, nullable=True)  # Size in bytes
    mime_type = Column(String(100), nullable=True)
    file_hash = Column(String(64), nullable=True)  # SHA-256 hash for deduplication
    original_filename = Column(String(255), nullable=True)  # Original uploaded filename
    
    # Processing information
    processing_status = Column(
        String(50), 
        default="pending", 
        nullable=False,
        # Validate using CHECK constraint instead of ENUM
    )
    processing_error = Column(Text, nullable=True)
    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    
    # Extracted content
    extracted_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    key_concepts = Column(JSON, nullable=True)  # List of key concepts
    content_metadata = Column(JSON, nullable=True)  # Additional metadata
    
    # Vector embeddings reference
    embedding_id = Column(String(100), nullable=True)  # ID in vector store
    embedding_model = Column(String(50), nullable=True)
    embeddings_generated = Column(Integer, default=0, nullable=False)  # Boolean as integer
    
    # Organization
    subject = Column(String(100), nullable=True)
    tags = Column(JSON, nullable=True)  # List of tags
    
    # Analytics
    view_count = Column(Integer, default=0, nullable=False)
    study_time_minutes = Column(Float, default=0.0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_accessed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="content_items")
    study_sessions = relationship("StudySession", secondary="study_session_content", back_populates="content_items")
    concepts = relationship("Concept", back_populates="content", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Content {self.title} ({self.content_type})>"