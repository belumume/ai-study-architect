#!/usr/bin/env bash
# Build script for Render deployment

set -e

echo "Starting build process..."

# Check if pg_dump is already available
if command -v pg_dump &> /dev/null; then
    echo "PostgreSQL client found:"
    pg_dump --version
else
    echo "PostgreSQL client not found - will handle in backup script"
fi

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install additional backup dependencies
echo "Installing backup dependencies..."
pip install boto3 cryptography psycopg2-binary

# Generate RSA keys if they don't exist
echo "Setting up RSA keys..."
python scripts/generate_rsa_keys.py || echo "RSA keys setup skipped"

echo "Build complete!"