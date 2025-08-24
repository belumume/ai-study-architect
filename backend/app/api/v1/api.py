"""Main API router for v1 endpoints"""

from fastapi import APIRouter

# Import routers explicitly
from app.api.v1.csrf import router as csrf_router
from app.api.v1.auth import router as auth_router
from app.api.v1.tutor import router as tutor_router
from app.api.v1.content import router as content_router
from app.api.v1.admin import router as admin_router
from app.api.v1.chat import router as chat_router
from app.api.v1.agents import router as agents_router
from app.api.v1.endpoints.backup import router as backup_router
from app.api.v1.health import router as health_router

api_router = APIRouter()

# Include routers with explicit references
api_router.include_router(health_router, tags=["health"])
api_router.include_router(csrf_router, prefix="/csrf", tags=["authentication"])
api_router.include_router(auth_router, tags=["authentication"])
api_router.include_router(tutor_router, tags=["tutor"])
api_router.include_router(content_router, tags=["content"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(agents_router, tags=["agents"])
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
api_router.include_router(backup_router, prefix="/backup", tags=["maintenance"])