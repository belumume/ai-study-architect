"""Add database indexes for performance

Revision ID: 5f6e634ec8dc
Revises: 3c297453e3ed
Create Date: 2025-07-22 03:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '5f6e634ec8dc'
down_revision = '3c297453e3ed'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add indexes for common query patterns"""
    
    # User table indexes (email and username already have unique indexes from initial migration)
    op.create_index('idx_users_created_at', 'users', ['created_at'])
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    
    # Content table indexes
    op.create_index('idx_content_user_id', 'content', ['user_id'])
    op.create_index('idx_content_created_at', 'content', ['created_at'])
    op.create_index('idx_content_content_type', 'content', ['content_type'])
    op.create_index('idx_content_processing_status', 'content', ['processing_status'])
    # Composite index for user's content by type
    op.create_index('idx_content_user_type', 'content', ['user_id', 'content_type'])
    # Composite index for user's content by date
    op.create_index('idx_content_user_created', 'content', ['user_id', 'created_at'])
    
    # Study session indexes
    op.create_index('idx_study_sessions_user_id', 'study_sessions', ['user_id'])
    op.create_index('idx_study_sessions_status', 'study_sessions', ['status'])
    op.create_index('idx_study_sessions_created_at', 'study_sessions', ['created_at'])
    op.create_index('idx_study_sessions_scheduled_start', 'study_sessions', ['scheduled_start'])
    # Composite index for user's sessions by status
    op.create_index('idx_study_sessions_user_status', 'study_sessions', ['user_id', 'status'])
    
    # Practice session indexes
    op.create_index('idx_practice_sessions_user_id', 'practice_sessions', ['user_id'])
    op.create_index('idx_practice_sessions_study_session_id', 'practice_sessions', ['study_session_id'])
    op.create_index('idx_practice_sessions_created_at', 'practice_sessions', ['created_at'])
    
    # Problem indexes
    op.create_index('idx_problems_source_content_id', 'problems', ['source_content_id'])
    op.create_index('idx_problems_difficulty_level', 'problems', ['difficulty_level'])
    op.create_index('idx_problems_topic', 'problems', ['topic'])
    op.create_index('idx_problems_subject', 'problems', ['subject'])
    
    # Study session content association table indexes
    # These are already created as part of the primary key, but adding for clarity
    op.create_index('idx_study_session_content_session', 'study_session_content', ['study_session_id'])
    op.create_index('idx_study_session_content_content', 'study_session_content', ['content_id'])


def downgrade() -> None:
    """Remove indexes"""
    
    # Drop indexes in reverse order
    op.drop_index('idx_study_session_content_content', 'study_session_content')
    op.drop_index('idx_study_session_content_session', 'study_session_content')
    
    op.drop_index('idx_problems_subject', 'problems')
    op.drop_index('idx_problems_topic', 'problems')
    op.drop_index('idx_problems_difficulty_level', 'problems')
    op.drop_index('idx_problems_source_content_id', 'problems')
    
    op.drop_index('idx_practice_sessions_created_at', 'practice_sessions')
    op.drop_index('idx_practice_sessions_study_session_id', 'practice_sessions')
    op.drop_index('idx_practice_sessions_user_id', 'practice_sessions')
    
    op.drop_index('idx_study_sessions_user_status', 'study_sessions')
    op.drop_index('idx_study_sessions_scheduled_start', 'study_sessions')
    op.drop_index('idx_study_sessions_created_at', 'study_sessions')
    op.drop_index('idx_study_sessions_status', 'study_sessions')
    op.drop_index('idx_study_sessions_user_id', 'study_sessions')
    
    op.drop_index('idx_content_user_created', 'content')
    op.drop_index('idx_content_user_type', 'content')
    op.drop_index('idx_content_processing_status', 'content')
    op.drop_index('idx_content_content_type', 'content')
    op.drop_index('idx_content_created_at', 'content')
    op.drop_index('idx_content_user_id', 'content')
    
    op.drop_index('idx_users_is_active', 'users')
    op.drop_index('idx_users_created_at', 'users')