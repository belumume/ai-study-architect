#!/usr/bin/env bash
# Build script for Render Starter plan (with more permissions)

set -e

echo "Starting build process for Starter plan..."

# Try to install PostgreSQL 17 client with sudo (Starter plan might allow this)
if command -v sudo &> /dev/null; then
    echo "Attempting to install PostgreSQL 17 client with sudo..."
    sudo apt-get update || echo "Cannot update apt"
    sudo apt-get install -y wget ca-certificates || echo "Cannot install prerequisites"
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add - || echo "Cannot add key"
    echo "deb http://apt.postgresql.org/pub/repos/apt/ bookworm-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list || echo "Cannot add repo"
    sudo apt-get update || echo "Cannot update after adding repo"
    sudo apt-get install -y postgresql-client-17 || echo "Cannot install PostgreSQL 17"
else
    echo "No sudo available - using existing PostgreSQL client"
fi

# Check pg_dump version
if command -v pg_dump &> /dev/null; then
    echo "PostgreSQL client version:"
    pg_dump --version
fi

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install backup dependencies
pip install boto3 cryptography psycopg2-binary

# Generate RSA keys
python scripts/generate_rsa_keys.py || echo "RSA keys setup skipped"

echo "Build complete!"