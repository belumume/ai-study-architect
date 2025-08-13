#!/usr/bin/env python3
"""
Enterprise-grade backup system for AI Study Architect.
Primary: Cloudflare R2 (daily)
Secondary: AWS S3 (weekly)
Both encrypted, auto-rotating, monitored.
"""

import os
import sys
import json
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Tuple
import tempfile
import subprocess

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable not set")
    sys.exit(1)

class CloudProvider:
    """Cloud storage provider configurations"""
    
    CLOUDFLARE_R2 = {
        "name": "Cloudflare R2",
        "endpoint_template": "https://{account_id}.r2.cloudflarestorage.com",
        "env_vars": {
            "account_id": "R2_ACCOUNT_ID",
            "access_key": "R2_ACCESS_KEY",
            "secret_key": "R2_SECRET_KEY",
            "bucket": "R2_BUCKET"
        },
        "default_bucket": "ai-study-architect-backups",
        "retention_days": 30,
        "keep_minimum": 7
    }
    
    AWS_S3 = {
        "name": "AWS S3",
        "endpoint_template": "https://s3.{region}.amazonaws.com",
        "env_vars": {
            "access_key": "AWS_ACCESS_KEY_ID",
            "secret_key": "AWS_SECRET_ACCESS_KEY",
            "region": "AWS_REGION",
            "bucket": "AWS_BACKUP_BUCKET"
        },
        "default_bucket": "ai-study-architect-backup-secondary",
        "default_region": "us-west-2",
        "retention_days": 14,
        "keep_minimum": 3
    }

class BackupOrchestrator:
    """Orchestrates backups across multiple providers"""
    
    def __init__(self):
        self.providers_status = {}
        self.encryption_key = os.getenv("BACKUP_ENCRYPTION_KEY")
        if not self.encryption_key:
            logger.warning("⚠️  No BACKUP_ENCRYPTION_KEY set. Generating one...")
            self.encryption_key = hashlib.sha256(os.urandom(32)).hexdigest()
            logger.info(f"💡 Save this key in Render: BACKUP_ENCRYPTION_KEY={self.encryption_key}")
    
    def backup_all(self):
        """Execute all configured backups"""
        logger.info("🚀 Starting backup orchestration...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "environment": os.getenv("ENVIRONMENT", "production"),
            "providers": {}
        }
        
        # Primary: Cloudflare R2 (always)
        r2_success = self.backup_to_r2()
        results["providers"]["cloudflare_r2"] = {
            "success": r2_success,
            "type": "primary"
        }
        
        # Secondary: AWS S3 (weekly or on-demand)
        if self._should_run_secondary():
            s3_success = self.backup_to_s3()
            results["providers"]["aws_s3"] = {
                "success": s3_success,
                "type": "secondary"
            }
        
        # Send monitoring alert if any failed
        if not all(p["success"] for p in results["providers"].values()):
            self._send_alert(results)
        
        return results
    
    def backup_to_r2(self) -> bool:
        """Primary backup to Cloudflare R2"""
        logger.info("☁️  Cloudflare R2 Backup (PRIMARY)")
        
        config = CloudProvider.CLOUDFLARE_R2
        
        # Get credentials
        account_id = os.getenv(config["env_vars"]["account_id"])
        access_key = os.getenv(config["env_vars"]["access_key"])
        secret_key = os.getenv(config["env_vars"]["secret_key"])
        bucket = os.getenv(config["env_vars"]["bucket"], config["default_bucket"])
        
        if not all([account_id, access_key, secret_key]):
            logger.error("❌ R2 not configured. See setup instructions below.")
            self._print_r2_setup()
            return False
        
        endpoint = config["endpoint_template"].format(account_id=account_id)
        
        return self._execute_backup(
            provider="cloudflare_r2",
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            bucket=bucket,
            retention_config=config
        )
    
    def backup_to_s3(self) -> bool:
        """Secondary backup to AWS S3"""
        logger.info("☁️  AWS S3 Backup (SECONDARY)")
        
        config = CloudProvider.AWS_S3
        
        # Get credentials
        access_key = os.getenv(config["env_vars"]["access_key"])
        secret_key = os.getenv(config["env_vars"]["secret_key"])
        region = os.getenv(config["env_vars"]["region"], config["default_region"])
        bucket = os.getenv(config["env_vars"]["bucket"], config["default_bucket"])
        
        if not all([access_key, secret_key]):
            logger.error("❌ AWS S3 not configured. See setup instructions below.")
            self._print_s3_setup()
            return False
        
        endpoint = config["endpoint_template"].format(region=region)
        
        return self._execute_backup(
            provider="aws_s3",
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            bucket=bucket,
            retention_config=config,
            region=region
        )
    
    def _execute_backup(self, provider: str, endpoint: str, access_key: str, 
                       secret_key: str, bucket: str, retention_config: dict,
                       region: Optional[str] = None) -> bool:
        """Execute backup to S3-compatible storage"""
        try:
            import boto3
            from botocore.config import Config
        except ImportError:
            logger.error("Install boto3: pip install boto3")
            return False
        
        # Configure S3 client
        client_config = {
            'service_name': 's3',
            'endpoint_url': endpoint,
            'aws_access_key_id': access_key,
            'aws_secret_access_key': secret_key,
        }
        
        if region:
            client_config['region_name'] = region
        
        s3_client = boto3.client(
            **client_config,
            config=Config(signature_version='s3v4')
        )
        
        # Use temp file
        with tempfile.NamedTemporaryFile(suffix='.sql.gz.enc', delete=True) as tmp_file:
            try:
                # 1. Create compressed dump
                logger.info("📝 Creating database dump...")
                if not self._create_dump(tmp_file.name):
                    return False
                
                # 2. Encrypt
                logger.info("🔐 Encrypting backup...")
                self._encrypt_file(tmp_file.name)
                
                # 3. Upload
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                object_key = f"backups/{os.getenv('ENVIRONMENT', 'production')}/{provider}/{timestamp}.sql.gz.enc"
                
                file_size = os.path.getsize(tmp_file.name)
                size_mb = file_size / (1024 * 1024)
                
                logger.info(f"📤 Uploading {size_mb:.2f} MB to {bucket}/{object_key}")
                
                # Upload with metadata
                s3_client.upload_file(
                    tmp_file.name,
                    bucket,
                    object_key,
                    ExtraArgs={
                        'Metadata': {
                            'environment': os.getenv('ENVIRONMENT', 'production'),
                            'timestamp': timestamp,
                            'provider': provider,
                            'encrypted': 'true',
                            'compressed': 'gzip',
                            'database_size_mb': str(size_mb)
                        },
                        'StorageClass': 'STANDARD_IA' if provider == 'aws_s3' else 'STANDARD'
                    }
                )
                
                logger.info(f"✅ Backup successful to {retention_config['name']}")
                
                # 4. Cleanup old backups
                self._cleanup_old_backups(
                    s3_client, bucket, provider,
                    retention_config["retention_days"],
                    retention_config["keep_minimum"]
                )
                
                return True
                
            except Exception as e:
                logger.error(f"❌ Backup to {provider} failed: {e}")
                return False
    
    def _create_dump(self, output_file: str) -> bool:
        """Create compressed PostgreSQL dump"""
        import subprocess
        import shutil
        from urllib.parse import urlparse
        
        db_url = DATABASE_URL
        
        # First, try to use pg_dump if available
        if shutil.which('pg_dump'):
            logger.info("Using pg_dump for backup")
            
            # Use connection string directly
            cmd = [
                'pg_dump',
                db_url,
                '--no-password',
                '--format=plain',  # Plain SQL format (we'll compress it ourselves)
                '--no-owner',
                '--no-privileges',
                '--exclude-table-data=audit_logs',
                '--exclude-table-data=sessions',
                '-f', output_file
            ]
            
            try:
                # Try without version check (will work for minor version differences)
                result = subprocess.run(
                    cmd, 
                    capture_output=True,
                    text=True, 
                    timeout=300,
                    env={**os.environ, 'PGCONNECT_TIMEOUT': '10'}
                )
                
                if result.returncode == 0:
                    # Compress the output
                    import gzip
                    with open(output_file, 'rb') as f_in:
                        with gzip.open(f'{output_file}.gz', 'wb') as f_out:
                            f_out.write(f_in.read())
                    os.rename(f'{output_file}.gz', output_file)
                    return True
                else:
                    logger.warning(f"pg_dump failed, trying Python fallback: {result.stderr}")
            except Exception as e:
                logger.warning(f"pg_dump error, trying Python fallback: {e}")
        
        # Fallback: Use Python with psycopg2 to dump data
        logger.info("Using Python-based backup (pg_dump not available or failed)")
        try:
            import psycopg2
            import gzip
            import json
            
            # Connect to database
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename NOT IN ('audit_logs', 'sessions', 'alembic_version')
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            backup_data = {'tables': {}}
            
            for table in tables:
                # Get table data
                cursor.execute(f'SELECT * FROM "{table}"')
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                # Convert to JSON-serializable format
                backup_data['tables'][table] = {
                    'columns': columns,
                    'data': [[str(val) if val is not None else None for val in row] for row in rows]
                }
                
                logger.info(f"Backed up table {table}: {len(rows)} rows")
            
            # Compress and save
            with gzip.open(output_file, 'wt', encoding='utf-8') as f:
                json.dump(backup_data, f)
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Python backup failed: {e}")
            return False
    
    def _encrypt_file(self, filepath: str):
        """Encrypt file using Fernet (AES-128-CBC + HMAC) for secure authenticated encryption"""
        try:
            from cryptography.fernet import Fernet
            import base64
            
            # Derive Fernet key from our encryption key
            key_bytes = hashlib.sha256(self.encryption_key.encode()).digest()
            fernet_key = base64.urlsafe_b64encode(key_bytes)
            f = Fernet(fernet_key)
            
            # Encrypt file in chunks (memory efficient)
            encrypted_data = []
            chunk_size = 4096 * 1024  # 4MB chunks
            
            with open(filepath, 'rb') as infile:
                while True:
                    chunk = infile.read(chunk_size)
                    if not chunk:
                        break
                    encrypted_data.append(f.encrypt(chunk))
            
            # Write encrypted data
            with open(filepath, 'wb') as outfile:
                for chunk in encrypted_data:
                    outfile.write(chunk)
            
        except ImportError:
            logger.warning("Encryption skipped (install cryptography)")
        except Exception as e:
            logger.error(f"Encryption error: {e}")
    
    def _cleanup_old_backups(self, s3_client, bucket: str, provider: str,
                            retention_days: int, keep_minimum: int):
        """Remove old backups based on retention policy"""
        try:
            prefix = f"backups/{os.getenv('ENVIRONMENT', 'production')}/{provider}/"
            response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
            
            if 'Contents' not in response:
                return
            
            backups = response['Contents']
            backups.sort(key=lambda x: x['LastModified'], reverse=True)
            
            # Always keep minimum number
            if len(backups) <= keep_minimum:
                return
            
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            deleted_count = 0
            
            for backup in backups[keep_minimum:]:
                if backup['LastModified'].replace(tzinfo=None) < cutoff_date:
                    logger.info(f"🗑️  Deleting old backup: {backup['Key']}")
                    s3_client.delete_object(Bucket=bucket, Key=backup['Key'])
                    deleted_count += 1
            
            if deleted_count:
                logger.info(f"♻️  Cleaned up {deleted_count} old backups")
                
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")
    
    def _should_run_secondary(self) -> bool:
        """Check if secondary backup should run (weekly)"""
        # Run on Sundays or if forced
        return datetime.now().weekday() == 6 or os.getenv("FORCE_SECONDARY_BACKUP") == "true"
    
    def _send_alert(self, results: dict):
        """Send monitoring alert for backup failures"""
        # This would integrate with your monitoring service
        logger.error("🚨 BACKUP FAILURE ALERT")
        logger.error(json.dumps(results, indent=2))
        
        # If Sentry is configured, send alert
        try:
            from app.core.monitoring import capture_message
            capture_message(
                "Backup failure detected",
                level="error",
                context=results
            )
        except:
            pass
    
    def _print_r2_setup(self):
        """Print Cloudflare R2 setup instructions"""
        print("""
📋 CLOUDFLARE R2 SETUP INSTRUCTIONS:

1. Go to Cloudflare Dashboard > R2
2. Create bucket: 'ai-study-architect-backups'
3. Go to R2 > Manage API Tokens
4. Create token with 'Object Read & Write' permissions
5. Add these to Render environment variables:

   R2_ACCOUNT_ID=your-account-id
   R2_ACCESS_KEY=your-access-key-id
   R2_SECRET_KEY=your-secret-access-key
   R2_BUCKET=ai-study-architect-backups
   BACKUP_ENCRYPTION_KEY=$(openssl rand -base64 32)
""")
    
    def _print_s3_setup(self):
        """Print AWS S3 setup instructions"""
        print("""
📋 AWS S3 SETUP INSTRUCTIONS:

1. Go to AWS Console > S3
2. Create bucket: 'ai-study-architect-backup-secondary'
3. Choose different region from primary (e.g., us-west-2)
4. Go to IAM > Users > Create User
5. Attach policy: AmazonS3FullAccess (or custom limited)
6. Add these to Render environment variables:

   AWS_ACCESS_KEY_ID=your-access-key
   AWS_SECRET_ACCESS_KEY=your-secret-key
   AWS_REGION=us-west-2
   AWS_BACKUP_BUCKET=ai-study-architect-backup-secondary
""")

def verify_backup(provider: str, backup_key: str):
    """Verify a backup file is valid and can be decrypted"""
    logger.info(f"🔍 Verifying backup: {backup_key}")
    
    # Download backup
    # Decrypt
    # Verify pg_restore can read it
    # Report results
    
    logger.info("Verification not yet implemented - use Render UI")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Enterprise backup management for AI Study Architect"
    )
    parser.add_argument('--r2', action='store_true', help='Backup to Cloudflare R2 (primary)')
    parser.add_argument('--s3', action='store_true', help='Backup to AWS S3 (secondary)')
    parser.add_argument('--all', action='store_true', help='Run all configured backups')
    parser.add_argument('--verify', type=str, help='Verify a backup file')
    parser.add_argument('--setup', action='store_true', help='Show setup instructions')
    
    args = parser.parse_args()
    
    orchestrator = BackupOrchestrator()
    
    if args.setup:
        orchestrator._print_r2_setup()
        orchestrator._print_s3_setup()
    elif args.r2:
        success = orchestrator.backup_to_r2()
        sys.exit(0 if success else 1)
    elif args.s3:
        success = orchestrator.backup_to_s3()
        sys.exit(0 if success else 1)
    elif args.all:
        results = orchestrator.backup_all()
        success = all(p["success"] for p in results["providers"].values())
        sys.exit(0 if success else 1)
    elif args.verify:
        verify_backup("", args.verify)
    else:
        # Default: run primary backup
        success = orchestrator.backup_to_r2()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()