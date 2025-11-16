"""Add knowledge graph tables (concepts and concept_dependencies)

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2025-11-16 18:30:00.000000

This migration adds the knowledge graph foundation for the mastery-based learning system.
Tables:
- concepts: Atomic learning concepts extracted from course materials
- concept_dependencies: Prerequisite relationships between concepts
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add concepts and concept_dependencies tables"""

    # Create concepts table
    op.create_table('concepts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('concept_type', sa.String(50), nullable=False),
        sa.Column('difficulty', sa.String(50), nullable=False),
        sa.Column('estimated_minutes', sa.Integer(), nullable=False),
        sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('examples', sa.JSON(), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('external_resources', sa.JSON(), nullable=True),
        sa.Column('extraction_confidence', sa.Float(), nullable=True),
        sa.Column('extraction_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['content_id'], ['content.id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "difficulty IN ('beginner', 'intermediate', 'advanced', 'expert')",
            name='concept_difficulty_check'
        ),
        sa.CheckConstraint(
            "concept_type IN ('definition', 'procedure', 'principle', 'example', 'application', 'comparison')",
            name='concept_type_check'
        ),
        sa.CheckConstraint(
            "estimated_minutes >= 0",
            name='concept_estimated_minutes_positive'
        ),
    )

    # Create indexes for concepts
    op.create_index('ix_concepts_name', 'concepts', ['name'])
    op.create_index('ix_concepts_content_id', 'concepts', ['content_id'])
    op.create_index('ix_concepts_difficulty', 'concepts', ['difficulty'])
    op.create_index('ix_concepts_created_at', 'concepts', ['created_at'])

    # Create concept_dependencies table
    op.create_table('concept_dependencies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prerequisite_concept_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dependent_concept_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('strength', sa.Float(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['prerequisite_concept_id'], ['concepts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['dependent_concept_id'], ['concepts.id'], ondelete='CASCADE'),
        sa.UniqueConstraint(
            'prerequisite_concept_id',
            'dependent_concept_id',
            name='unique_concept_dependency'
        ),
        sa.CheckConstraint(
            "strength >= 0.0 AND strength <= 1.0",
            name='dependency_strength_range'
        ),
    )

    # Create indexes for concept_dependencies
    op.create_index('ix_concept_dependencies_prerequisite', 'concept_dependencies', ['prerequisite_concept_id'])
    op.create_index('ix_concept_dependencies_dependent', 'concept_dependencies', ['dependent_concept_id'])


def downgrade() -> None:
    """Remove knowledge graph tables"""

    # Drop concept_dependencies indexes
    op.drop_index('ix_concept_dependencies_dependent', table_name='concept_dependencies')
    op.drop_index('ix_concept_dependencies_prerequisite', table_name='concept_dependencies')

    # Drop concept_dependencies table
    op.drop_table('concept_dependencies')

    # Drop concepts indexes
    op.drop_index('ix_concepts_created_at', table_name='concepts')
    op.drop_index('ix_concepts_difficulty', table_name='concepts')
    op.drop_index('ix_concepts_content_id', table_name='concepts')
    op.drop_index('ix_concepts_name', table_name='concepts')

    # Drop concepts table
    op.drop_table('concepts')
