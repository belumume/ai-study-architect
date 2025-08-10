"""API v1 package - REST endpoints for AI Study Architect"""

from app.api.v1.csrf import router as csrf_router
from app.api.v1.auth import router as auth_router
from app.api.v1.tutor import router as tutor_router
from app.api.v1.content import router as content_router
from app.api.v1.admin import router as admin_router

__all__ = ["csrf_router", "auth_router", "tutor_router", "content_router", "admin_router"]