"""
UserConceptMastery model for tracking per-user mastery of extracted concepts.

Phase 2: Stores mastery status for each concept per user.
Phase 4 will add: total_attempts, correct_attempts, consecutive_correct
Phase 5 will add: ease_factor, repetition_number, interval_days, next_review_date
"""

import enum
import uuid

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.utils import utcnow


class MasteryStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    LEARNING = "learning"
    REVIEWING = "reviewing"
    MASTERED = "mastered"


class UserConceptMastery(Base):
    __tablename__ = "user_concept_mastery"
    __table_args__ = (
        UniqueConstraint("user_id", "concept_id", name="uq_user_concept_mastery"),
        CheckConstraint(
            "mastery_level >= 0.0 AND mastery_level <= 1.0",
            name="mastery_level_range",
        ),
        CheckConstraint(
            "status IN ('not_started', 'learning', 'reviewing', 'mastered')",
            name="mastery_status_check",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    concept_id = Column(
        UUID(as_uuid=True),
        ForeignKey("concepts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status = Column(String(20), nullable=False, default=MasteryStatus.NOT_STARTED)
    mastery_level = Column(Float, nullable=False, default=0.0)

    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    user = relationship("User", back_populates="concept_mastery")
    concept = relationship("Concept", back_populates="mastery_records")

    def __repr__(self) -> str:
        return f"<UserConceptMastery user={self.user_id} concept={self.concept_id} status={self.status}>"
