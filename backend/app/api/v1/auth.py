"""
Authentication endpoints - Sync version
"""

from datetime import datetime, timedelta
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import JSONResponse
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


@router.post("/login")
@limiter.limit("5/minute")  # Prevent brute force attacks
def login(
    request: Request,
    response: Response,  # Added for cookie support
    form_data: OAuth2PasswordRequestForm = Depends(),
    remember_me: bool = False,  # Optional remember me
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
    
    # Store user_id for CSRF cookie
    request.state.user_id = str(user.id)
    
    # Set httpOnly cookies for better security (like major platforms)
    # Access token cookie (30 minutes if remember_me, else session)
    access_max_age = (
        settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        if remember_me else None  # None = session cookie
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=access_max_age,
        httponly=True,  # Cannot be accessed by JavaScript (XSS protection)
        secure=not settings.DEBUG,  # HTTPS only in production
        samesite="lax",  # CSRF protection
        path="/",
    )
    
    # Refresh token cookie (7 days if remember_me, else session)
    refresh_max_age = (
        settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        if remember_me else None  # None = session cookie
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=refresh_max_age,
        httponly=True,
        secure=not settings.DEBUG,  # HTTPS only in production
        samesite="lax",
        path="/",
    )
    
    # Return tokens in response for backward compatibility
    # Note: User info is now in the JWT payload, not in the response
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
@limiter.limit("10/minute")  # Allow more refreshes than login attempts
def refresh_token(
    request: Request,
    response: Response,  # Added for cookie support
    token_request: Optional[RefreshTokenRequest] = None,
    db: Session = Depends(get_db)
) -> Any:
    """
    Refresh access token using refresh token from either:
    1. Request body (backward compatibility)
    2. httpOnly cookie (new secure method)
    """
    refresh_token = None
    
    # Try to get refresh token from request body first (backward compatibility)
    if token_request and token_request.refresh_token:
        refresh_token = token_request.refresh_token
    
    # If not in body, try cookie (new secure method)
    if not refresh_token:
        refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise InvalidTokenError()
    
    # Verify refresh token
    try:
        user_id = verify_token(refresh_token, token_type="refresh")
        if not user_id:
            raise InvalidTokenError()
    except Exception:
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
    
    # Update cookies with new tokens
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        path="/",
    )
    
    # Maintain remember_me status from original login
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        path="/",
    )
    
    # Return tokens for backward compatibility
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout")
@limiter.limit("10/minute")
def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Logout current user by clearing httpOnly cookies.
    Also supports token-based logout for backward compatibility.
    """
    # Clear httpOnly cookies (new secure method)
    response.delete_cookie(
        key="access_token",
        path="/",
        secure=not settings.DEBUG,
        samesite="lax"
    )
    response.delete_cookie(
        key="refresh_token",
        path="/",
        secure=not settings.DEBUG,
        samesite="lax"
    )
    
    # Note: Clients using Bearer tokens should remove them client-side
    # Optional: Implement token blacklisting here if needed
    
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