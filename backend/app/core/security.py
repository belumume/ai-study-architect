"""
Security utilities for authentication and authorization
"""

import logging
import threading
import time
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.rsa_keys import key_manager

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Global key storage with thread safety
_key_lock = threading.RLock()
_current_keys: dict[str, str | float] = {}
_archived_keys: list[dict[str, Any]] = []

# Initialize RSA keys for JWT
try:
    PRIVATE_KEY, PUBLIC_KEY = key_manager.initialize_keys()
    with _key_lock:
        _current_keys = {
            "private": PRIVATE_KEY,
            "public": PUBLIC_KEY,
            "created_at": time.time(),
            "key_id": "initial",
        }
    logger.info("RSA keys initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize RSA keys: {e}")
    # Fallback to HS256 if RSA fails
    PRIVATE_KEY = PUBLIC_KEY = None


def get_current_keys() -> dict[str, str]:
    """Get current RSA keys thread-safely"""
    with _key_lock:
        return _current_keys.copy()


def rotate_jwt_keys() -> dict[str, str]:
    """
    Rotate JWT RSA keys and archive the old ones.

    Returns:
        Dictionary containing the new keys and metadata
    """
    global PRIVATE_KEY, PUBLIC_KEY

    with _key_lock:
        try:
            # Archive current keys if they exist
            if _current_keys:
                archived_key = {**_current_keys, "archived_at": time.time(), "status": "archived"}
                _archived_keys.append(archived_key)
                logger.info(f"Archived JWT key with ID: {_current_keys.get('key_id')}")

            # Generate new keys
            new_private, new_public = key_manager.rotate_keys()
            key_id = f"key_{int(time.time())}"

            # Update global keys
            PRIVATE_KEY = new_private
            PUBLIC_KEY = new_public

            # Update current keys storage
            _current_keys.update(
                {
                    "private": new_private,
                    "public": new_public,
                    "created_at": time.time(),
                    "key_id": key_id,
                    "status": "active",
                }
            )

            logger.info(f"JWT keys rotated successfully. New key ID: {key_id}")

            # Keep only last 5 archived keys to prevent memory bloat
            if len(_archived_keys) > 5:
                removed = _archived_keys.pop(0)
                logger.info(f"Removed old archived key: {removed.get('key_id')}")

            return {
                "key_id": key_id,
                "created_at": _current_keys["created_at"],
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Failed to rotate JWT keys: {e}")
            return {"status": "error", "error": str(e)}


def create_access_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
    family_id: str | None = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        subject: The subject of the token (usually user ID)
        expires_delta: Optional custom expiration time
        family_id: Optional refresh token family ID (for token rotation tracking)

    Returns:
        Encoded JWT token
    """
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    current_keys = get_current_keys()
    kid = current_keys.get("key_id", "fallback")
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
    }
    if family_id:
        to_encode["fid"] = family_id

    # Use RS256 if RSA keys are available, otherwise fallback to HS256
    # kid goes in the JWT header per RFC 7515, not the payload
    if current_keys.get("private"):
        encoded_jwt = jwt.encode(
            to_encode, current_keys["private"], algorithm="RS256", headers={"kid": kid}
        )
    else:
        encoded_jwt = jwt.encode(
            to_encode, settings.JWT_SECRET_KEY, algorithm="HS256", headers={"kid": kid}
        )
    return encoded_jwt


def create_refresh_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
    family_id: str | None = None,
) -> str:
    """
    Create a JWT refresh token.

    Args:
        subject: The subject of the token (usually user ID)
        expires_delta: Optional custom expiration time
        family_id: Optional token family ID for rotation tracking

    Returns:
        Encoded JWT refresh token
    """
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    current_keys = get_current_keys()
    kid = current_keys.get("key_id", "fallback")
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
    }
    if family_id:
        to_encode["fid"] = family_id

    # Use RS256 if RSA keys are available, otherwise fallback to HS256
    # kid goes in the JWT header per RFC 7515, not the payload
    if current_keys.get("private"):
        encoded_jwt = jwt.encode(
            to_encode, current_keys["private"], algorithm="RS256", headers={"kid": kid}
        )
    else:
        encoded_jwt = jwt.encode(
            to_encode, settings.JWT_SECRET_KEY, algorithm="HS256", headers={"kid": kid}
        )
    return encoded_jwt


def _find_key_for_token(token: str) -> str | None:
    """
    Find the appropriate public key for token verification.
    Tries current key first, then archived keys for graceful rotation.
    """
    try:
        # Read kid from JWT header per RFC 7515 (falls back to claims for old tokens)
        unverified_header = jwt.get_unverified_header(token)
        token_kid = unverified_header.get("kid")
        if not token_kid:
            unverified_payload = jwt.get_unverified_claims(token)
            token_kid = unverified_payload.get("kid")

        with _key_lock:
            # Try current key first
            current_keys = _current_keys.copy()
            if token_kid == current_keys.get("key_id") or not token_kid:
                return current_keys.get("public")

            # Try archived keys for graceful rotation
            for archived_key in reversed(_archived_keys):  # Most recent first
                if token_kid == archived_key.get("key_id"):
                    return archived_key.get("public")

        return None
    except Exception:
        # If we can't decode the token, return current key as fallback
        current_keys = get_current_keys()
        return current_keys.get("public")


def verify_token(token: str, token_type: str = "access") -> str | None:
    """
    Verify and decode a JWT token with rotation support.

    Args:
        token: The JWT token to verify
        token_type: Expected token type ("access" or "refresh")

    Returns:
        The subject (user ID) if valid, None otherwise
    """
    claims = verify_token_claims(token, token_type)
    if claims is None:
        return None
    return claims.get("sub")


def verify_token_claims(token: str, token_type: str = "access") -> dict | None:
    """
    Verify and decode a JWT token, returning the full claims dict.

    Args:
        token: The JWT token to verify
        token_type: Expected token type ("access" or "refresh")

    Returns:
        The full claims dict if valid, None otherwise
    """
    try:
        payload = None

        # Try RS256 with rotation support
        public_key = _find_key_for_token(token)
        if public_key:
            try:
                payload = jwt.decode(token, public_key, algorithms=["RS256"])
            except JWTError as e:
                logger.debug(f"RS256 verification failed: {e}")

        # Fallback to HS256 for backward compatibility
        if payload is None:
            try:
                payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
            except JWTError as e:
                logger.debug(f"HS256 verification failed: {e}")
                return None

        # Verify token type
        if payload.get("type") != token_type:
            logger.debug(f"Token type mismatch: expected {token_type}, got {payload.get('type')}")
            return None

        subject: str = payload.get("sub")
        if subject is None:
            logger.debug("No subject found in token")
            return None

        return payload
    except Exception as e:
        logger.debug(f"Token verification failed: {e}")
        return None


def get_key_rotation_info() -> dict[str, Any]:
    """
    Get information about key rotation status.

    Returns:
        Dictionary with current and archived key information
    """
    with _key_lock:
        return {
            "current_key": {
                "key_id": _current_keys.get("key_id"),
                "created_at": _current_keys.get("created_at"),
                "status": _current_keys.get("status", "active"),
            },
            "archived_keys_count": len(_archived_keys),
            "last_rotation": _archived_keys[-1].get("archived_at") if _archived_keys else None,
            "rotation_available": bool(_current_keys.get("private")),
        }


def _truncate_for_bcrypt(password: str) -> str:
    """Prepare password for bcrypt: strip NULL bytes and truncate to 72 bytes."""
    clean = password.replace("\x00", "")
    encoded = clean.encode("utf-8")[:72]
    return encoded.decode("utf-8", errors="ignore")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(_truncate_for_bcrypt(plain_password), hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(_truncate_for_bcrypt(password))
