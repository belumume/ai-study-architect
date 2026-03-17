"""
Authentication endpoints - Sync version

Refresh token rotation (Todo 031):
- Each login creates a token "family" identified by a UUID (family_id / fid).
- The current valid refresh token hash is stored in Redis: refresh_family:{fid}.
- On refresh, the old token is consumed and a new one issued in the same family.
- If a consumed token is replayed, the entire family is invalidated (theft detection).
- Old tokens without fid (pre-rotation) are migrated into a new family on first refresh.
"""

import hashlib
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Form, Request, Response, status
from fastapi.security import HTTPBearer
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core.cache import redis_cache
from app.core.config import settings
from app.core.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.core.rate_limiter import limiter
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token_claims,
)
from app.core.utils import utcnow
from app.models.user import User
from app.schemas.user import (
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)

logger = logging.getLogger(__name__)

# Redis key prefix and TTL for refresh token families
_FAMILY_KEY_PREFIX = "refresh_family:"
_FAMILY_TTL_SECONDS = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


def _hash_token(token: str) -> str:
    """SHA-256 hash of a token for safe storage in Redis."""
    return hashlib.sha256(token.encode()).hexdigest()


def _store_refresh_family(family_id: str, token_hash: str) -> None:
    """Store the current valid refresh token hash for a family."""
    redis_cache.set(
        f"{_FAMILY_KEY_PREFIX}{family_id}",
        token_hash,
        ttl=_FAMILY_TTL_SECONDS,
    )


def _invalidate_family(family_id: str, reason: str = "theft") -> None:
    """Invalidate an entire token family."""
    redis_cache.delete(f"{_FAMILY_KEY_PREFIX}{family_id}")
    if reason == "theft":
        logger.warning("Refresh token family invalidated (potential theft): %s", family_id)
    else:
        logger.info("Refresh token family invalidated (%s): %s", reason, family_id)


class OAuth2PasswordRequestFormWithRememberMe:
    """
    Custom OAuth2 form that includes remember_me field
    """

    def __init__(
        self,
        username: str = Form(),
        password: str = Form(),
        remember_me: str = Form(default="false"),
        scope: str = Form(default=""),
        client_id: str | None = Form(default=None),
        client_secret: str | None = Form(default=None),
    ):
        self.username = username
        self.password = password
        self.remember_me = remember_me
        self.scopes = scope.split()
        self.client_id = client_id
        self.client_secret = client_secret


router = APIRouter(prefix="/auth")
security = HTTPBearer()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")  # Prevent account creation spam
def register(request: Request, user_in: UserCreate, db: Session = Depends(get_db)) -> Any:
    """
    Register a new user.
    """
    # Check if user already exists
    existing_user = (
        db.query(User)
        .filter(or_(User.email == user_in.email, User.username == user_in.username))
        .first()
    )

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
    form_data: OAuth2PasswordRequestFormWithRememberMe = Depends(),
    db: Session = Depends(get_db),
) -> Any:
    """
    OAuth2 compatible token login with Remember Me support.
    """
    # Convert remember_me string to boolean
    remember_me_bool = form_data.remember_me.lower() == "true"

    # Find user by email or username
    user = (
        db.query(User)
        .filter(or_(User.email == form_data.username, User.username == form_data.username))
        .first()
    )

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise InvalidCredentialsError()

    if not user.is_active:
        raise InactiveUserError()

    # Update last login
    user.last_login_at = utcnow()
    db.commit()

    # Create token family for rotation tracking.
    # Only embed family_id if Redis is available — otherwise the refresh endpoint
    # would find no stored hash and incorrectly treat the token as stolen.
    redis_cache._get_client()  # ensure lazy init
    family_id = uuid.uuid4().hex if redis_cache.is_connected else None
    if not family_id:
        logger.info("Redis unavailable at login — issuing tokens without family tracking")

    access_token = create_access_token(subject=str(user.id), family_id=family_id)
    refresh_token = create_refresh_token(subject=str(user.id), family_id=family_id)

    if family_id:
        _store_refresh_family(family_id, _hash_token(refresh_token))

    # Store user_id for CSRF cookie
    request.state.user_id = str(user.id)

    # Set httpOnly cookies for better security (like major platforms)
    # Access token cookie (30 minutes if remember_me, else session)
    access_max_age = (
        settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        if remember_me_bool
        else None  # None = session cookie
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
        if remember_me_bool
        else None  # None = session cookie
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

    # Tokens are in httpOnly cookies only — never expose in response body
    return {"token_type": "bearer"}


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")  # Allow more refreshes than login attempts
def refresh_token(
    request: Request,
    response: Response,
    token_request: RefreshTokenRequest | None = None,
    db: Session = Depends(get_db),
) -> Any:
    """
    Refresh access token with token rotation and replay detection.

    Token sources (in priority order):
    1. Request body (backward compatibility)
    2. httpOnly cookie (primary method)

    Rotation logic:
    - Tokens with a family_id (fid) claim are validated against Redis.
    - On success, the old token is consumed and a new one issued.
    - If a consumed token is replayed, the entire family is invalidated.
    - Legacy tokens without fid are migrated into a new family.
    """
    raw_refresh_token = None

    # Try to get refresh token from request body first (backward compatibility)
    if token_request and token_request.refresh_token:
        raw_refresh_token = token_request.refresh_token

    # If not in body, try cookie
    if not raw_refresh_token:
        raw_refresh_token = request.cookies.get("refresh_token")

    if not raw_refresh_token:
        raise InvalidTokenError()

    # Verify refresh token signature and expiry
    claims = verify_token_claims(raw_refresh_token, token_type="refresh")
    if not claims:
        raise InvalidTokenError()

    user_id = claims.get("sub")
    if not user_id:
        raise InvalidTokenError()

    family_id = claims.get("fid")

    if family_id and redis_cache.is_connected:
        # --- Token rotation validation (requires Redis) ---
        stored_hash = redis_cache.get(f"{_FAMILY_KEY_PREFIX}{family_id}")

        if stored_hash is None:
            # Family was invalidated (theft detected previously) or expired
            logger.warning("Refresh attempt on invalidated/expired family: %s", family_id)
            raise InvalidTokenError()

        current_hash = _hash_token(raw_refresh_token)

        if stored_hash != current_hash:
            # Token was already consumed — this is a replay (potential theft).
            # Invalidate the entire family so the legitimate user's next refresh also fails,
            # forcing re-authentication.
            _invalidate_family(family_id)
            raise InvalidTokenError()
    elif not family_id:
        # Legacy token without family_id — migrate into the rotation system.
        family_id = uuid.uuid4().hex
        logger.info("Migrating legacy refresh token to family %s for user %s", family_id, user_id)
    else:
        # Token has fid but Redis is down — keep the same family, skip replay check.
        # Rotation still happens (new token issued), just no replay detection until Redis recovers.
        logger.warning("Redis unavailable — skipping rotation validation for family %s", family_id)

    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFoundError()
    if not user.is_active:
        raise InactiveUserError()

    # Issue new tokens in the same family
    access_token = create_access_token(subject=str(user.id), family_id=family_id)
    new_refresh_token = create_refresh_token(subject=str(user.id), family_id=family_id)

    # Store the new refresh token hash, consuming the old one
    _store_refresh_family(family_id, _hash_token(new_refresh_token))

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

    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        path="/",
    )

    # Tokens are in httpOnly cookies only — never expose in response body
    return {"token_type": "bearer"}


@router.post("/logout")
@limiter.limit("10/minute")
def logout(
    request: Request, response: Response, current_user: User = Depends(get_current_user)
) -> Any:
    """
    Logout current user by clearing httpOnly cookies and invalidating token family.
    """
    # Invalidate the refresh token family if present in the cookie
    raw_refresh = request.cookies.get("refresh_token")
    if raw_refresh:
        claims = verify_token_claims(raw_refresh, token_type="refresh")
        if claims and claims.get("fid"):
            _invalidate_family(claims["fid"], reason="logout")

    # Clear httpOnly cookies
    response.delete_cookie(key="access_token", path="/", secure=not settings.DEBUG, samesite="lax")
    response.delete_cookie(key="refresh_token", path="/", secure=not settings.DEBUG, samesite="lax")

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
@limiter.limit("30/minute")
def get_current_user_info(request: Request, current_user: User = Depends(get_current_user)) -> Any:
    """
    Get current user information.
    """
    return current_user
