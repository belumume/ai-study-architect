"""
Practice Session model for AI-generated practice problems
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class ProblemType(str, enum.Enum):
    """Types of practice problems"""
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    CODE = "code"
    CALCULATION = "calculation"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"


class DifficultyLevel(str, enum.Enum):
    """Problem difficulty levels"""
    BEGINNER = "beginner"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class PracticeSession(Base):
    """Practice session model"""
    
    __tablename__ = "practice_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    study_session_id = Column(UUID(as_uuid=True), ForeignKey("study_sessions.id"), nullable=True)
    
    # Session information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    subject = Column(String(100), nullable=True)
    topic = Column(String(100), nullable=True)
    
    # Problems
    problems = Column(JSON, nullable=False)  # List of problem objects
    problem_count = Column(Integer, nullable=False)
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    time_limit_minutes = Column(Integer, nullable=True)
    actual_duration_minutes = Column(Integer, default=0, nullable=False)
    
    # Performance
    score = Column(Float, nullable=True)  # Percentage score
    correct_answers = Column(Integer, default=0, nullable=False)
    incorrect_answers = Column(Integer, default=0, nullable=False)
    skipped_answers = Column(Integer, default=0, nullable=False)
    
    # Adaptive learning
    difficulty_level = Column(Enum(DifficultyLevel), default=DifficultyLevel.MEDIUM, nullable=False)
    adaptive_adjustments = Column(JSON, nullable=True)  # Log of difficulty adjustments
    
    # AI Generation metadata
    generation_params = Column(JSON, nullable=True)  # Parameters used for generation
    generation_model = Column(String(50), nullable=True)
    
    # Detailed results
    problem_results = Column(JSON, nullable=True)  # Detailed results per problem
    strengths = Column(JSON, nullable=True)  # Identified strength areas
    weaknesses = Column(JSON, nullable=True)  # Identified weak areas
    recommendations = Column(Text, nullable=True)  # AI recommendations
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="practice_sessions")
    study_session = relationship("StudySession", back_populates="practice_sessions")
    
    def __repr__(self) -> str:
        return f"<PracticeSession {self.title} ({self.problem_count} problems)>"


class Problem(Base):
    """Individual practice problem (for future expansion)"""
    
    __tablename__ = "problems"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Problem content
    question = Column(Text, nullable=False)
    problem_type = Column(Enum(ProblemType), nullable=False)
    options = Column(JSON, nullable=True)  # For multiple choice
    correct_answer = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    
    # Metadata
    subject = Column(String(100), nullable=True)
    topic = Column(String(100), nullable=True)
    subtopic = Column(String(100), nullable=True)
    difficulty_level = Column(Enum(DifficultyLevel), nullable=False)
    
    # Source
    source_content_id = Column(UUID(as_uuid=True), nullable=True)
    generated_by_model = Column(String(50), nullable=True)
    
    # Usage statistics
    times_used = Column(Integer, default=0, nullable=False)
    average_score = Column(Float, nullable=True)
    average_time_seconds = Column(Integer, nullable=True)
    
    # Quality metrics
    quality_score = Column(Float, nullable=True)  # Based on user feedback
    flagged_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<Problem {self.problem_type.value} - {self.topic}>"