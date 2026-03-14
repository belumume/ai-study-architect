"""Pydantic schemas for content management"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ContentBase(BaseModel):
    """Base content schema"""

    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    content_type: str = Field(..., description="Type of content: notes, textbook, video, etc.")
    tags: list[str] | None = Field(default_factory=list)


class ContentCreate(ContentBase):
    """Schema for creating content - file upload handled separately"""

    pass


class ContentUpdate(BaseModel):
    """Schema for updating content metadata"""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    tags: list[str] | None = None
    subject_id: UUID | None = None

    model_config = ConfigDict(extra="forbid")


class ContentResponse(ContentBase):
    """Schema for content response"""

    id: UUID
    user_id: UUID
    file_path: str
    file_size: int
    mime_type: str
    file_hash: str
    original_filename: str
    processing_status: str
    extracted_text: str | None = None
    summary: str | None = None
    key_concepts: list[str] | None = None
    embeddings_generated: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContentListResponse(BaseModel):
    """Response for listing content"""

    items: list[ContentResponse]
    total: int
    skip: int
    limit: int
