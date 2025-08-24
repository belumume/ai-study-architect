from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """Simple health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "AI Study Architect API",
        "version": "1.0.0"
    }