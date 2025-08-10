"""Add search and performance optimization indexes

Revision ID: edcfcde614ab
Revises: 5f6e634ec8dc
Create Date: 2025-07-22 07:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'edcfcde614ab'
down_revision = '5f6e634ec8dc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add indexes for search optimization and N+1 query prevention"""
    
    # Search optimization indexes for content table
    # These support the full-text search functionality
    op.create_index('idx_content_title_lower', 'content', 
                   [sa.text("LOWER(title)")], postgresql_using='btree')
    op.create_index('idx_content_description_lower', 'content', 
                   [sa.text("LOWER(description)")], postgresql_using='btree')
    op.create_index('idx_content_extracted_text_lower', 'content', 
                   [sa.text("LOWER(extracted_text)")], postgresql_using='btree')
    
    # Hash-based index for deduplication
    op.create_index('idx_content_file_hash', 'content', ['file_hash'])
    op.create_index('idx_content_user_hash', 'content', ['user_id', 'file_hash'])
    
    # Analytics and statistics indexes
    op.create_index('idx_content_file_size', 'content', ['file_size'])
    op.create_index('idx_content_view_count', 'content', ['view_count'])
    op.create_index('idx_content_study_time', 'content', ['study_time_minutes'])
    op.create_index('idx_content_last_accessed', 'content', ['last_accessed_at'])
    
    # Subject-based indexing
    op.create_index('idx_content_subject', 'content', ['subject'])
    op.create_index('idx_content_user_subject', 'content', ['user_id', 'subject'])
    
    # Composite indexes for complex queries
    op.create_index('idx_content_user_status_created', 'content', 
                   ['user_id', 'processing_status', 'created_at'])
    
    # JSON-based tag search optimization (PostgreSQL specific)
    # This supports efficient tag-based filtering
    try:
        # Only create if PostgreSQL supports GIN indexes on JSON
        op.create_index('idx_content_tags_gin', 'content', ['tags'], 
                       postgresql_using='gin')
    except Exception:
        # Fallback for databases that don't support GIN on JSON
        pass
    
    # Embeddings and AI-related indexes
    op.create_index('idx_content_embedding_id', 'content', ['embedding_id'])
    op.create_index('idx_content_embeddings_generated', 'content', ['embeddings_generated'])
    op.create_index('idx_content_embedding_model', 'content', ['embedding_model'])
    
    # File processing optimization
    op.create_index('idx_content_mime_type', 'content', ['mime_type'])
    op.create_index('idx_content_processing_times', 'content', 
                   ['processing_started_at', 'processing_completed_at'])


def downgrade() -> None:
    """Remove search optimization indexes"""
    
    # Drop indexes in reverse order
    op.drop_index('idx_content_processing_times', 'content')
    op.drop_index('idx_content_mime_type', 'content')
    
    op.drop_index('idx_content_embedding_model', 'content')
    op.drop_index('idx_content_embeddings_generated', 'content')
    op.drop_index('idx_content_embedding_id', 'content')
    
    try:
        op.drop_index('idx_content_tags_gin', 'content')
    except Exception:
        pass
    
    op.drop_index('idx_content_user_status_created', 'content')
    
    op.drop_index('idx_content_user_subject', 'content')
    op.drop_index('idx_content_subject', 'content')
    
    op.drop_index('idx_content_last_accessed', 'content')
    op.drop_index('idx_content_study_time', 'content')
    op.drop_index('idx_content_view_count', 'content')
    op.drop_index('idx_content_file_size', 'content')
    
    op.drop_index('idx_content_user_hash', 'content')
    op.drop_index('idx_content_file_hash', 'content')
    
    op.drop_index('idx_content_extracted_text_lower', 'content')
    op.drop_index('idx_content_description_lower', 'content')
    op.drop_index('idx_content_title_lower', 'content')