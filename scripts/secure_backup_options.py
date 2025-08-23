#!/usr/bin/env python3
"""
Secure backup options for environment variables.
Choose the method that matches your security needs.
"""

import json
import os
from datetime import datetime
from cryptography.fernet import Fernet
import getpass
import hashlib
import base64

# Option 1: Encrypted local backup
def create_encrypted_backup(env_vars):
    """Creates an encrypted backup with password-derived key."""
    
    # Get password from user (not stored)
    password = getpass.getpass("Enter encryption password: ")
    confirm = getpass.getpass("Confirm encryption password: ")
    
    if password != confirm:
        print("❌ Passwords don't match!")
        return
    
    # Derive key from password
    key = base64.urlsafe_b64encode(hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        b'render-backup-salt',  # Salt - could be randomized
        100000  # Iterations
    )[:32])
    
    # Encrypt the data
    fernet = Fernet(key)
    data = json.dumps(env_vars).encode()
    encrypted = fernet.encrypt(data)
    
    # Save encrypted backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"env_backup_{timestamp}.enc"
    
    with open(filename, 'wb') as f:
        f.write(encrypted)
    
    print(f"✅ Encrypted backup saved to: {filename}")
    print("📝 You'll need the password to decrypt")
    print("⚠️  Without the password, this file is unrecoverable!")

# Option 2: Direct cloud backup (using existing backup system)
def backup_to_cloud():
    """Trigger manual backup to R2/S3 through your existing API."""
    import requests
    
    print("This uses your existing backup system:")
    print("1. Go to: https://ai-study-architect.onrender.com/docs")
    print("2. Use the /api/v1/backup/trigger endpoint")
    print("3. Your env vars are already included in database backups")
    
    # Or trigger programmatically if you have the backup token
    backup_token = getpass.getpass("Enter BACKUP_TOKEN (or press Enter to skip): ")
    if backup_token:
        response = requests.post(
            "https://ai-study-architect.onrender.com/api/v1/backup/trigger",
            headers={"X-Backup-Token": backup_token},
            json={"provider": "r2"}
        )
        if response.status_code == 200:
            print("✅ Cloud backup triggered successfully")
        else:
            print(f"❌ Backup failed: {response.text}")

# Option 3: Password manager format
def export_for_password_manager(env_vars):
    """Format for easy copy/paste into password manager."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("\n" + "="*60)
    print(f"RENDER ENV BACKUP - {timestamp}")
    print("Copy this entire block to your password manager:")
    print("="*60)
    
    for key, value in env_vars.items():
        # Mask sensitive values in terminal output
        if len(value) > 10:
            masked = value[:3] + "..." + value[-3:]
        else:
            masked = "***"
        print(f"{key}={masked}")
    
    print("="*60)
    print("✅ Copy the ACTUAL values from Render dashboard")
    print("📝 Store in password manager as 'Render AI Study Architect Env'")

# Option 4: Secure cloud storage
def backup_to_secure_cloud():
    """Instructions for manual secure cloud backup."""
    
    print("""
    🔐 Most Secure Options:
    
    1. **Bitwarden/1Password Secure Notes**
       - Create secure note: "Render Env Vars Backup"
       - Copy/paste from Render dashboard
       - Automatically encrypted, synced, versioned
    
    2. **Encrypted Cloud Storage**
       - Use Cryptomator + Google Drive/Dropbox
       - Or use Keybase encrypted git
       - Or use age encryption + any cloud
    
    3. **GitHub Secret Gist (Private)**
       - Create private gist (still be careful!)
       - Name it with timestamp
       - Delete after recovery if needed
    
    4. **Your Existing R2/S3 Buckets**
       - Manually upload encrypted file
       - Already configured with your credentials
       - Use AWS CLI or Cloudflare dashboard
    
    5. **Render's Own Backup**
       - Database backups include connection strings
       - But not all env vars
       - Check Render dashboard → Backups
    """)

# Option 5: Recovery-only reference
def create_recovery_reference():
    """Create a reference doc without actual values."""
    
    reference = {
        "service": "ai-study-architect",
        "service_id": "srv-d2aad97diees738qmshg",
        "dashboard_url": "https://dashboard.render.com/web/srv-d2aad97diees738qmshg/env",
        "env_vars_needed": [
            "DATABASE_URL (auto-set by Render)",
            "ANTHROPIC_API_KEY (from Anthropic console)",
            "OPENAI_API_KEY (from OpenAI platform)",
            "BACKUP_TOKEN (from GitHub secrets)",
            "BACKUP_ENCRYPTION_KEY (NEVER CHANGE - check password manager)",
            "AWS_ACCESS_KEY_ID (from AWS IAM)",
            "AWS_SECRET_ACCESS_KEY (from AWS IAM)",
            "AWS_BACKUP_BUCKET (ai-study-architect-backup-2025)",
            "R2_ACCOUNT_ID (from Cloudflare dashboard)",
            "R2_ACCESS_KEY (from R2 API token)",
            "R2_SECRET_KEY (from R2 API token)",
            "R2_BUCKET (ai-study-architect-backups)",
            "SECRET_KEY (auto-generated)",
            "JWT_SECRET_KEY (auto-generated)"
        ],
        "recovery_sources": {
            "Anthropic Console": "https://console.anthropic.com/settings/keys",
            "OpenAI Platform": "https://platform.openai.com/api-keys",
            "GitHub Secrets": "https://github.com/belumume/ai-study-architect/settings/secrets/actions",
            "AWS IAM": "https://console.aws.amazon.com/iam/",
            "Cloudflare R2": "https://dash.cloudflare.com/",
            "Password Manager": "Check for 'Render AI Study Architect' entry"
        }
    }
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"env_recovery_reference_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(reference, f, indent=2)
    
    print(f"✅ Recovery reference saved to: {filename}")
    print("📝 This contains NO sensitive data, just references")

if __name__ == "__main__":
    print("🔐 Secure Backup Options for Environment Variables")
    print("-" * 50)
    print("1. Encrypted local file (password protected)")
    print("2. Use existing cloud backup system")
    print("3. Format for password manager")
    print("4. Secure cloud storage guide")
    print("5. Create recovery reference (no secrets)")
    print("-" * 50)
    
    choice = input("Choose option (1-5): ")
    
    if choice == "1":
        print("\n⚠️  First, copy your env vars from Render dashboard")
        print("Then update this script with actual values")
        # create_encrypted_backup(env_vars_dict)
    elif choice == "2":
        backup_to_cloud()
    elif choice == "3":
        print("\n⚠️  First, copy your env vars from Render dashboard")
        # export_for_password_manager(env_vars_dict)
    elif choice == "4":
        backup_to_secure_cloud()
    elif choice == "5":
        create_recovery_reference()
    else:
        print("Invalid choice")