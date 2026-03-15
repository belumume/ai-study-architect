"""
Backup endpoint for triggering database backups.
Protected by a secret token for security.
"""

import logging
import os
import subprocess
import time
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel

from app.core.utils import utcnow

logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic model for backup request
class BackupRequest(BaseModel):
    provider: str = "s3"


# Backup token — fail closed if not configured
BACKUP_TOKEN = os.getenv("BACKUP_TOKEN")
if not BACKUP_TOKEN:
    logger.critical("BACKUP_TOKEN not configured — backup endpoint will reject all requests")
    BACKUP_TOKEN = None

# Rate limiting: track last backup time
last_backup_time = None
MIN_BACKUP_INTERVAL = 3600  # 1 hour minimum between manual backups


async def verify_backup_token(x_backup_token: str | None = Header(None), request: Request = None):
    """Verify the backup token. Authentication only — rate limiting is on /trigger."""
    # Log attempt for security monitoring
    client_ip = request.client.host if request and request.client else "unknown"
    user_agent = request.headers.get("user-agent", "") if request else ""
    logger.info(f"Backup attempt from IP: {client_ip}, User-Agent: {user_agent}")

    # Check token — fail closed if BACKUP_TOKEN not configured
    if BACKUP_TOKEN is None:
        logger.error(f"Backup rejected — BACKUP_TOKEN not configured. IP: {client_ip}")
        raise HTTPException(status_code=503, detail="Backup service not configured")
    if not x_backup_token or x_backup_token != BACKUP_TOKEN:
        logger.warning(f"Invalid backup token attempt from IP: {client_ip}")
        raise HTTPException(status_code=403, detail="Forbidden")

    return True


def _check_trigger_rate_limit(request: Request | None = None):
    """Rate limit check for /trigger only. Raises 429 if called too soon."""
    global last_backup_time

    is_test_mode = os.getenv("BACKUP_TEST_MODE", "false").lower() == "true"
    if is_test_mode:
        logger.info("Test mode enabled - rate limiting bypassed")
        return

    current_time = time.time()
    if last_backup_time and (current_time - last_backup_time) < MIN_BACKUP_INTERVAL:
        remaining_seconds = MIN_BACKUP_INTERVAL - (current_time - last_backup_time)
        client_ip = request.client.host if request and request.client else "unknown"
        logger.warning(f"Rate limit hit from IP: {client_ip}. Wait {remaining_seconds:.0f}s")
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit: wait {remaining_seconds:.0f} seconds before next backup",
        )


@router.post("/trigger")
async def trigger_backup(
    backup_request: BackupRequest,
    authorized: bool = Depends(verify_backup_token),
    request: Request = None,
):
    """
    Trigger a database backup.
    Protected by secret token and rate limiting (except for GitHub Actions).
    """
    global last_backup_time

    _check_trigger_rate_limit(request)

    provider = backup_request.provider

    # Validate provider
    if provider not in ["s3", "r2", "both"]:
        raise HTTPException(status_code=400, detail="Invalid provider. Use 's3', 'r2', or 'both'")

    try:
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
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )

            if result.returncode != 0:
                logger.error(
                    f"{current_provider.upper()} backup failed with code {result.returncode}"
                )
                logger.error(f"STDOUT: {result.stdout}")
                logger.error(f"STDERR: {result.stderr}")

                # For "both", continue with next provider even if one fails
                if provider == "both":
                    results.append(
                        {
                            "provider": current_provider,
                            "status": "failed",
                        }
                    )
                    continue
                else:
                    logger.error(
                        f"{current_provider.upper()} backup failed: "
                        f"stdout={result.stdout[-500:]}, stderr={result.stderr[-500:]}"
                    )
                    raise HTTPException(
                        status_code=500,
                        detail=f"{current_provider.upper()} backup failed",
                    )
            else:
                logger.info(f"Backup to {current_provider.upper()} completed successfully")
                results.append({"provider": current_provider, "status": "success"})

        # Return results
        if provider == "both":
            success_count = sum(1 for r in results if r["status"] == "success")
            if success_count > 0:
                last_backup_time = time.time()
            return {
                "status": "partial"
                if 0 < success_count < len(results)
                else ("success" if success_count == len(results) else "failed"),
                "message": f"Backup completed: {success_count}/{len(results)} successful",
                "details": results,
                "timestamp": utcnow().isoformat(),
            }
        else:
            last_backup_time = time.time()
            return {
                "status": "success",
                "message": f"{provider.upper()} backup completed",
                "timestamp": utcnow().isoformat(),
            }
    except subprocess.TimeoutExpired:
        logger.error("Backup operation timed out")
        raise HTTPException(status_code=504, detail="Operation timed out")
    except Exception as e:
        logger.error(f"Backup error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Backup failed unexpectedly",
        )


@router.get("/status")
async def backup_status(authorized: bool = Depends(verify_backup_token)):
    """Check if backup service is ready"""
    test_mode = os.getenv("BACKUP_TEST_MODE", "false").lower() == "true"
    return {
        "status": "ready",
        "providers": {
            "aws_s3": "configured" if os.getenv("AWS_ACCESS_KEY_ID") else "not configured",
            "cloudflare_r2": "configured"
            if (os.getenv("R2_ACCESS_KEY") and os.getenv("R2_SECRET_KEY"))
            else "not configured",
        },
        "encryption": "enabled" if os.getenv("BACKUP_ENCRYPTION_KEY") else "WARNING: disabled",
        "last_backup": datetime.fromtimestamp(last_backup_time).isoformat()
        if last_backup_time
        else None,
        "rate_limit": f"{MIN_BACKUP_INTERVAL} seconds{' (DISABLED - test mode active)' if test_mode else ''}",
        "test_mode": test_mode,
        "retention_policies": {
            "r2": "30 days, min 7 backups (controlled by our code)",
            "s3": "14 days, min 3 backups (controlled by our code)",
        },
    }


@router.post("/test")
async def test_backup_setup(authorized: bool = Depends(verify_backup_token)):
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
        "script_locations_checked": [],
    }

    # Check for backup script in various locations
    possible_paths = [
        "/opt/render/project/src/project/backend/scripts/backup_database.py",
        "/opt/render/project/src/backend/scripts/backup_database.py",
        "scripts/backup_database.py",
        os.path.join(os.getcwd(), "scripts", "backup_database.py"),
    ]

    for path in possible_paths:
        checks["script_locations_checked"].append({"path": path, "exists": os.path.exists(path)})

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
                    region_name="auto",
                )
                checks["r2_client_creation"] = "success"
            except Exception as e:
                checks["r2_client_creation"] = "failed"
    except ImportError:
        checks["boto3_installed"] = False

    try:
        from cryptography.fernet import Fernet

        checks["cryptography_installed"] = True
    except ImportError:
        checks["cryptography_installed"] = False

    return checks


@router.post("/debug")
async def debug_backup(authorized: bool = Depends(verify_backup_token)):
    """Debug backup by running a simple pg_dump test"""
    import shutil
    import subprocess

    result = {
        "pg_dump_path": shutil.which("pg_dump"),
        "database_url_set": bool(os.getenv("DATABASE_URL")),
        "render_env": os.getenv("RENDER", "not set"),
        "aws_keys_set": bool(os.getenv("AWS_ACCESS_KEY_ID")),
    }

    # Try a simple pg_dump version check
    try:
        version = subprocess.run(
            ["pg_dump", "--version"], capture_output=True, text=True, timeout=5
        )
        result["pg_dump_version"] = version.stdout.strip()
    except Exception:
        result["pg_dump_version"] = "unavailable"

    # Try to connect to database using SQLAlchemy (no credential exposure via CLI)
    if os.getenv("DATABASE_URL"):
        try:
            from app.core.database import engine

            with engine.connect() as conn:
                from sqlalchemy import text

                row = conn.execute(
                    text("SELECT tablename FROM pg_tables WHERE schemaname='public' LIMIT 1")
                ).fetchone()
                result["database_connection"] = "SUCCESS"
                result["sample_table"] = row[0] if row else "no tables"
        except Exception as e:
            result["database_connection"] = "FAILED"
            result["connection_error"] = type(e).__name__

    return result
