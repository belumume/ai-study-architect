"""Add partial unique index for one active session per user

Revision ID: c1d2e3f4a5b6
Revises: f8a1b2c3d4e5
Create Date: 2026-03-15

Ensures at most one active (in_progress or paused) session exists per user
at the database level, preventing race conditions in the application layer.
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
    # Local dev uses PG enum (uppercase labels), Neon uses VARCHAR (lowercase values).
    # Detect column type and use appropriate syntax.
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_name = 'study_sessions' AND column_name = 'status'"
        )
    )
    data_type = result.scalar()

    if data_type == "USER-DEFINED":
        # PG enum — use enum cast with uppercase labels
        op.execute(
            "CREATE UNIQUE INDEX ix_one_active_session "
            "ON study_sessions (user_id) "
            "WHERE status IN ('IN_PROGRESS'::sessionstatus, 'PAUSED'::sessionstatus)"
        )
    else:
        # VARCHAR — use plain lowercase strings
        op.execute(
            "CREATE UNIQUE INDEX ix_one_active_session "
            "ON study_sessions (user_id) "
            "WHERE status IN ('in_progress', 'paused')"
        )


def downgrade() -> None:
    op.drop_index("ix_one_active_session", table_name="study_sessions")
