"""
Pydantic schemas for User-related operations
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema with common attributes"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: str | None = Field(None, max_length=255)
    bio: str | None = None
    learning_goals: str | None = None
    preferred_study_time: str | None = Field(
        None,
        pattern="^(morning|afternoon|evening|night)$"
    )
    timezone: str = Field(default="UTC", max_length=50)
    allow_analytics: bool = False
    allow_collaboration: bool = True


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema for user profile updates"""
    full_name: str | None = Field(None, max_length=255)
    bio: str | None = None
    learning_goals: str | None = None
    preferred_study_time: str | None = Field(
        None,
        pattern="^(morning|afternoon|evening|night)$"
    )
    timezone: str | None = Field(None, max_length=50)
    allow_analytics: bool | None = None
    allow_collaboration: bool | None = None


class UserUpdatePassword(BaseModel):
    """Schema for password update"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class UserResponse(UserBase):
    """Schema for user responses (excludes password)"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    is_verified: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None


class UserLogin(BaseModel):
    """Schema for user login"""
    username_or_email: str
    password: str


class Token(BaseModel):
    """Schema for authentication tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token payload data"""
    sub: str | None = None
    exp: datetime | None = None
    type: str | None = None


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str
