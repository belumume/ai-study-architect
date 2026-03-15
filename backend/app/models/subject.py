"""
Subject model for organizing study materials by topic
"""

import uuid
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.utils import utcnow

SUBJECT_COLORS = [
    "#D4FF00",
    "#00F2FE",
    "#FF2D7B",
    "#FFD700",
    "#B4A7FF",
    "#4dffd2",
    "#FF6B00",
    "#E0E0E0",
]


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    color = Column(String(7), nullable=False, default="#D4FF00")
    weekly_goal_minutes = Column(Integer, default=300, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_subject_user_name"),)

    user = relationship("User", back_populates="subjects")
    study_sessions = relationship("StudySession", back_populates="subject")

    def __repr__(self) -> str:
        return f"<Subject {self.name} ({self.color})>"
