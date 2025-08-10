"""
Feature flags for safe experimentation and gradual rollouts.

Usage:
    from app.core.feature_flags import is_feature_enabled
    
    if is_feature_enabled("new_ai_model"):
        # Use experimental model
    else:
        # Use stable model
"""

from typing import Dict, Optional
from pydantic import BaseModel
from app.core.config import settings
import json
import os

class FeatureFlag(BaseModel):
    """Feature flag configuration"""
    name: str
    enabled: bool = False
    rollout_percentage: int = 0  # 0-100 for gradual rollout
    environments: list[str] = ["development"]  # Where it's enabled
    user_whitelist: list[str] = []  # Specific users who get the feature

# Feature flags configuration
FEATURE_FLAGS: Dict[str, FeatureFlag] = {
    "enhanced_socratic_mode": FeatureFlag(
        name="enhanced_socratic_mode",
        enabled=False,
        rollout_percentage=10,  # 10% of users
        environments=["staging"],
    ),
    "new_content_processor": FeatureFlag(
        name="new_content_processor",
        enabled=False,
        environments=["development", "staging"],
    ),
    "ai_model_claude_3_5": FeatureFlag(
        name="ai_model_claude_3_5",
        enabled=True,
        rollout_percentage=100,
        environments=["production", "staging"],
    ),
    "detailed_analytics": FeatureFlag(
        name="detailed_analytics",
        enabled=False,
        user_whitelist=["admin@aistudyarchitect.com"],
    ),
    "experimental_memory": FeatureFlag(
        name="experimental_memory",
        enabled=False,
        environments=["staging"],
    ),
}

def is_feature_enabled(
    feature_name: str,
    user_id: Optional[str] = None,
    check_percentage: bool = True
) -> bool:
    """
    Check if a feature is enabled.
    
    Args:
        feature_name: Name of the feature flag
        user_id: Optional user ID for user-specific features
        check_percentage: Whether to check rollout percentage
    
    Returns:
        True if feature is enabled for this context
    """
    # Feature doesn't exist - default to disabled
    if feature_name not in FEATURE_FLAGS:
        return False
    
    flag = FEATURE_FLAGS[feature_name]
    
    # Check if globally disabled
    if not flag.enabled:
        return False
    
    # Check environment
    current_env = settings.ENVIRONMENT
    if current_env not in flag.environments and "all" not in flag.environments:
        return False
    
    # Check user whitelist
    if user_id and flag.user_whitelist:
        if user_id in flag.user_whitelist:
            return True
        # If whitelist exists but user not in it, skip percentage check
        if not check_percentage:
            return False
    
    # Check rollout percentage (simple hash-based)
    if check_percentage and flag.rollout_percentage < 100:
        if user_id:
            # Consistent per-user rollout
            user_hash = hash(f"{feature_name}:{user_id}") % 100
            return user_hash < flag.rollout_percentage
        else:
            # Random rollout for anonymous
            import random
            return random.randint(0, 99) < flag.rollout_percentage
    
    return True

def get_enabled_features(user_id: Optional[str] = None) -> list[str]:
    """Get list of all enabled features for a user/context"""
    return [
        name for name in FEATURE_FLAGS
        if is_feature_enabled(name, user_id)
    ]

def update_feature_flag(
    feature_name: str,
    enabled: Optional[bool] = None,
    rollout_percentage: Optional[int] = None,
    environments: Optional[list[str]] = None,
) -> bool:
    """
    Update a feature flag configuration.
    Note: In production, this should be backed by a database or config service.
    """
    if feature_name not in FEATURE_FLAGS:
        return False
    
    flag = FEATURE_FLAGS[feature_name]
    
    if enabled is not None:
        flag.enabled = enabled
    if rollout_percentage is not None:
        flag.rollout_percentage = max(0, min(100, rollout_percentage))
    if environments is not None:
        flag.environments = environments
    
    return True

# Usage example in your code:
"""
from app.core.feature_flags import is_feature_enabled

@router.post("/agents/chat")
async def chat_endpoint(request: ChatRequest, user_id: str):
    if is_feature_enabled("enhanced_socratic_mode", user_id):
        # Use new enhanced Socratic questioning
        return enhanced_socratic_response(request)
    else:
        # Use stable version
        return standard_socratic_response(request)
"""