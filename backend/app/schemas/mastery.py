"""
Pydantic schemas for user concept mastery tracking.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.user_concept_mastery import MasteryStatus


class MasteryResponse(BaseModel):
    id: UUID
    concept_id: UUID
    status: MasteryStatus
    mastery_level: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubjectMasterySummary(BaseModel):
    subject_id: UUID
    subject_name: str
    total_concepts: int
    mastered_count: int
    learning_count: int
    not_started_count: int
    mastery_percentage: float
