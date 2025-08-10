"""
Study Session model for tracking learning sessions
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text, Float, Table, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class SessionStatus(str, enum.Enum):
    """Study session status"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class StudyMode(str, enum.Enum):
    """Types of study modes"""
    READING = "reading"
    PRACTICE = "practice"
    REVIEW = "review"
    QUIZ = "quiz"
    DISCUSSION = "discussion"
    PROJECT = "project"


# Association table for many-to-many relationship between study sessions and content
study_session_content = Table(
    "study_session_content",
    Base.metadata,
    Column("study_session_id", UUID(as_uuid=True), ForeignKey("study_sessions.id"), primary_key=True),
    Column("content_id", UUID(as_uuid=True), ForeignKey("content.id"), primary_key=True),
    Column("added_at", DateTime, default=datetime.utcnow),
    Column("time_spent_minutes", Float, default=0.0),
)


class StudySession(Base):
    """Study session model"""
    
    __tablename__ = "study_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Session information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    study_mode = Column(Enum(StudyMode), nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.PLANNED, nullable=False)
    
    # Timing
    scheduled_start = Column(DateTime, nullable=True)
    scheduled_end = Column(DateTime, nullable=True)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, default=0, nullable=False)
    
    # Learning objectives
    learning_objectives = Column(JSON, nullable=True)  # List of objectives
    target_concepts = Column(JSON, nullable=True)  # Concepts to focus on
    
    # AI Agent interactions
    agent_interactions = Column(JSON, nullable=True)  # Log of agent interactions
    personalization_params = Column(JSON, nullable=True)  # Personalization settings
    
    # Progress tracking
    progress_percentage = Column(Float, default=0.0, nullable=False)
    concepts_mastered = Column(JSON, nullable=True)  # List of mastered concepts
    areas_for_improvement = Column(JSON, nullable=True)  # Identified weak areas
    
    # Analytics
    focus_score = Column(Float, nullable=True)  # 0-100 focus/engagement score
    comprehension_score = Column(Float, nullable=True)  # 0-100 comprehension score
    notes = Column(Text, nullable=True)  # User notes during session
    
    # Collaboration
    is_collaborative = Column(Boolean, default=False, nullable=False)
    collaborator_ids = Column(JSON, nullable=True)  # List of collaborator user IDs
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="study_sessions")
    content_items = relationship("Content", secondary=study_session_content, back_populates="study_sessions")
    practice_sessions = relationship("PracticeSession", back_populates="study_session", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<StudySession {self.title} ({self.status.value})>"