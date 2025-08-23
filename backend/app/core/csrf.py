"""
CSRF Protection for FastAPI
Implements double-submit cookie pattern for CSRF protection
"""

import secrets
import time
from typing import Optional, Dict, Any
from fastapi import Request, Response, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel
import hashlib
import hmac
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.exceptions import CSRFError


class CSRFToken(BaseModel):
    """CSRF Token model"""
    token: str
    created_at: float
    user_id: Optional[str] = None


class CSRFProtect:
    """
    CSRF Protection using double-submit cookie pattern
    
    This implementation:
    1. Generates a random token
    2. Stores it in a httpOnly cookie
    3. Requires the same token in a header for state-changing requests
    4. Validates token matches and isn't expired
    """
    
    def __init__(
        self,
        secret_key: str = None,
        token_lifetime: int = 3600,  # 1 hour
        cookie_name: str = "csrf_token",
        header_name: str = "X-CSRF-Token",
        cookie_secure: bool = True,
        cookie_httponly: bool = False,  # Must be False for JavaScript to read
        cookie_samesite: str = "strict"
    ):
        self.secret_key = secret_key or settings.SECRET_KEY
        self.token_lifetime = token_lifetime
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.cookie_secure = cookie_secure and not settings.DEBUG
        self.cookie_httponly = cookie_httponly
        self.cookie_samesite = cookie_samesite
        
    def generate_csrf_token(self, user_id: Optional[str] = None) -> str:
        """
        Generate a new CSRF token
        
        Args:
            user_id: Optional user ID to bind token to specific user
            
        Returns:
            Generated CSRF token
        """
        # Generate random token
        random_token = secrets.token_urlsafe(32)
        
        # Create timestamp
        timestamp = str(int(time.time()))
        
        # Create token data
        token_data = f"{random_token}:{timestamp}"
        if user_id:
            token_data += f":{user_id}"
        
        # Sign the token
        signature = self._sign_token(token_data)
        
        # Combine token and signature
        csrf_token = f"{token_data}:{signature}"
        
        return csrf_token
    
    def _sign_token(self, token_data: str) -> str:
        """Sign token data with HMAC"""
        return hmac.new(
            self.secret_key.encode(),
            token_data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def validate_csrf_token(
        self,
        cookie_token: Optional[str],
        header_token: Optional[str],
        user_id: Optional[str] = None
    ) -> bool:
        """
        Validate CSRF token from cookie matches header token
        
        Args:
            cookie_token: Token from cookie
            header_token: Token from header
            user_id: Optional user ID for additional validation
            
        Returns:
            True if tokens are valid and match
            
        Raises:
            CSRFError: If validation fails
        """
        # Check both tokens exist
        if not cookie_token or not header_token:
            raise CSRFError("CSRF token missing")
        
        # Tokens must match exactly
        if cookie_token != header_token:
            raise CSRFError("CSRF token mismatch")
        
        # Parse token
        try:
            parts = cookie_token.split(":")
            if len(parts) < 3:
                raise CSRFError("Invalid CSRF token format")
            
            random_token = parts[0]
            timestamp = parts[1]
            signature = parts[-1]
            
            # Reconstruct token data
            if len(parts) == 4:
                token_user_id = parts[2]
                # If user_id is provided, verify it matches the token's user_id
                if user_id and token_user_id != user_id:
                    raise CSRFError("CSRF token user mismatch")
                # Use the token's user_id for signature verification
                token_data = f"{random_token}:{timestamp}:{token_user_id}"
            else:
                token_data = f"{random_token}:{timestamp}"
            
            # Verify signature
            expected_signature = self._sign_token(token_data)
            if not hmac.compare_digest(signature, expected_signature):
                raise CSRFError("CSRF token signature invalid")
            
            # Check token age
            token_age = int(time.time()) - int(timestamp)
            if token_age > self.token_lifetime:
                raise CSRFError("CSRF token expired")
            
            return True
            
        except (ValueError, IndexError) as e:
            raise CSRFError(f"CSRF token validation failed: {str(e)}")
    
    def set_csrf_cookie(self, response: Response, user_id: Optional[str] = None) -> str:
        """
        Set CSRF token in response cookie
        
        Args:
            response: FastAPI response object
            user_id: Optional user ID to bind token
            
        Returns:
            Generated CSRF token
        """
        csrf_token = self.generate_csrf_token(user_id)
        
        response.set_cookie(
            key=self.cookie_name,
            value=csrf_token,
            max_age=self.token_lifetime,
            secure=self.cookie_secure,
            httponly=self.cookie_httponly,
            samesite=self.cookie_samesite,
            path="/"
        )
        
        return csrf_token
    
    def get_csrf_token_from_request(self, request: Request) -> Dict[str, Optional[str]]:
        """
        Extract CSRF tokens from request
        
        Args:
            request: FastAPI request object
            
        Returns:
            Dict with cookie_token and header_token
        """
        # Get token from cookie
        cookie_token = request.cookies.get(self.cookie_name)
        
        # Get token from header
        header_token = request.headers.get(self.header_name)
        
        # For DELETE requests and other methods that don't typically have form data,
        # we only check header, not form data
        
        return {
            "cookie_token": cookie_token,
            "header_token": header_token
        }
    
    def validate_request(self, request: Request, user_id: Optional[str] = None) -> bool:
        """
        Validate CSRF token in request
        
        Args:
            request: FastAPI request object
            user_id: Optional user ID for validation
            
        Returns:
            True if valid
            
        Raises:
            CSRFError: If validation fails
        """
        tokens = self.get_csrf_token_from_request(request)
        return self.validate_csrf_token(
            tokens["cookie_token"],
            tokens["header_token"],
            user_id
        )
    
    def exempt_path(self, path: str) -> bool:
        """
        Check if path should be exempt from CSRF protection
        
        Args:
            path: Request path
            
        Returns:
            True if path is exempt
        """
        # Exempt paths that don't need CSRF protection
        exempt_paths = [
            "/api/v1/auth/login",
            "/api/v1/auth/register", 
            "/api/v1/auth/refresh",
            "/api/v1/auth/logout",  # Logout doesn't need CSRF
            "/api/v1/health",
            "/health",  # Root health check
            "/api/v1/csrf/token",  # Endpoint to get CSRF token
            "/api/v1/content/upload",  # File upload uses JWT auth
            "/api/v1/backup/",  # Backup endpoint uses token auth
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        
        # Special handling for main chat endpoint (JWT protected)
        # Note: The main chat endpoint is at /api/v1/chat after router prefix fix
        if path == "/api/v1/chat" or path.startswith("/api/v1/chat/") or path.startswith("/api/v1/agents/"):
            return True
        
        return any(path.startswith(p) for p in exempt_paths)


# Global CSRF protection instance
csrf_protect = CSRFProtect()


def require_csrf_token(request: Request):
    """
    Dependency to require valid CSRF token
    
    Use this as a dependency on state-changing endpoints:
    
    @router.post("/update")
    def update_resource(
        request: Request,
        _csrf: None = Depends(require_csrf_token)
    ):
        ...
    """
    if not csrf_protect.exempt_path(request.url.path):
        # Only validate for unsafe methods
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            try:
                # Get user_id from request state if available
                user_id = getattr(request.state, "user_id", None)
                csrf_protect.validate_request(request, user_id)
            except CSRFError as e:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=str(e)
                )