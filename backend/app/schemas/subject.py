"""
Subject Pydantic schemas
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
import unicodedata


class SubjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    color: str = Field(default="#D4FF00", pattern=r"^#[0-9a-fA-F]{6}$")
    weekly_goal_minutes: int = Field(default=300, ge=0, le=2520)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        v = unicodedata.normalize("NFC", v)
        if not v:
            raise ValueError("Name cannot be empty after normalization")
        if any(unicodedata.category(c).startswith("C") for c in v):
            raise ValueError("Name contains invalid control characters")
        return v


class SubjectCreate(SubjectBase):
    pass


class SubjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    weekly_goal_minutes: Optional[int] = Field(None, ge=0, le=2520)
    is_active: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        v = unicodedata.normalize("NFC", v)
        if not v:
            raise ValueError("Name cannot be empty after normalization")
        if any(unicodedata.category(c).startswith("C") for c in v):
            raise ValueError("Name contains invalid control characters")
        return v


class SubjectResponse(SubjectBase):
    id: uuid.UUID
    user_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
