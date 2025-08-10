#!/usr/bin/env python3
"""
Python-only database backup (no pg_dump required).
Uses SQLAlchemy to export data directly.
"""

import os
import sys
import json
import gzip
import hashlib
import tempfile
from datetime import datetime
from pathlib import Path
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
import boto3
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PythonBackup:
    """Pure Python backup without pg_dump"""
    
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine)
        
    def backup_to_json(self, output_file: str):
        """Export all tables to compressed JSON"""
        logger.info("📊 Exporting database to JSON...")
        
        backup_data = {
            "timestamp": datetime.now().isoformat(),
            "database": settings.DATABASE_URL.split('/')[-1].split('?')[0],
            "tables": {}
        }
        
        Session = sessionmaker(bind=self.engine)
        session = Session()
        
        try:
            # Export each table
            for table_name in self.metadata.tables:
                logger.info(f"  Exporting table: {table_name}")
                table = self.metadata.tables[table_name]
                
                # Get all rows
                result = session.execute(table.select())
                rows = []
                for row in result:
                    row_dict = dict(row._mapping)
                    # Convert datetime objects to strings
                    for key, value in row_dict.items():
                        if hasattr(value, 'isoformat'):
                            row_dict[key] = value.isoformat()
                    rows.append(row_dict)
                
                backup_data["tables"][table_name] = {
                    "columns": [col.name for col in table.columns],
                    "rows": rows,
                    "row_count": len(rows)
                }
                
            # Compress and save
            logger.info("🗜️  Compressing backup...")
            with gzip.open(output_file, 'wt', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2)
                
            file_size = os.path.getsize(output_file) / (1024 * 1024)
            logger.info(f"✅ Backup created: {file_size:.2f} MB")
            return True
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False
        finally:
            session.close()
    
    def upload_to_s3(self, local_file: str):
        """Upload backup to S3"""
        logger.info("📤 Uploading to S3...")
        
        access_key = os.getenv("AWS_ACCESS_KEY_ID")
        secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        bucket = os.getenv("AWS_BACKUP_BUCKET", "ai-study-architect-backup-2025")
        region = os.getenv("AWS_REGION", "us-west-2")
        
        if not all([access_key, secret_key]):
            logger.error("AWS credentials not set")
            return False
        
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            s3_key = f"backups/python/{timestamp}_backup.json.gz"
            
            s3_client.upload_file(
                local_file,
                bucket,
                s3_key,
                ExtraArgs={
                    'StorageClass': 'STANDARD_IA',
                    'ServerSideEncryption': 'AES256'
                }
            )
            
            logger.info(f"✅ Uploaded to s3://{bucket}/{s3_key}")
            return True
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return False

def main():
    """Run Python-only backup"""
    logger.info("🐍 Python-only backup (no pg_dump needed)")
    
    backup = PythonBackup()
    
    with tempfile.NamedTemporaryFile(suffix='.json.gz', delete=False) as tmp:
        try:
            # Create backup
            if backup.backup_to_json(tmp.name):
                # Upload to S3
                if backup.upload_to_s3(tmp.name):
                    logger.info("🎉 Backup complete!")
                else:
                    logger.error("Upload failed")
            else:
                logger.error("Backup creation failed")
        finally:
            # Clean up temp file
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

if __name__ == "__main__":
    main()