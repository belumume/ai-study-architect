#!/usr/bin/env python3
"""
Backup script for Render environment variables.
Store these securely - they contain sensitive API keys!
"""

import json
from datetime import datetime

# CRITICAL: Fill in your current environment variables here
# Get these from https://dashboard.render.com/web/srv-d2aad97diees738qmshg/env
CURRENT_ENV_VARS = {
    "DATABASE_URL": "postgresql://...",  # Auto-configured by Render
    "ANTHROPIC_API_KEY": "sk-ant-xxx",  # Your Claude API key
    "OPENAI_API_KEY": "sk-xxx",  # Your OpenAI API key
    "BACKUP_TOKEN": "xxx",  # Match GitHub secret
    "BACKUP_ENCRYPTION_KEY": "xxx",  # NEVER CHANGE THIS
    "AWS_ACCESS_KEY_ID": "xxx",
    "AWS_SECRET_ACCESS_KEY": "xxx",
    "AWS_BACKUP_BUCKET": "ai-study-architect-backup-2025",
    "R2_ACCOUNT_ID": "xxx",
    "R2_ACCESS_KEY": "xxx",
    "R2_SECRET_KEY": "xxx",
    "R2_BUCKET": "ai-study-architect-backups",
    "SECRET_KEY": "xxx",  # Auto-generated
    "JWT_SECRET_KEY": "xxx",  # Auto-generated
}

def backup_env_vars():
    """Create timestamped backup of environment variables."""
    import os
    
    # Create backups directory if it doesn't exist
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups", "env_vars")
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"env_backup_{timestamp}.json"
    backup_file = os.path.join(backup_dir, backup_filename)
    
    with open(backup_file, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "service": "ai-study-architect",
            "service_id": "srv-d2aad97diees738qmshg",
            "env_vars": CURRENT_ENV_VARS
        }, f, indent=2)
    
    print(f"✅ Environment variables backed up to: {backup_file}")
    print("⚠️  Store this file securely - it contains sensitive API keys!")
    print(f"💡 Consider encrypting with: gpg -c {backup_file}")

if __name__ == "__main__":
    backup_env_vars()