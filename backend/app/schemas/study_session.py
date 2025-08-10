"""Pydantic schemas for study sessions and learning plans"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class DifficultyLevel(str, Enum):
    """Difficulty levels for learning content"""
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"


class LearningObjective(BaseModel):
    """Individual learning objective within a study plan"""
    id: str
    title: str
    description: str
    estimated_hours: float
    topics: List[str]
    prerequisites: List[str] = Field(default_factory=list)
    resources: List[str] = Field(default_factory=list)
    completed: bool = False
    completion_date: Optional[datetime] = None


class StudyPlan(BaseModel):
    """A complete study plan for a learning goal"""
    title: str
    description: str
    objectives: List[LearningObjective]
    total_hours: float
    created_by: str  # Agent ID that created the plan
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StudySessionCreate(BaseModel):
    """Schema for creating a new study session"""
    title: str
    description: Optional[str] = None
    planned_duration: int  # in minutes
    content_ids: List[int] = Field(default_factory=list)
    objectives: List[str] = Field(default_factory=list)


class StudySessionUpdate(BaseModel):
    """Schema for updating a study session"""
    title: Optional[str] = None
    description: Optional[str] = None
    planned_duration: Optional[int] = None
    actual_duration: Optional[int] = None
    completion_percentage: Optional[int] = None
    notes: Optional[str] = None
    is_completed: Optional[bool] = None


class StudySessionResponse(BaseModel):
    """Schema for study session responses"""
    id: int
    user_id: int
    title: str
    description: Optional[str]
    planned_duration: int
    actual_duration: Optional[int]
    completion_percentage: int
    notes: Optional[str]
    is_completed: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class StudyProgress(BaseModel):
    """Overall study progress for a user"""
    total_sessions: int
    completed_sessions: int
    total_study_time: int  # in minutes
    average_completion_rate: float
    topics_covered: List[str]
    current_streak: int  # days
    longest_streak: int  # days
    last_study_date: Optional[datetime]