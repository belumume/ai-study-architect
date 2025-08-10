"""
Admin API endpoints for system management
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.core.rsa_keys import key_manager
from app.core.exceptions import UnauthorizedError
from app.core.security import rotate_jwt_keys, get_key_rotation_info
from app.core.database import get_pool_status, test_database_connection
from app.core.cache import redis_cache, ai_cache
from app.core.agent_manager import agent_manager
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class KeyRotationResponse(BaseModel):
    """Response for key rotation"""
    success: bool
    message: str
    key_id: str
    created_at: float


class KeyRotationInfoResponse(BaseModel):
    """Response for key rotation info"""
    current_key: Dict[str, Any]
    archived_keys_count: int
    last_rotation: Optional[float]
    rotation_available: bool


class DatabasePoolStatus(BaseModel):
    """Response for database pool status"""
    pool_size: int
    checked_in: int
    checked_out: int
    overflow: int
    invalid: int
    total_connections: int
    available_connections: int
    pool_status: str


class CacheStatus(BaseModel):
    """Response for cache status"""
    connected: bool
    used_memory: str
    total_connections: int
    keyspace_hits: int
    keyspace_misses: int
    hit_rate: float
    connected_clients: int
    uptime_seconds: int


class AgentManagerStatus(BaseModel):
    """Response for agent manager status"""
    redis_connected: bool
    local_cache_size: int
    max_local_cache_size: int
    total_agents: int
    agents_by_type: Dict[str, int]
    default_ttl_hours: float


def verify_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Verify that the current user is an admin
    
    Args:
        current_user: The authenticated user
        
    Returns:
        The user if they are an admin
        
    Raises:
        UnauthorizedError: If user is not an admin
    """
    if not current_user.is_superuser:
        raise UnauthorizedError(
            detail="Admin privileges required",
            error_code="ADMIN_REQUIRED"
        )
    return current_user


@router.post("/rotate-keys", response_model=KeyRotationResponse)
@limiter.limit("1/hour")
def rotate_rsa_keys(
    request: Request,
    admin_user: User = Depends(verify_admin),
    db: Session = Depends(get_db)
) -> KeyRotationResponse:
    """
    Rotate RSA keys for JWT signing
    
    This endpoint allows admins to rotate the RSA keys used for JWT signing.
    Old keys are archived and new ones are generated with graceful transition.
    
    Args:
        request: FastAPI request (for rate limiting)
        admin_user: The authenticated admin user
        db: Database session
        
    Returns:
        Key rotation response with rotation status
    """
    try:
        logger.info(f"Admin {admin_user.email} initiated key rotation")
        
        # Rotate keys using the security module's rotation function
        rotation_result = rotate_jwt_keys()
        
        if rotation_result["status"] == "success":
            logger.info(f"JWT keys rotated successfully. New key ID: {rotation_result['key_id']}")
            
            return KeyRotationResponse(
                success=True,
                message="JWT keys rotated successfully. Existing tokens remain valid during transition.",
                key_id=rotation_result["key_id"],
                created_at=rotation_result["created_at"]
            )
        else:
            logger.error(f"Key rotation failed: {rotation_result.get('error')}")
            raise HTTPException(
                status_code=500,
                detail=f"Key rotation failed: {rotation_result.get('error')}"
            )
        
    except Exception as e:
        logger.error(f"Key rotation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Key rotation failed"
        )


@router.get("/keys/info", response_model=KeyRotationInfoResponse)
@limiter.limit("10/minute")
def get_keys_info(
    request: Request,
    admin_user: User = Depends(verify_admin)
) -> KeyRotationInfoResponse:
    """
    Get information about current key rotation status
    
    Returns information about:
    - Current active key ID and creation time
    - Number of archived keys
    - Last rotation timestamp
    - Whether rotation is available
    
    Args:
        request: FastAPI request (for rate limiting)
        admin_user: The authenticated admin user
        
    Returns:
        Key rotation information
    """
    try:
        logger.info(f"Admin {admin_user.email} requested key rotation info")
        
        info = get_key_rotation_info()
        
        return KeyRotationInfoResponse(
            current_key=info["current_key"],
            archived_keys_count=info["archived_keys_count"],
            last_rotation=info["last_rotation"],
            rotation_available=info["rotation_available"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get key rotation info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to get key rotation info"
        )


@router.get("/public-key")
def get_public_key() -> Dict[str, str]:
    """
    Get the current public key for JWT verification
    
    This endpoint returns the public key that should be used to verify JWT tokens.
    This is useful for external services that need to verify tokens.
    
    Returns:
        Dictionary containing the public key
    """
    try:
        _, public_key = key_manager.load_keys()
        return {
            "public_key": public_key,
            "algorithm": "RS256"
        }
    except Exception as e:
        logger.error(f"Failed to load public key: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to load public key"
        )


@router.get("/health/detailed")
@limiter.limit("10/minute")
def detailed_health_check(
    request: Request,
    admin_user: User = Depends(verify_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Detailed health check for administrators
    
    Returns detailed information about system health including:
    - Database connectivity
    - Redis connectivity (when implemented)
    - AI services status
    - Disk space
    - Memory usage
    
    Args:
        request: FastAPI request (for rate limiting)
        admin_user: The authenticated admin user
        db: Database session
        
    Returns:
        Detailed health status
    """
    health_status = {
        "status": "healthy",
        "checks": {}
    }
    
    # Check database with pool status
    try:
        if test_database_connection():
            pool_status = get_pool_status()
            health_status["checks"]["database"] = {
                "status": "healthy",
                "message": "Database connection successful",
                "pool_status": pool_status
            }
        else:
            health_status["status"] = "unhealthy"
            health_status["checks"]["database"] = {
                "status": "unhealthy",
                "message": "Database connection failed"
            }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}"
        }
    
    # Check disk space
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        health_status["checks"]["disk_space"] = {
            "status": "healthy" if free > 1_000_000_000 else "warning",  # 1GB threshold
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "usage_percent": round((used / total) * 100, 2)
        }
    except Exception as e:
        health_status["checks"]["disk_space"] = {
            "status": "unknown",
            "message": f"Could not check disk space: {str(e)}"
        }
    
    # Check memory usage
    try:
        import psutil
        memory = psutil.virtual_memory()
        health_status["checks"]["memory"] = {
            "status": "healthy" if memory.percent < 90 else "warning",
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "usage_percent": memory.percent
        }
    except ImportError:
        health_status["checks"]["memory"] = {
            "status": "unknown",
            "message": "psutil not installed"
        }
    except Exception as e:
        health_status["checks"]["memory"] = {
            "status": "unknown",
            "message": f"Could not check memory: {str(e)}"
        }
    
    # Check Redis cache
    try:
        cache_stats = redis_cache.get_stats()
        if cache_stats.get("connected", False):
            health_status["checks"]["redis"] = {
                "status": "healthy",
                "message": "Redis cache is connected",
                "hit_rate": cache_stats.get("hit_rate", 0),
                "used_memory": cache_stats.get("used_memory", "Unknown"),
                "connected_clients": cache_stats.get("connected_clients", 0)
            }
        else:
            health_status["checks"]["redis"] = {
                "status": "unhealthy",
                "message": "Redis cache is not connected",
                "error": cache_stats.get("error", "Connection failed")
            }
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "message": f"Redis cache error: {str(e)}"
        }
    
    return health_status


@router.get("/database/pool", response_model=DatabasePoolStatus)
@limiter.limit("30/minute")
def get_database_pool_status(
    request: Request,
    admin_user: User = Depends(verify_admin)
) -> DatabasePoolStatus:
    """
    Get database connection pool status
    
    Returns detailed information about the database connection pool:
    - Pool size and overflow
    - Active/available connections
    - Pool health status
    
    Args:
        request: FastAPI request (for rate limiting)
        admin_user: The authenticated admin user
        
    Returns:
        Database pool status information
    """
    try:
        logger.info(f"Admin {admin_user.email} requested database pool status")
        
        pool_status = get_pool_status()
        
        return DatabasePoolStatus(
            pool_size=pool_status["pool_size"],
            checked_in=pool_status["checked_in"],
            checked_out=pool_status["checked_out"],
            overflow=pool_status["overflow"],
            invalid=pool_status["invalid"],
            total_connections=pool_status["total_connections"],
            available_connections=pool_status["available_connections"],
            pool_status=pool_status["pool_status"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get database pool status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to get database pool status"
        )


@router.get("/cache/status", response_model=CacheStatus)
@limiter.limit("30/minute")
def get_cache_status(
    request: Request,
    admin_user: User = Depends(verify_admin)
) -> CacheStatus:
    """
    Get Redis cache status and statistics
    
    Returns information about:
    - Connection status
    - Memory usage
    - Hit/miss rates
    - Connected clients
    - Uptime
    
    Args:
        request: FastAPI request (for rate limiting)
        admin_user: The authenticated admin user
        
    Returns:
        Cache status information
    """
    try:
        logger.info(f"Admin {admin_user.email} requested cache status")
        
        stats = redis_cache.get_stats()
        
        if not stats.get("connected", False):
            return CacheStatus(
                connected=False,
                used_memory="N/A",
                total_connections=0,
                keyspace_hits=0,
                keyspace_misses=0,
                hit_rate=0.0,
                connected_clients=0,
                uptime_seconds=0
            )
        
        return CacheStatus(
            connected=stats["connected"],
            used_memory=stats["used_memory"],
            total_connections=stats["total_connections"],
            keyspace_hits=stats["keyspace_hits"],
            keyspace_misses=stats["keyspace_misses"],
            hit_rate=stats["hit_rate"],
            connected_clients=stats["connected_clients"],
            uptime_seconds=stats["uptime_seconds"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get cache status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to get cache status"
        )


@router.post("/cache/clear-model")
@limiter.limit("3/hour")
def clear_model_cache(
    request: Request,
    model: str,
    admin_user: User = Depends(verify_admin)
):
    """
    Clear cache for a specific AI model
    
    Removes all cached responses for the specified model.
    Useful for when a model is updated or retrained.
    
    Args:
        request: FastAPI request (for rate limiting)
        model: Name of the model to clear cache for
        admin_user: The authenticated admin user
        
    Returns:
        Summary of cleared cache entries
    """
    try:
        logger.info(f"Admin {admin_user.email} clearing cache for model {model}")
        
        cleared_count = ai_cache.clear_model_cache(model)
        
        return {
            "message": f"Successfully cleared cache for model '{model}'",
            "cleared_entries": cleared_count
        }
        
    except Exception as e:
        logger.error(f"Failed to clear model cache: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to clear model cache"
        )


@router.post("/cache/clear-pattern")
@limiter.limit("2/hour") 
def clear_cache_pattern(
    request: Request,
    pattern: str,
    admin_user: User = Depends(verify_admin)
):
    """
    Clear cache entries matching a pattern
    
    WARNING: Use with caution. Can clear large amounts of cached data.
    
    Args:
        request: FastAPI request (for rate limiting)
        pattern: Redis pattern to match (e.g., "llm_response:*")
        admin_user: The authenticated admin user
        
    Returns:
        Summary of cleared cache entries
    """
    try:
        logger.warning(
            f"Admin {admin_user.email} clearing cache pattern '{pattern}'"
        )
        
        cleared_count = redis_cache.clear_pattern(pattern)
        
        return {
            "message": f"Successfully cleared cache pattern '{pattern}'",
            "cleared_entries": cleared_count
        }
        
    except Exception as e:
        logger.error(f"Failed to clear cache pattern: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to clear cache pattern"
        )


@router.get("/agents/status", response_model=AgentManagerStatus)
@limiter.limit("30/minute")
def get_agent_manager_status(
    request: Request,
    admin_user: User = Depends(verify_admin)
) -> AgentManagerStatus:
    """
    Get agent manager status and statistics
    
    Returns information about:
    - Redis connectivity for agent storage
    - Number of agents in local cache vs Redis
    - Agent distribution by type
    - TTL settings
    
    Args:
        request: FastAPI request (for rate limiting)
        admin_user: The authenticated admin user
        
    Returns:
        Agent manager status information
    """
    try:
        logger.info(f"Admin {admin_user.email} requested agent manager status")
        
        stats = agent_manager.get_stats()
        
        if "error" in stats:
            return AgentManagerStatus(
                redis_connected=False,
                local_cache_size=stats.get("local_cache_size", 0),
                max_local_cache_size=50,
                total_agents=0,
                agents_by_type={},
                default_ttl_hours=2.0
            )
        
        return AgentManagerStatus(
            redis_connected=stats["redis_connected"],
            local_cache_size=stats["local_cache_size"],
            max_local_cache_size=stats["max_local_cache_size"],
            total_agents=stats["total_agents"],
            agents_by_type=stats["agents_by_type"],
            default_ttl_hours=stats["default_ttl_hours"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get agent manager status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to get agent manager status"
        )


@router.get("/agents/list/{user_id}")
@limiter.limit("10/minute")
def list_user_agents(
    request: Request,
    user_id: str,
    admin_user: User = Depends(verify_admin)
):
    """
    List all agents for a specific user
    
    Args:
        request: FastAPI request (for rate limiting)
        user_id: User ID to list agents for
        admin_user: The authenticated admin user
        
    Returns:
        List of agent metadata
    """
    try:
        logger.info(f"Admin {admin_user.email} listing agents for user {user_id}")
        
        agents = agent_manager.list_user_agents(user_id)
        
        return {
            "user_id": user_id,
            "agent_count": len(agents),
            "agents": agents
        }
        
    except Exception as e:
        logger.error(f"Failed to list agents for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to list user agents"
        )


@router.post("/agents/cleanup")
@limiter.limit("3/hour")
def cleanup_expired_agents(
    request: Request,
    admin_user: User = Depends(verify_admin)
):
    """
    Clean up expired agents from storage
    
    Removes agents that haven't been active within the TTL period.
    This helps prevent memory leaks and storage bloat.
    
    Args:
        request: FastAPI request (for rate limiting)
        admin_user: The authenticated admin user
        
    Returns:
        Cleanup summary
    """
    try:
        logger.info(f"Admin {admin_user.email} initiated agent cleanup")
        
        cleaned_count = agent_manager.cleanup_expired_agents()
        
        return {
            "message": f"Agent cleanup completed successfully",
            "cleaned_agents": cleaned_count,
            "cleanup_time": str(datetime.utcnow())
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup expired agents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to cleanup expired agents"
        )


@router.delete("/agents/{user_id}/{agent_type}")
@limiter.limit("10/hour")
def delete_user_agent(
    request: Request,
    user_id: str,
    agent_type: str,
    session_id: Optional[str] = None,
    admin_user: User = Depends(verify_admin)
):
    """
    Delete a specific agent for a user
    
    Args:
        request: FastAPI request (for rate limiting)
        user_id: User ID
        agent_type: Type of agent to delete
        session_id: Optional session ID
        admin_user: The authenticated admin user
        
    Returns:
        Deletion status
    """
    try:
        logger.warning(f"Admin {admin_user.email} deleting agent {agent_type} for user {user_id}")
        
        success = agent_manager.delete_agent(user_id, agent_type, session_id)
        
        if success:
            return {
                "message": f"Successfully deleted agent {agent_type} for user {user_id}",
                "user_id": user_id,
                "agent_type": agent_type,
                "session_id": session_id
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Agent not found or could not be deleted"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete agent: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to delete agent"
        )