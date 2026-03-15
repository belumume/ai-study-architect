"""Replace broken partial unique index for one active session per user

Revision ID: c1d2e3f4a5b6
Revises: f8a1b2c3d4e5
Create Date: 2026-03-15

Migration 942421c3cadb created idx_one_active_session_per_user using sa.text()
which failed on Neon (VARCHAR column, not PG enum). This migration drops the
broken index and recreates it with proper type detection.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, None] = "f8a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # Drop the broken index from migration 942421c3cadb if it exists
    existing = conn.execute(
        sa.text("SELECT 1 FROM pg_indexes WHERE indexname = 'idx_one_active_session_per_user'")
    ).scalar()
    if existing:
        op.drop_index("idx_one_active_session_per_user", table_name="study_sessions")

    # Detect column type: PG enum (USER-DEFINED) vs VARCHAR
    result = conn.execute(
        sa.text(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_schema = current_schema() "
            "AND table_name = 'study_sessions' AND column_name = 'status'"
        )
    )
    data_type = result.scalar()
    if data_type is None:
        raise RuntimeError("study_sessions.status column not found in current schema")

    if data_type == "USER-DEFINED":
        # PG enum — cast to text to avoid hardcoding enum type name
        op.execute(
            "CREATE UNIQUE INDEX ix_one_active_session "
            "ON study_sessions (user_id) "
            "WHERE status::text IN ('IN_PROGRESS', 'PAUSED')"
        )
    else:
        # VARCHAR — plain lowercase strings
        op.execute(
            "CREATE UNIQUE INDEX ix_one_active_session "
            "ON study_sessions (user_id) "
            "WHERE status IN ('in_progress', 'paused')"
        )


def downgrade() -> None:
    op.drop_index("ix_one_active_session", table_name="study_sessions")
    # Restore original index name with portable type detection
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_schema = current_schema() "
            "AND table_name = 'study_sessions' AND column_name = 'status'"
        )
    )
    data_type = result.scalar()
    if data_type == "USER-DEFINED":
        op.execute(
            "CREATE UNIQUE INDEX idx_one_active_session_per_user "
            "ON study_sessions (user_id) "
            "WHERE status::text IN ('IN_PROGRESS', 'PAUSED')"
        )
    else:
        op.execute(
            "CREATE UNIQUE INDEX idx_one_active_session_per_user "
            "ON study_sessions (user_id) "
            "WHERE status IN ('in_progress', 'paused')"
        )
