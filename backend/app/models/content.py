"""
Content model for user-uploaded study materials
"""

import enum
import uuid
import sqlalchemy as sa
from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy import event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.utils import utcnow


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
            name="content_type_check",
        ),
        CheckConstraint(
            "processing_status IN ('pending', 'processing', 'completed', 'failed')",
            name="processing_status_check",
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
    subject = Column(String(100), nullable=True)  # Legacy text field (pre-Phase 2)
    subject_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    tags = Column(JSON, nullable=True)  # List of tags

    # Concept extraction lifecycle (separate from processing_status)
    extraction_status = Column(
        String(20), nullable=True
    )  # extracting|completed|completed_empty|failed|partial
    extraction_error = Column(Text, nullable=True)

    # Full-text search (maintained by PostgreSQL trigger)
    search_vector = Column(TSVECTOR)

    # Analytics
    view_count = Column(Integer, default=0, nullable=False)
    study_time_minutes = Column(Float, default=0.0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )
    last_accessed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="content_items")
    subject_ref = relationship("Subject")
    study_sessions = relationship(
        "StudySession", secondary="study_session_content", back_populates="content_items"
    )

    def __repr__(self) -> str:
        return f"<Content {self.title} ({self.content_type})>"


@event.listens_for(Content.__table__, "after_create")
def _create_search_trigger(_target: sa.Table, connection: sa.Connection, **_kw: object) -> None:
    """Create tsvector trigger + GIN index for create_all() environments (tests, init_db)."""
    connection.execute(
        sa.text("""
            CREATE OR REPLACE FUNCTION content_search_vector_update() RETURNS trigger AS $$
            BEGIN
                NEW.search_vector :=
                    setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
                    setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B') ||
                    setweight(to_tsvector('english', coalesce(NEW.extracted_text, '')), 'C');
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
    )
    connection.execute(
        sa.text("""
            CREATE TRIGGER content_search_vector_trigger
            BEFORE INSERT OR UPDATE OF title, description, extracted_text
            ON content
            FOR EACH ROW
            EXECUTE FUNCTION content_search_vector_update();
        """)
    )
    connection.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_content_search_vector "
            "ON content USING GIN (search_vector)"
        )
    )
