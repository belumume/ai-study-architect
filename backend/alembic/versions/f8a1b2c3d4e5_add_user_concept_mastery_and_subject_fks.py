"""Add user_concept_mastery table and subject FK columns

Revision ID: f8a1b2c3d4e5
Revises: 942421c3cadb
Create Date: 2026-03-14

Phase 2: Concept Extraction Pipeline
- Creates user_concept_mastery table (7 columns, 2 constraints, 3 indexes)
- Adds subject_id FK to concepts table
- Adds subject_id FK + extraction_status + extraction_error to content table
- Backfills content.subject_id from legacy content.subject string field
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f8a1b2c3d4e5"
down_revision: Union[str, None] = "942421c3cadb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create user_concept_mastery table
    op.create_table(
        "user_concept_mastery",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "concept_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("concepts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="not_started",
        ),
        sa.Column("mastery_level", sa.Float, nullable=False, server_default="0.0"),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("user_id", "concept_id", name="uq_user_concept_mastery"),
        sa.CheckConstraint(
            "mastery_level >= 0.0 AND mastery_level <= 1.0",
            name="mastery_level_range",
        ),
        sa.CheckConstraint(
            "status IN ('not_started', 'learning', 'reviewing', 'mastered')",
            name="mastery_status_check",
        ),
    )

    # Indexes for user_concept_mastery
    op.create_index(
        "ix_ucm_concept_id",
        "user_concept_mastery",
        ["concept_id"],
    )
    op.create_index(
        "ix_ucm_user_status",
        "user_concept_mastery",
        ["user_id", "status"],
        postgresql_where=sa.text("status != 'mastered'"),
    )

    # 2. Add subject_id to concepts table
    op.add_column(
        "concepts",
        sa.Column(
            "subject_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("subjects.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_concepts_subject_id", "concepts", ["subject_id"])

    # 3. Add subject_id + extraction fields to content table
    op.add_column(
        "content",
        sa.Column(
            "subject_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("subjects.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_content_subject_id", "content", ["subject_id"])

    op.add_column(
        "content",
        sa.Column("extraction_status", sa.String(20), nullable=True),
    )
    op.add_column(
        "content",
        sa.Column("extraction_error", sa.Text, nullable=True),
    )

    # 4. Backfill content.subject_id from legacy content.subject string
    op.execute(
        """
        UPDATE content
        SET subject_id = s.id
        FROM subjects s
        WHERE content.subject = s.name
          AND content.user_id = s.user_id
          AND content.subject_id IS NULL
        """
    )


def downgrade() -> None:
    # Remove extraction fields from content
    op.drop_column("content", "extraction_error")
    op.drop_column("content", "extraction_status")

    # Remove subject_id from content
    op.drop_index("ix_content_subject_id", table_name="content")
    op.drop_column("content", "subject_id")

    # Remove subject_id from concepts
    op.drop_index("ix_concepts_subject_id", table_name="concepts")
    op.drop_column("concepts", "subject_id")

    # Drop user_concept_mastery table
    op.drop_index("ix_ucm_user_status", table_name="user_concept_mastery")
    op.drop_index("ix_ucm_concept_id", table_name="user_concept_mastery")
    op.drop_table("user_concept_mastery")
