"""
Common dependencies for API endpoints - Sync version
Supports both Bearer tokens and httpOnly cookies for authentication
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import select
from jose import JWTError

from app.core.database import get_db
from app.core.security import verify_token
from app.core.exceptions import (
    InvalidTokenError,
    UserNotFoundError,
    InactiveUserError,
    PermissionDeniedError,
)
from app.models.user import User

# Security scheme with auto_error=False to allow cookie fallback
security = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from either:
    1. Authorization header (Bearer token) - for backward compatibility
    2. httpOnly cookie - new secure method (industry standard)
    
    Args:
        request: The FastAPI request object
        credentials: The HTTP authorization credentials (optional)
        db: Database session
        
    Returns:
        The current user object
        
    Raises:
        HTTPException: If authentication fails
    """
    token = None
    
    # First, try Authorization header (backward compatibility)
    if credentials and credentials.credentials:
        token = credentials.credentials
    
    # If no header token, try cookie (new secure method)
    if not token:
        token = request.cookies.get("access_token")
    
    # If still no token, raise unauthorized
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify the token
    try:
        user_id = verify_token(token, token_type="access")
        if not user_id:
            raise InvalidTokenError()
    except Exception:
        raise InvalidTokenError()
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise UserNotFoundError()
    
    if not user.is_active:
        raise InactiveUserError()
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.
    
    Args:
        current_user: The current user from token
        
    Returns:
        The current active user
        
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise InactiveUserError()
    return current_user


def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current superuser.
    
    Args:
        current_user: The current user from token
        
    Returns:
        The current superuser
        
    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise PermissionDeniedError(detail="Superuser access required")
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.
    
    Args:
        credentials: Optional HTTP authorization credentials
        db: Database session
        
    Returns:
        The current user or None
    """
    if not credentials:
        return None
        
    try:
        return get_current_user(credentials, db)
    except (InvalidTokenError, UserNotFoundError, InactiveUserError):
        return None


async def get_current_user_ws(token: str, db: Session) -> Optional[User]:
    """
    Get current user from WebSocket token.
    
    Args:
        token: JWT token string
        db: Database session
        
    Returns:
        The current user or None
    """
    try:
        # Verify the token
        user_id = verify_token(token, token_type="access")
        if not user_id:
            return None
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            return None
            
        return user
    except (JWTError, Exception):
        return None