"""
Security utilities for authentication and authorization
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union, Dict, List
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging
import threading
import time

from app.core.config import settings
from app.core.rsa_keys import key_manager

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Global key storage with thread safety
_key_lock = threading.RLock()
_current_keys: Dict[str, str] = {}
_archived_keys: List[Dict[str, Any]] = []

# Initialize RSA keys for JWT
try:
    PRIVATE_KEY, PUBLIC_KEY = key_manager.initialize_keys()
    with _key_lock:
        _current_keys = {
            "private": PRIVATE_KEY,
            "public": PUBLIC_KEY,
            "created_at": time.time(),
            "key_id": "initial"
        }
    logger.info("RSA keys initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize RSA keys: {e}")
    # Fallback to HS256 if RSA fails
    PRIVATE_KEY = PUBLIC_KEY = None


def get_current_keys() -> Dict[str, str]:
    """Get current RSA keys thread-safely"""
    with _key_lock:
        return _current_keys.copy()


def rotate_jwt_keys() -> Dict[str, str]:
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
                archived_key = {
                    **_current_keys,
                    "archived_at": time.time(),
                    "status": "archived"
                }
                _archived_keys.append(archived_key)
                logger.info(f"Archived JWT key with ID: {_current_keys.get('key_id')}")
            
            # Generate new keys
            new_private, new_public = key_manager.rotate_keys()
            key_id = f"key_{int(time.time())}"
            
            # Update global keys
            PRIVATE_KEY = new_private
            PUBLIC_KEY = new_public
            
            # Update current keys storage
            _current_keys.update({
                "private": new_private,
                "public": new_public,
                "created_at": time.time(),
                "key_id": key_id,
                "status": "active"
            })
            
            logger.info(f"JWT keys rotated successfully. New key ID: {key_id}")
            
            # Keep only last 5 archived keys to prevent memory bloat
            if len(_archived_keys) > 5:
                removed = _archived_keys.pop(0)
                logger.info(f"Removed old archived key: {removed.get('key_id')}")
            
            return {
                "key_id": key_id,
                "created_at": _current_keys["created_at"],
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Failed to rotate JWT keys: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


def create_access_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: The subject of the token (usually user ID)
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    current_keys = get_current_keys()
    to_encode = {
        "exp": expire, 
        "sub": str(subject), 
        "type": "access",
        "kid": current_keys.get("key_id", "fallback")  # Key ID for rotation support
    }
    
    # Use RS256 if RSA keys are available, otherwise fallback to HS256
    if current_keys.get("private"):
        encoded_jwt = jwt.encode(
            to_encode, 
            current_keys["private"], 
            algorithm="RS256"
        )
    else:
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.JWT_SECRET_KEY, 
            algorithm="HS256"
        )
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        subject: The subject of the token (usually user ID)
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT refresh token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    current_keys = get_current_keys()
    to_encode = {
        "exp": expire, 
        "sub": str(subject), 
        "type": "refresh",
        "kid": current_keys.get("key_id", "fallback")  # Key ID for rotation support
    }
    
    # Use RS256 if RSA keys are available, otherwise fallback to HS256
    if current_keys.get("private"):
        encoded_jwt = jwt.encode(
            to_encode,
            current_keys["private"],
            algorithm="RS256"
        )
    else:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm="HS256"
        )
    return encoded_jwt


def _find_key_for_token(token: str) -> Optional[str]:
    """
    Find the appropriate public key for token verification.
    Tries current key first, then archived keys for graceful rotation.
    """
    try:
        # Decode without verification to get the key ID
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


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """
    Verify and decode a JWT token with rotation support.
    
    Args:
        token: The JWT token to verify
        token_type: Expected token type ("access" or "refresh")
        
    Returns:
        The subject (user ID) if valid, None otherwise
    """
    try:
        payload = None
        
        # Try RS256 with rotation support
        public_key = _find_key_for_token(token)
        if public_key:
            try:
                payload = jwt.decode(
                    token, 
                    public_key, 
                    algorithms=["RS256"]
                )
            except JWTError as e:
                logger.debug(f"RS256 verification failed: {e}")
                
        # Fallback to HS256 for backward compatibility
        if payload is None:
            try:
                payload = jwt.decode(
                    token, 
                    settings.JWT_SECRET_KEY, 
                    algorithms=["HS256"]
                )
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
            
        return subject
    except Exception as e:
        logger.debug(f"Token verification failed: {e}")
        return None


def get_key_rotation_info() -> Dict[str, Any]:
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
                "status": _current_keys.get("status", "active")
            },
            "archived_keys_count": len(_archived_keys),
            "last_rotation": _archived_keys[-1].get("archived_at") if _archived_keys else None,
            "rotation_available": bool(_current_keys.get("private"))
        }


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        The hashed password
    """
    return pwd_context.hash(password)