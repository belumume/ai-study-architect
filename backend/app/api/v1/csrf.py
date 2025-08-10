"""
CSRF Token API endpoints
"""

from fastapi import APIRouter, Response, Request, Depends
from pydantic import BaseModel
from app.api.dependencies import get_optional_current_user
from app.models.user import User
from app.core.csrf import csrf_protect
import logging

logger = logging.getLogger(__name__)
logger.info("CSRF module loaded - creating router")

router = APIRouter()


class CSRFTokenResponse(BaseModel):
    """CSRF token response"""
    csrf_token: str
    header_name: str
    expires_in: int


@router.get("/token", response_model=CSRFTokenResponse)
def get_csrf_token(
    request: Request,
    response: Response,
    current_user: User = Depends(get_optional_current_user)
) -> CSRFTokenResponse:
    """
    Get a CSRF token
    
    This endpoint returns a CSRF token that must be included
    in the X-CSRF-Token header for all state-changing requests.
    
    If a valid token already exists in the cookie, it returns that token.
    Otherwise, it generates a new token.
    """
    user_id = str(current_user.id) if current_user else None
    
    # Check if a valid token already exists in the cookie
    existing_token = request.cookies.get(csrf_protect.cookie_name)
    
    if existing_token:
        try:
            # Validate the existing token
            csrf_protect.validate_csrf_token(existing_token, existing_token, user_id)
            # Token is valid, return it
            csrf_token = existing_token
            logger.info(f"Returning existing CSRF token for user {user_id}")
        except Exception as e:
            # Token is invalid or expired, generate a new one
            logger.info(f"Existing token invalid ({str(e)}), generating new token for user {user_id}")
            csrf_token = csrf_protect.set_csrf_cookie(response, user_id)
    else:
        # No existing token, generate a new one
        logger.info(f"No existing token, generating new token for user {user_id}")
        csrf_token = csrf_protect.set_csrf_cookie(response, user_id)
    
    return CSRFTokenResponse(
        csrf_token=csrf_token,
        header_name=csrf_protect.header_name,
        expires_in=csrf_protect.token_lifetime
    )


# Log when module is imported
logger.info(f"CSRF router created with {len(router.routes)} routes")