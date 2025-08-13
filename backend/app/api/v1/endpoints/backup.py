"""
Backup endpoint for triggering database backups.
Protected by a secret token for security.
"""
import os
import subprocess
import tempfile
import hashlib
import time
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from typing import Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic model for backup request
class BackupRequest(BaseModel):
    provider: str = "s3"

# Generate a secure backup token on startup
BACKUP_TOKEN = os.getenv("BACKUP_TOKEN")
if not BACKUP_TOKEN:
    logger.error("BACKUP_TOKEN not configured!")
    BACKUP_TOKEN = "not-configured"

# Rate limiting: track last backup time
last_backup_time = None
MIN_BACKUP_INTERVAL = 300  # 5 minutes for testing (TODO: change back to 3600 after testing)

async def verify_backup_token(
    x_backup_token: Optional[str] = Header(None),
    request: Request = None
):
    """Verify the backup token with rate limiting and logging"""
    global last_backup_time
    
    # Log attempt for security monitoring
    client_ip = request.client.host if request else "unknown"
    user_agent = request.headers.get("user-agent", "") if request else ""
    logger.info(f"Backup attempt from IP: {client_ip}, User-Agent: {user_agent}")
    
    # Check token
    if not x_backup_token or x_backup_token != BACKUP_TOKEN:
        logger.warning(f"Invalid backup token attempt from IP: {client_ip}")
        raise HTTPException(status_code=403, detail="Forbidden")
    
    # During testing phase, we'll be more lenient with rate limiting
    # After testing is complete, remove BACKUP_TEST_MODE and increase MIN_BACKUP_INTERVAL to 3600
    is_test_mode = os.getenv("BACKUP_TEST_MODE", "false").lower() == "true"
    
    # Apply rate limiting (unless in test mode)
    if not is_test_mode:
        # Check rate limiting for manual triggers
        current_time = time.time()
        if last_backup_time and (current_time - last_backup_time) < MIN_BACKUP_INTERVAL:
            remaining_seconds = MIN_BACKUP_INTERVAL - (current_time - last_backup_time)
            logger.warning(f"Rate limit hit from IP: {client_ip}. Wait {remaining_seconds:.0f}s")
            raise HTTPException(
                status_code=429, 
                detail=f"Rate limit: wait {remaining_seconds:.0f} seconds before next backup"
            )
    else:
        logger.info("Test mode enabled - rate limiting bypassed")
    
    return True

@router.post("/trigger")
async def trigger_backup(
    backup_request: BackupRequest,
    authorized: bool = Depends(verify_backup_token),
    request: Request = None
):
    """
    Trigger a database backup.
    Protected by secret token and rate limiting (except for GitHub Actions).
    """
    global last_backup_time
    
    provider = backup_request.provider
    
    # Validate provider
    if provider not in ["s3", "r2", "both"]:
        raise HTTPException(status_code=400, detail="Invalid provider. Use 's3', 'r2', or 'both'")
    
    try:
        # Update last backup time
        last_backup_time = time.time()
        
        # Check if we're on Render or local
        if os.path.exists("/opt/render/project/src/project/backend"):
            work_dir = "/opt/render/project/src/project/backend"
        elif os.path.exists("/opt/render/project/src/backend"):
            work_dir = "/opt/render/project/src/backend"
        else:
            # Fallback to current directory
            work_dir = os.getcwd()
            
        # Ensure script exists
        script_path = os.path.join(work_dir, "scripts", "backup_database.py")
        if not os.path.exists(script_path):
            logger.error(f"Backup script not found at {script_path}")
            raise HTTPException(status_code=500, detail="Backup configuration error")
        
        # Handle "both" provider option
        providers_to_run = ["r2", "s3"] if provider == "both" else [provider]
        results = []
        
        for current_provider in providers_to_run:
            logger.info(f"Starting {current_provider.upper()} backup from {work_dir}...")
            
            # Run the backup script
            result = subprocess.run(
                ["python", script_path, f"--{current_provider}"],
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
            )
            
            if result.returncode != 0:
                logger.error(f"{current_provider.upper()} backup failed with code {result.returncode}")
                logger.error(f"STDOUT: {result.stdout}")
                logger.error(f"STDERR: {result.stderr}")
                
                # For "both", continue with next provider even if one fails
                if provider == "both":
                    results.append({
                        "provider": current_provider,
                        "status": "failed",
                        "error": result.stderr[-500:] if result.stderr else "Unknown error"
                    })
                    continue
                else:
                    # Return actual error for debugging
                    raise HTTPException(status_code=500, detail={
                        "error": f"{current_provider.upper()} backup failed",
                        "stdout": result.stdout[-1000:] if result.stdout else None,
                        "stderr": result.stderr[-1000:] if result.stderr else None,
                        "return_code": result.returncode
                    })
            else:
                logger.info(f"Backup to {current_provider.upper()} completed successfully")
                results.append({
                    "provider": current_provider,
                    "status": "success"
                })
        
        # Return results
        if provider == "both":
            success_count = sum(1 for r in results if r["status"] == "success")
            return {
                "status": "partial" if 0 < success_count < len(results) else ("success" if success_count == len(results) else "failed"),
                "message": f"Backup completed: {success_count}/{len(results)} successful",
                "details": results,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "status": "success",
                "message": f"{provider.upper()} backup completed",
                "timestamp": datetime.utcnow().isoformat()
            }
    except subprocess.TimeoutExpired:
        logger.error("Backup operation timed out")
        raise HTTPException(status_code=504, detail="Operation timed out")
    except Exception as e:
        logger.error(f"Backup error: {str(e)}")
        # For debugging - show the actual error
        import traceback
        raise HTTPException(status_code=500, detail={
            "error": str(e),
            "type": type(e).__name__,
            "traceback": traceback.format_exc()[-1000:]  # Last 1000 chars of traceback
        })

@router.get("/status")
async def backup_status(authorized: bool = Depends(verify_backup_token)):
    """Check if backup service is ready"""
    test_mode = os.getenv("BACKUP_TEST_MODE", "false").lower() == "true"
    return {
        "status": "ready",
        "providers": {
            "aws_s3": "configured" if os.getenv("AWS_ACCESS_KEY_ID") else "not configured",
            "cloudflare_r2": "configured" if (os.getenv("R2_ACCESS_KEY") and os.getenv("R2_SECRET_KEY")) else "not configured"
        },
        "encryption": "enabled" if os.getenv("BACKUP_ENCRYPTION_KEY") else "WARNING: disabled",
        "last_backup": datetime.fromtimestamp(last_backup_time).isoformat() if last_backup_time else None,
        "rate_limit": f"{MIN_BACKUP_INTERVAL} seconds{' (DISABLED - test mode active)' if test_mode else ''}",
        "test_mode": test_mode,
        "retention_policies": {
            "r2": "30 days, min 7 backups (controlled by our code)",
            "s3": "14 days, min 3 backups (controlled by our code)"
        }
    }

@router.post("/test")
async def test_backup_setup(
    authorized: bool = Depends(verify_backup_token)
):
    """Test backup configuration without actually running backup"""
    import shutil
    
    checks = {
        "token_configured": bool(os.getenv("BACKUP_TOKEN")),
        "aws_configured": bool(os.getenv("AWS_ACCESS_KEY_ID")),
        "r2_configured": bool(os.getenv("R2_ACCESS_KEY") and os.getenv("R2_SECRET_KEY")),
        "encryption_configured": bool(os.getenv("BACKUP_ENCRYPTION_KEY")),
        "database_url_configured": bool(os.getenv("DATABASE_URL")),
        "pg_dump_available": bool(shutil.which("pg_dump")),
        "current_directory": os.getcwd(),
        "script_locations_checked": []
    }
    
    # Check for backup script in various locations
    possible_paths = [
        "/opt/render/project/src/project/backend/scripts/backup_database.py",
        "/opt/render/project/src/backend/scripts/backup_database.py",
        "scripts/backup_database.py",
        os.path.join(os.getcwd(), "scripts", "backup_database.py")
    ]
    
    for path in possible_paths:
        checks["script_locations_checked"].append({
            "path": path,
            "exists": os.path.exists(path)
        })
    
    # Try to import required modules
    try:
        import boto3
        checks["boto3_installed"] = True
        
        # Test R2 client creation if configured
        if os.getenv("R2_ACCESS_KEY") and os.getenv("R2_SECRET_KEY"):
            try:
                r2_client = boto3.client(
                    "s3",
                    endpoint_url=f"https://{os.getenv('R2_ACCOUNT_ID', '')}.r2.cloudflarestorage.com",
                    aws_access_key_id=os.getenv("R2_ACCESS_KEY"),
                    aws_secret_access_key=os.getenv("R2_SECRET_KEY"),
                    region_name="auto"
                )
                checks["r2_client_creation"] = "success"
            except Exception as e:
                checks["r2_client_creation"] = f"failed: {str(e)[:100]}"
    except ImportError:
        checks["boto3_installed"] = False
    
    try:
        from cryptography.fernet import Fernet
        checks["cryptography_installed"] = True
    except ImportError:
        checks["cryptography_installed"] = False
    
    return checks

@router.post("/debug")
async def debug_backup(
    authorized: bool = Depends(verify_backup_token)
):
    """Debug backup by running a simple pg_dump test"""
    import subprocess
    import shutil
    
    result = {
        "pg_dump_path": shutil.which("pg_dump"),
        "database_url_set": bool(os.getenv("DATABASE_URL")),
        "render_env": os.getenv("RENDER", "not set"),
        "aws_keys_set": bool(os.getenv("AWS_ACCESS_KEY_ID")),
    }
    
    # Try a simple pg_dump version check
    try:
        version = subprocess.run(
            ["pg_dump", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        result["pg_dump_version"] = version.stdout.strip()
    except Exception as e:
        result["pg_dump_version"] = f"Error: {str(e)}"
    
    # Try to connect to database
    if os.getenv("DATABASE_URL"):
        try:
            db_url = os.getenv("DATABASE_URL")
            # Just try to list tables (quick test)
            test_cmd = [
                "psql",
                db_url,
                "-c", "SELECT tablename FROM pg_tables WHERE schemaname='public' LIMIT 1;",
                "-t"  # Tuples only
            ]
            
            test_result = subprocess.run(
                test_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if test_result.returncode == 0:
                result["database_connection"] = "SUCCESS"
                result["sample_table"] = test_result.stdout.strip()
            else:
                result["database_connection"] = "FAILED"
                result["connection_error"] = test_result.stderr[:500]
        except Exception as e:
            result["database_connection"] = "ERROR"
            result["connection_error"] = str(e)[:500]
    
    return result