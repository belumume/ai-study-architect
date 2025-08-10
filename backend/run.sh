#!/usr/bin/env bash
# Universal start script that handles both Alembic and direct startup

set -e

echo "Starting AI Study Architect..."
echo "Initial working directory: $(pwd)"

# Navigate to the correct directory on Render
if [ -d "/opt/render/project/src/project/backend" ]; then
    echo "Detected Render environment"
    cd /opt/render/project/src/project/backend
    echo "Changed to backend directory: $(pwd)"
    echo "Directory contents:"
    ls -la
fi

# Set Python path explicitly for module resolution
export PYTHONPATH="/opt/render/project/src/project/backend:$(pwd):${PYTHONPATH}"
echo "Python path set to: $PYTHONPATH"

# Verify Python can find the app module
echo "=== Testing Python imports ==="
python -c "import sys; print('Python executable:', sys.executable)" || true
python -c "import sys; print('Python version:', sys.version)" || true
python -c "import sys; print('Python path:', sys.path[:3])" || true
python -c "import app; print('✓ app module found at:', app.__file__)" || echo "✗ Cannot import app module"
python -c "from app.models import User; print('✓ app.models.User found')" || echo "✗ Cannot import app.models"

# Attempt migrations, but don't fail if they don't work
echo "Attempting database migrations..."
(
    # Try to run Alembic using Python module (ensures venv dependencies)
    python -m alembic upgrade head 2>&1 | tee /tmp/alembic.log
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo "✓ Migrations completed successfully"
    else
        echo "⚠ Migrations failed (this is OK - app will create tables)"
        echo "Alembic output saved to /tmp/alembic.log"
    fi
) || true

# Start the application using python -m for proper module resolution
echo "Starting FastAPI application..."
# CRITICAL: Use python -m uvicorn to ensure proper module imports
python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}