#!/usr/bin/env bash
# Start script for Render deployment with proper Python path setup

set -e

echo "Starting AI Study Architect on Render..."

# Since rootDir is set to backend in render.yaml,
# we should already be in the backend directory
# Just add the current directory to PYTHONPATH
export PYTHONPATH="$(pwd):${PYTHONPATH}"

# Debug information (helps diagnose deployment issues)
echo "Working directory: $(pwd)"
echo "Python path: $PYTHONPATH"
echo "Directory contents:"
ls -la

# Verify app directory exists
if [ -d "app" ]; then
    echo "✓ app directory found at $(pwd)/app"
else
    echo "✗ ERROR: app directory not found!"
    echo "Current location: $(pwd)"
    echo "Directory structure:"
    find . -type d -name "app" 2>/dev/null || true
    exit 1
fi

# Alembic state fix no longer needed - database tables already exist

# Run database migrations
echo "Running database migrations..."

# First, let's check if we can connect to the database
python -c "
import os
from sqlalchemy import create_engine
db_url = os.getenv('DATABASE_URL', '')
if db_url:
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute('SELECT 1')
        print('✓ Database connection successful')
        exit(0)
    except Exception as e:
        print(f'✗ Database connection failed: {e}')
        exit(1)
else:
    print('✗ DATABASE_URL not set')
    exit(1)
" && {
    # Database is ready, run migrations
    alembic upgrade head || {
        echo "Migration failed - trying alternative approach..."
        # Try with explicit PYTHONPATH
        PYTHONPATH=$(pwd) alembic upgrade head || {
            echo "Migration still failed - will skip for now"
            echo "The app will create tables on first request"
        }
    }
} || {
    echo "Database not ready - skipping migrations"
    echo "The app will create tables when database becomes available"
}

# Start the FastAPI application
echo "Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}