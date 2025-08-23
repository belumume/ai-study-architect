"""
Debug endpoint to check AI service configuration
REMOVE THIS IN PRODUCTION!
"""

import os
from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_active_user
from app.services.ai_service_manager import ai_service_manager
from app.models.user import User

router = APIRouter()

@router.get("/ai-status")
async def check_ai_status(
    current_user: User = Depends(get_current_active_user)
):
    """Check AI service configuration status"""
    
    # Only allow superusers or specific test user
    if not (current_user.is_superuser or current_user.username == "testuser_claude"):
        return {"error": "Unauthorized"}
    
    status = {
        "anthropic": {
            "api_key_set": bool(os.getenv("ANTHROPIC_API_KEY")),
            "api_key_length": len(os.getenv("ANTHROPIC_API_KEY", "")) if os.getenv("ANTHROPIC_API_KEY") else 0,
            "model": os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
        },
        "openai": {
            "api_key_set": bool(os.getenv("OPENAI_API_KEY")),
            "api_key_length": len(os.getenv("OPENAI_API_KEY", "")) if os.getenv("OPENAI_API_KEY") else 0,
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        }
    }
    
    # Check which service is available
    service_name, service = await ai_service_manager.get_available_service()
    status["available_service"] = service_name
    
    # Test a simple completion if service is available
    if service:
        try:
            test_messages = [
                {"role": "user", "content": "Say 'API test successful' and nothing else"}
            ]
            result = await ai_service_manager.chat_completion(
                messages=test_messages,
                temperature=0,
                max_tokens=10,
                stream=False
            )
            status["test_response"] = result.get("response", "No response")
            status["test_error"] = result.get("error", None)
        except Exception as e:
            status["test_error"] = str(e)
    else:
        status["test_error"] = "No service available"
    
    return status