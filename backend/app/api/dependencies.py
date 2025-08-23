"""
Common dependencies for API endpoints - Sync version
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
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

# Security scheme
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    Args:
        credentials: The HTTP authorization credentials
        db: Database session
        
    Returns:
        The current user object
        
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    
    # Verify the token
    user_id = verify_token(token, token_type="access")
    if not user_id:
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