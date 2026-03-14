"""add_subjects_table_and_session_fields

Revision ID: 942421c3cadb
Revises: b7c8d9e0f1a2
Create Date: 2026-03-14 02:14:50.885532

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "942421c3cadb"
down_revision: Union[str, None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create subjects table
    op.create_table(
        "subjects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("color", sa.String(7), nullable=False, server_default="#D4FF00"),
        sa.Column("weekly_goal_minutes", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="uq_subject_user_name"),
    )
    op.create_index("idx_subjects_user_id", "subjects", ["user_id"])
    op.create_index("idx_subjects_user_active", "subjects", ["user_id", "is_active"])

    # Add columns to study_sessions
    op.add_column(
        "study_sessions", sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column(
        "study_sessions",
        sa.Column("accumulated_seconds", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("study_sessions", sa.Column("last_resumed_at", sa.DateTime(), nullable=True))

    # Add foreign key for subject_id
    op.create_foreign_key(
        "fk_study_sessions_subject_id", "study_sessions", "subjects", ["subject_id"], ["id"]
    )

    # Composite indexes for dashboard queries (P0 performance finding)
    op.create_index(
        "idx_study_sessions_user_status_start",
        "study_sessions",
        ["user_id", "status", sa.text("actual_start DESC")],
    )
    op.create_index(
        "idx_study_sessions_user_subject_start",
        "study_sessions",
        ["user_id", "subject_id", sa.text("actual_start DESC")],
    )

    # Partial unique index: one active session per user (C1 security finding)
    op.create_index(
        "idx_one_active_session_per_user",
        "study_sessions",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('in_progress', 'paused')"),
    )


def downgrade() -> None:
    op.drop_index("idx_one_active_session_per_user", table_name="study_sessions")
    op.drop_index("idx_study_sessions_user_subject_start", table_name="study_sessions")
    op.drop_index("idx_study_sessions_user_status_start", table_name="study_sessions")
    op.drop_constraint("fk_study_sessions_subject_id", "study_sessions", type_="foreignkey")
    op.drop_column("study_sessions", "last_resumed_at")
    op.drop_column("study_sessions", "accumulated_seconds")
    op.drop_column("study_sessions", "subject_id")
    op.drop_index("idx_subjects_user_active", table_name="subjects")
    op.drop_index("idx_subjects_user_id", table_name="subjects")
    op.drop_table("subjects")
