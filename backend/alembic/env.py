"""Simplified Alembic environment configuration that works on Render"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# CRITICAL: Set Python path for Render
# On Render, the app is at: /opt/render/project/src/project/backend
# We need to ensure this is in the path FIRST

# Determine where we are
if os.path.exists("/opt/render/project/src/project/backend"):
    # We're on Render
    backend_path = "/opt/render/project/src/project/backend"
else:
    # We're local - get parent of alembic directory
    backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add to Python path
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
    print(f"[Alembic] Added to path: {backend_path}", file=sys.stderr)

# Now we can import - but wrap in try/catch
try:
    from app.core.config import settings
    from app.core.database import Base
    
    # Try to import models - if this fails, we can still run with Base
    try:
        from app.models.user import User
        from app.models.content import Content
        from app.models.study_session import StudySession
        from app.models.practice import PracticeSession, Problem
        print("[Alembic] ✓ All models imported successfully", file=sys.stderr)
    except ImportError as e:
        print(f"[Alembic] Warning: Could not import all models: {e}", file=sys.stderr)
        print("[Alembic] Continuing with Base metadata only", file=sys.stderr)
    
except ImportError as e:
    print(f"[Alembic] FATAL: Cannot import app.core: {e}", file=sys.stderr)
    print(f"[Alembic] sys.path: {sys.path}", file=sys.stderr)
    print(f"[Alembic] Current dir: {os.getcwd()}", file=sys.stderr)
    # Re-raise to fail properly
    raise

# Alembic Config object
config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get database URL
database_url = settings.DATABASE_URL_SQLALCHEMY
database_url_escaped = database_url.replace('%', '%%')
config.set_main_option("sqlalchemy.url", database_url_escaped)

# Target metadata for autogenerate
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()