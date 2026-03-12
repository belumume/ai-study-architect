"""R2/S3-compatible object storage service."""

import logging
from typing import Optional
import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_s3_client():
    """Create boto3 S3 client configured for R2."""
    if not settings.R2_ENDPOINT_URL:
        logger.warning("R2 not configured (R2_ENDPOINT_URL not set)")
        return None
    return boto3.client(
        "s3",
        endpoint_url=settings.R2_ENDPOINT_URL,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
    )


def upload_file(key: str, data: bytes, content_type: str = "application/octet-stream") -> bool:
    """Upload bytes to R2. Returns True on success."""
    client = _get_s3_client()
    if not client:
        return False
    try:
        client.put_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return True
    except ClientError as e:
        logger.error(f"R2 upload failed for {key}: {e}")
        return False


def download_file(key: str) -> Optional[bytes]:
    """Download bytes from R2. Returns None on failure."""
    client = _get_s3_client()
    if not client:
        return None
    try:
        response = client.get_object(Bucket=settings.R2_BUCKET_NAME, Key=key)
        return response["Body"].read()
    except ClientError as e:
        logger.error(f"R2 download failed for {key}: {e}")
        return None


def delete_file(key: str) -> bool:
    """Delete object from R2. Returns True on success."""
    client = _get_s3_client()
    if not client:
        return False
    try:
        client.delete_object(Bucket=settings.R2_BUCKET_NAME, Key=key)
        return True
    except ClientError as e:
        logger.error(f"R2 delete failed for {key}: {e}")
        return False


def generate_presigned_url(key: str, expires_in: int = 3600) -> Optional[str]:
    """Generate a presigned download URL. Returns None on failure."""
    client = _get_s3_client()
    if not client:
        return None
    try:
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.R2_BUCKET_NAME, "Key": key},
            ExpiresIn=expires_in,
        )
    except ClientError as e:
        logger.error(f"R2 presigned URL failed for {key}: {e}")
        return None
