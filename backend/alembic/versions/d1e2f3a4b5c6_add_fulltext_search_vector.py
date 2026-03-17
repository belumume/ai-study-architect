"""Add full-text search vector column with GIN index and trigger

Revision ID: d1e2f3a4b5c6
Revises: c1d2e3f4a5b6
Create Date: 2026-03-16

Adds tsvector column + GIN index + trigger for PostgreSQL full-text search
on content table. Replaces LIKE-based search (O(n*text_size)) with indexed
tsvector search (O(log n)). Weighted: title(A) > description(B) > text(C).
"""

from alembic import op


revision = "d1e2f3a4b5c6"
down_revision = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add tsvector column
    op.execute("ALTER TABLE content ADD COLUMN search_vector tsvector")

    # Create trigger function with weighted fields
    op.execute("""
        CREATE OR REPLACE FUNCTION content_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B') ||
                setweight(to_tsvector('english', coalesce(NEW.extracted_text, '')), 'C');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger
    op.execute("""
        CREATE TRIGGER content_search_vector_trigger
        BEFORE INSERT OR UPDATE OF title, description, extracted_text
        ON content
        FOR EACH ROW
        EXECUTE FUNCTION content_search_vector_update();
    """)

    # Backfill existing rows
    op.execute("""
        UPDATE content SET search_vector =
            setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(description, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(extracted_text, '')), 'C');
    """)

    # Create GIN index for fast search
    op.execute("CREATE INDEX idx_content_search_vector ON content USING GIN (search_vector)")

    # Drop old LOWER() btree indexes — useless for substring LIKE search
    op.execute("DROP INDEX IF EXISTS idx_content_title_lower")
    op.execute("DROP INDEX IF EXISTS idx_content_description_lower")
    op.execute("DROP INDEX IF EXISTS idx_content_extracted_text_lower")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_content_search_vector")
    op.execute("DROP TRIGGER IF EXISTS content_search_vector_trigger ON content")
    op.execute("DROP FUNCTION IF EXISTS content_search_vector_update()")
    op.execute("ALTER TABLE content DROP COLUMN IF EXISTS search_vector")

    # Recreate old indexes
    op.execute("CREATE INDEX idx_content_title_lower ON content (LOWER(title))")
    op.execute("CREATE INDEX idx_content_description_lower ON content (LOWER(description))")
    op.execute("CREATE INDEX idx_content_extracted_text_lower ON content (LOWER(extracted_text))")
