"""
AI Study Architect - Main FastAPI Application (Sync version)
"""

# CRITICAL: Setup Python path BEFORE any other imports
# This fixes ModuleNotFoundError on Render deployment
import sys
import os

# Import path setup module first - this MUST happen before any app imports
try:
    # Try relative import first (when running as module)
    from . import _path_setup
except ImportError:
    # Fall back to absolute import (when running directly)
    try:
        import app._path_setup
    except ImportError:
        # Manual path setup if import fails
        _current_file = os.path.abspath(__file__)
        _app_dir = os.path.dirname(_current_file)
        _backend_dir = os.path.dirname(_app_dir)
        
        if _backend_dir not in sys.path:
            sys.path.insert(0, _backend_dir)
        
        render_path = "/opt/render/project/src/project/backend"
        if os.path.exists(render_path) and render_path not in sys.path:
            sys.path.insert(0, render_path)

from fastapi import FastAPI, Request, Response, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
from typing import Any

# Configure logging FIRST (before any logger usage)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from app.core.config import settings
from app.core.csrf import csrf_protect, require_csrf_token

# Try to import init_db, fallback to minimal version
try:
    from app.core.init_db_safe import init_db
except ImportError as e:
    logger.warning(f"Could not import init_db_safe: {e}")
    from app.core.init_db_minimal import init_db_minimal
    from app.core.database import engine, Base
    
    def init_db():
        """Wrapper for minimal init"""
        return init_db_minimal(engine, Base)

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="AI Study Architect API",
    description="Multi-agent learning system for personalized education",
    version="0.1.0",
)

# CSRF protection is now handled by the new comprehensive implementation
app.state.csrf_protect = csrf_protect

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CSRF middleware will be added as a regular middleware function below

# Configure CORS (secure configuration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
    expose_headers=["X-Total-Count"],
)

# Add Trusted Host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "localhost", 
        "127.0.0.1", 
        "*.localhost",
        "ai-study-architect.onrender.com",
        "*.onrender.com"
    ]
)

# Add comprehensive security headers middleware
from app.core.security_headers import SecurityHeadersMiddleware
app.add_middleware(
    SecurityHeadersMiddleware,
    is_debug=settings.DEBUG,
    nonce_enabled=False,  # Disable nonce for now due to Swagger UI compatibility
    report_uri="/api/v1/security/csp-report" if not settings.DEBUG else None
)

# CSRF Protection middleware
@app.middleware("http")
async def csrf_middleware(request: Request, call_next) -> Response:
    """Apply CSRF protection using double-submit cookie pattern"""
    # Handle OPTIONS preflight requests
    if request.method == "OPTIONS":
        # Let CORS middleware handle OPTIONS
        return await call_next(request)
    
    # Skip CSRF for safe methods
    if request.method in ["GET", "HEAD"]:
        return await call_next(request)
    
    # Skip for exempt paths
    if csrf_protect.exempt_path(request.url.path):
        return await call_next(request)
    
    # For state-changing requests, validate CSRF token
    try:
        # Try to get user_id from JWT token if available
        user_id = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                from app.core.security import decode_access_token
                token = auth_header.split(" ")[1]
                payload = decode_access_token(token)
                user_id = payload.get("sub")
            except Exception:
                # If token decode fails, continue with validation without user_id
                pass
        
        csrf_protect.validate_request(request, user_id)
    except Exception as e:
        logger.warning(f"CSRF validation failed for {request.url.path}: {str(e)}")
        # Include CORS headers in error response to prevent misleading CORS errors
        origin = request.headers.get("origin")
        headers = {}
        if origin in settings.BACKEND_CORS_ORIGINS:
            headers = {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
            }
        return Response(
            content="CSRF validation failed",
            status_code=403,
            media_type="text/plain",
            headers=headers
        )
    
    # Process request
    response = await call_next(request)
    
    # Set CSRF cookie on successful auth responses
    if request.url.path in ["/api/v1/auth/login", "/api/v1/auth/register"] and response.status_code == 200:
        user_id = getattr(request.state, "user_id", None)
        csrf_protect.set_csrf_cookie(response, user_id)
    
    return response

# Request ID middleware for tracking
@app.middleware("http")
async def add_request_id(request: Request, call_next) -> Response:
    """Add request ID for tracking"""
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Root endpoint
@app.get("/")
@limiter.limit("30/minute")
def read_root(request: Request) -> dict[str, Any]:
    """Root endpoint"""
    return {
        "message": "Welcome to AI Study Architect API",
        "docs": "/docs",
        "health": "/health"
    }

# Health check endpoint
@app.get("/health")
@limiter.limit("60/minute")
def health_check(request: Request) -> dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Study Architect API"
    }



# Import and include routers
from app.api.v1.api import api_router

app.include_router(
    api_router,
    prefix="/api/v1"
)

# Log registered routes for debugging
api_routes = [r.path for r in app.routes if hasattr(r, 'path') and '/api/v1' in r.path]
csrf_registered = any('csrf' in r for r in api_routes)
logger.info(f"API routes registered: {len(api_routes)}")
logger.info(f"CSRF route registered: {csrf_registered}")

# Debug: Log all routes
logger.info("All registered routes:")
for route in app.routes:
    if hasattr(route, 'path'):
        logger.info(f"  - {route.path}")

logger.info(f"API router routes: {[r.path for r in api_router.routes if hasattr(r, 'path')]}")

# Startup event
@app.on_event("startup")
def startup_event() -> None:
    logger.info("Starting AI Study Architect API...")
    # Initialize database tables
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

# Shutdown event
@app.on_event("shutdown")
def shutdown_event() -> None:
    logger.info("Shutting down AI Study Architect API...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)