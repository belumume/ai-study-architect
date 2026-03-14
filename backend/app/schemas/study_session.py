"""Pydantic schemas for study sessions and learning plans"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, ConfigDict, Field
from enum import Enum


class DifficultyLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"


class LearningObjective(BaseModel):
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
    title: str
    description: str
    objectives: List[LearningObjective]
    total_hours: float
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StudySessionCreate(BaseModel):
    title: str
    description: Optional[str] = None
    planned_duration: int
    content_ids: List[uuid.UUID] = Field(default_factory=list)
    objectives: List[str] = Field(default_factory=list)


class StudySessionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    planned_duration: Optional[int] = None
    actual_duration: Optional[int] = None
    completion_percentage: Optional[int] = None
    notes: Optional[str] = None
    is_completed: Optional[bool] = None


class StudySessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    subject_id: Optional[uuid.UUID] = None
    title: str
    description: Optional[str]
    planned_duration: Optional[int] = None
    actual_duration: Optional[int] = None
    completion_percentage: Optional[int] = None
    notes: Optional[str] = None
    is_completed: Optional[bool] = None
    accumulated_seconds: int = 0
    status: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class StartSessionRequest(BaseModel):
    subject_id: Optional[uuid.UUID] = None
    study_mode: str = "practice"
    title: Optional[str] = None


class SessionStateResponse(BaseModel):
    id: uuid.UUID
    status: str
    accumulated_seconds: int
    duration_minutes: int
    subject_id: Optional[uuid.UUID] = None
    title: str
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class StudyProgress(BaseModel):
    total_sessions: int
    completed_sessions: int
    total_study_time: int
    average_completion_rate: float
    topics_covered: List[str]
    current_streak: int
    longest_streak: int
    last_study_date: Optional[datetime]
