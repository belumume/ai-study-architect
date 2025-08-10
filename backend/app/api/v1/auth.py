"""
Authentication endpoints - Sync version
"""

from datetime import datetime, timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, OAuth2PasswordRequestForm
from sqlalchemy import or_
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.dependencies import get_current_user, get_db
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from app.core.exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    InactiveUserError,
    InvalidTokenError,
    UserNotFoundError,
)
from app.models.user import User
from app.schemas.user import (
    Token,
    UserCreate,
    UserResponse,
    RefreshTokenRequest,
)

router = APIRouter(prefix="/auth")
limiter = Limiter(key_func=get_remote_address)
security = HTTPBearer()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")  # Prevent account creation spam
def register(
    request: Request,
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(
        or_(User.email == user_in.email, User.username == user_in.username)
    ).first()
    
    if existing_user:
        if existing_user.email == user_in.email:
            raise UserAlreadyExistsError(field="email")
        else:
            raise UserAlreadyExistsError(field="username")
    
    # Create new user
    user = User(
        email=user_in.email,
        username=user_in.username,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        is_active=True,
        is_superuser=False,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")  # Prevent brute force attacks
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """
    OAuth2 compatible token login.
    """
    # Find user by email or username
    user = db.query(User).filter(
        or_(
            User.email == form_data.username,
            User.username == form_data.username
        )
    ).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise InvalidCredentialsError()
    
    if not user.is_active:
        raise InactiveUserError()
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # Create tokens
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
@limiter.limit("10/minute")  # Allow more refreshes than login attempts
def refresh_token(
    request: Request,
    token_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Refresh access token using refresh token.
    """
    # Verify refresh token
    user_id = verify_token(token_request.refresh_token, token_type="refresh")
    if not user_id:
        raise InvalidTokenError()
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFoundError()
    if not user.is_active:
        raise InactiveUserError()
    
    # Create new tokens
    access_token = create_access_token(subject=str(user.id))
    new_refresh_token = create_refresh_token(subject=str(user.id))
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout")
@limiter.limit("10/minute")
def logout(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Logout current user.
    
    In a stateless JWT system, logout is typically handled client-side
    by removing the token. This endpoint can be used to blacklist tokens
    or perform other logout operations if needed.
    """
    # Here you could implement token blacklisting if needed
    # For now, we'll just return a success message
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
@limiter.limit("30/minute")
def get_current_user_info(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get current user information.
    """
    return current_user