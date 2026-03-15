"""Replace broken partial unique index for one active session per user

Revision ID: c1d2e3f4a5b6
Revises: f8a1b2c3d4e5
Create Date: 2026-03-15

Migration 942421c3cadb created idx_one_active_session_per_user using sa.text()
which failed on Neon (VARCHAR column). This migration drops the broken index
and recreates it with plain string comparison.

Note: The initial migration defines status as String(11) (VARCHAR), storing
lowercase values ('in_progress', 'paused'). Some local DBs may have a PG enum
from model autogeneration — those should be recreated from scratch.
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

    # Also drop our own index if re-running (idempotent)
    existing_new = conn.execute(
        sa.text("SELECT 1 FROM pg_indexes WHERE indexname = 'ix_one_active_session'")
    ).scalar()
    if existing_new:
        op.drop_index("ix_one_active_session", table_name="study_sessions")

    # Status column is VARCHAR per initial migration (String(11)), storing lowercase values.
    op.execute(
        "CREATE UNIQUE INDEX ix_one_active_session "
        "ON study_sessions (user_id) "
        "WHERE status IN ('in_progress', 'paused')"
    )


def downgrade() -> None:
    op.drop_index("ix_one_active_session", table_name="study_sessions")
    # Restore original index with same lowercase values
    op.execute(
        "CREATE UNIQUE INDEX idx_one_active_session_per_user "
        "ON study_sessions (user_id) "
        "WHERE status IN ('in_progress', 'paused')"
    )
