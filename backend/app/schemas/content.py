"""Pydantic schemas for content management"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


class ContentBase(BaseModel):
    """Base content schema"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    content_type: str = Field(..., description="Type of content: notes, textbook, video, etc.")
    tags: Optional[List[str]] = Field(default_factory=list)


class ContentCreate(ContentBase):
    """Schema for creating content - file upload handled separately"""
    pass


class ContentUpdate(BaseModel):
    """Schema for updating content metadata"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None
    
    model_config = ConfigDict(extra='forbid')


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
    extracted_text: Optional[str] = None
    summary: Optional[str] = None
    key_concepts: Optional[List[str]] = None
    embeddings_generated: bool = False
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ContentListResponse(BaseModel):
    """Response for listing content"""
    items: List[ContentResponse]
    total: int
    skip: int
    limit: int