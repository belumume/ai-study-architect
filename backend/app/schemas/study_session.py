"""Pydantic schemas for study sessions and learning plans"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.utils import utcnow


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
    topics: list[str]
    prerequisites: list[str] = Field(default_factory=list)
    resources: list[str] = Field(default_factory=list)
    completed: bool = False
    completion_date: datetime | None = None


class StudyPlan(BaseModel):
    title: str
    description: str
    objectives: list[LearningObjective]
    total_hours: float
    created_by: str
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class StudySessionCreate(BaseModel):
    title: str
    description: str | None = None
    planned_duration: int
    content_ids: list[uuid.UUID] = Field(default_factory=list)
    objectives: list[str] = Field(default_factory=list)


class StudySessionUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    planned_duration: int | None = None
    actual_duration: int | None = None
    completion_percentage: int | None = None
    notes: str | None = None
    is_completed: bool | None = None


class StudySessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    subject_id: uuid.UUID | None = None
    title: str
    description: str | None
    planned_duration: int | None = None
    actual_duration: int | None = None
    completion_percentage: int | None = None
    notes: str | None = None
    is_completed: bool | None = None
    accumulated_seconds: int = 0
    status: str | None = None
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class StartSessionRequest(BaseModel):
    subject_id: uuid.UUID | None = None
    study_mode: str = "practice"
    title: str | None = None


class SessionStateResponse(BaseModel):
    id: uuid.UUID
    status: str
    accumulated_seconds: int
    duration_minutes: int
    subject_id: uuid.UUID | None = None
    title: str
    actual_start: datetime | None = None
    actual_end: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class StudyProgress(BaseModel):
    total_sessions: int
    completed_sessions: int
    total_study_time: int
    average_completion_rate: float
    topics_covered: list[str]
    current_streak: int
    longest_streak: int
    last_study_date: datetime | None
