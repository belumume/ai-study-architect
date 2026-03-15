"""Add partial unique index for one active session per user

Revision ID: c1d2e3f4a5b6
Revises: f8a1b2c3d4e5
Create Date: 2026-03-15

Ensures at most one active (in_progress or paused) session exists per user
at the database level, preventing race conditions in the application layer.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, None] = "f8a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # status is a PostgreSQL enum with uppercase labels (IN_PROGRESS, PAUSED)
    op.execute(
        "CREATE UNIQUE INDEX ix_one_active_session "
        "ON study_sessions (user_id) "
        "WHERE status IN ('IN_PROGRESS'::sessionstatus, 'PAUSED'::sessionstatus)"
    )


def downgrade() -> None:
    op.drop_index("ix_one_active_session", table_name="study_sessions")
