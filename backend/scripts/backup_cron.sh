#!/bin/bash
# Backup script to run on Render via cron job

# Install PostgreSQL client if not present
if ! command -v pg_dump &> /dev/null; then
    apt-get update && apt-get install -y postgresql-client
fi

# Install boto3 if needed
pip install boto3

# Run the backup script
cd /opt/render/project/src/backend
python scripts/backup_database.py --s3