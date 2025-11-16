"""
Concept and ConceptDependency models for Knowledge Graph

These models support the mastery-based learning system by representing:
- Atomic learning concepts extracted from course materials
- Prerequisite relationships between concepts (dependency graph)
- User mastery progress for each concept

This is part of the Knowledge Graph Foundation (Week 1 of mastery-based pivot)
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Float,
    JSON,
    CheckConstraint,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class DifficultyLevel(str, enum.Enum):
    """Difficulty levels for concepts"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ConceptType(str, enum.Enum):
    """Types of learning concepts"""
    DEFINITION = "definition"          # Basic definition or terminology
    PROCEDURE = "procedure"            # Step-by-step process
    PRINCIPLE = "principle"            # Fundamental rule or law
    EXAMPLE = "example"                # Concrete example or case study
    APPLICATION = "application"        # Practical application
    COMPARISON = "comparison"          # Comparison between concepts


class Concept(Base):
    """
    Atomic learning concept extracted from course materials

    Represents a single, testable unit of knowledge that can be mastered.
    Concepts are extracted from uploaded content using AI-powered analysis.

    Examples:
    - "Variables in Python" (definition)
    - "Binary Search Algorithm" (procedure)
    - "Time Complexity" (principle)
    """

    __tablename__ = "concepts"

    # Table-level constraints
    __table_args__ = (
        CheckConstraint(
            "difficulty IN ('beginner', 'intermediate', 'advanced', 'expert')",
            name="concept_difficulty_check"
        ),
        CheckConstraint(
            "concept_type IN ('definition', 'procedure', 'principle', 'example', 'application', 'comparison')",
            name="concept_type_check"
        ),
        CheckConstraint(
            "estimated_minutes >= 0",
            name="concept_estimated_minutes_positive"
        ),
    )

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Core concept information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)

    # Concept metadata
    concept_type = Column(String(50), nullable=False, default=ConceptType.DEFINITION)
    difficulty = Column(String(50), nullable=False, default=DifficultyLevel.BEGINNER)

    # Learning estimates
    estimated_minutes = Column(Integer, nullable=False, default=15)  # Time to master

    # Content relationship
    content_id = Column(UUID(as_uuid=True), ForeignKey("content.id", ondelete="CASCADE"), nullable=False)

    # Additional context
    examples = Column(JSON, nullable=True)  # List of example questions/scenarios
    keywords = Column(JSON, nullable=True)  # List of related keywords for search
    external_resources = Column(JSON, nullable=True)  # Links to additional resources

    # AI extraction metadata
    extraction_confidence = Column(Float, nullable=True)  # 0.0 to 1.0 confidence score
    extraction_metadata = Column(JSON, nullable=True)  # Additional AI extraction info

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    content = relationship("Content", back_populates="concepts")

    # Concept dependencies (prerequisites)
    # A concept can have multiple prerequisites
    prerequisites = relationship(
        "ConceptDependency",
        foreign_keys="ConceptDependency.dependent_concept_id",
        back_populates="dependent_concept",
        cascade="all, delete-orphan"
    )

    # Concepts that depend on this one
    dependents = relationship(
        "ConceptDependency",
        foreign_keys="ConceptDependency.prerequisite_concept_id",
        back_populates="prerequisite_concept",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Concept(id={self.id}, name='{self.name}', difficulty='{self.difficulty}')>"


class ConceptDependency(Base):
    """
    Represents prerequisite relationships between concepts

    Defines the dependency graph for learning concepts.
    Example: "Variables" is a prerequisite for "Functions"

    This enables:
    - Enforcing mastery gates (must master prerequisites first)
    - Optimal learning path generation
    - Prerequisite checking before concept unlock
    """

    __tablename__ = "concept_dependencies"

    # Table-level constraints
    __table_args__ = (
        # Ensure unique prerequisite relationships
        UniqueConstraint(
            'prerequisite_concept_id',
            'dependent_concept_id',
            name='unique_concept_dependency'
        ),
        CheckConstraint(
            "strength >= 0.0 AND strength <= 1.0",
            name="dependency_strength_range"
        ),
    )

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Prerequisite relationship
    # "To understand dependent_concept, you must first understand prerequisite_concept"
    prerequisite_concept_id = Column(
        UUID(as_uuid=True),
        ForeignKey("concepts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    dependent_concept_id = Column(
        UUID(as_uuid=True),
        ForeignKey("concepts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Dependency metadata
    strength = Column(Float, nullable=False, default=1.0)  # 0.0 = optional, 1.0 = required
    reason = Column(Text, nullable=True)  # Why this dependency exists

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    prerequisite_concept = relationship(
        "Concept",
        foreign_keys=[prerequisite_concept_id],
        back_populates="dependents"
    )
    dependent_concept = relationship(
        "Concept",
        foreign_keys=[dependent_concept_id],
        back_populates="prerequisites"
    )

    def __repr__(self) -> str:
        return f"<ConceptDependency(prerequisite={self.prerequisite_concept_id}, dependent={self.dependent_concept_id}, strength={self.strength})>"
