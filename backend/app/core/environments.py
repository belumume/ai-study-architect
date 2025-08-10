"""
Environment-specific configurations.
Helps maintain different settings for dev, staging, and production.
"""

from typing import Dict, Any
from app.core.config import settings

class EnvironmentConfig:
    """Environment-specific settings"""
    
    @staticmethod
    def get_config() -> Dict[str, Any]:
        """Get configuration based on current environment"""
        env = settings.ENVIRONMENT.lower()
        
        configs = {
            "development": {
                "debug": True,
                "log_level": "DEBUG",
                "cache_ttl": 60,  # 1 minute cache in dev
                "rate_limit": "100/minute",
                "ai_model": "claude-3-haiku-20240307",  # Cheaper model for dev
                "cors_origins": ["http://localhost:3000", "http://localhost:5173"],
                "features": {
                    "experimental": True,
                    "verbose_logging": True,
                    "mock_ai": False,  # Use real AI even in dev
                },
            },
            "staging": {
                "debug": False,
                "log_level": "INFO",
                "cache_ttl": 300,  # 5 minute cache
                "rate_limit": "30/minute",
                "ai_model": "claude-3-5-sonnet-20241022",  # Same as prod
                "cors_origins": [
                    "https://ai-study-architect-staging.vercel.app",
                    "http://localhost:5173",  # Allow local frontend testing
                ],
                "features": {
                    "experimental": True,  # Test new features here
                    "verbose_logging": True,
                    "mock_ai": False,
                },
            },
            "production": {
                "debug": False,
                "log_level": "WARNING",
                "cache_ttl": 900,  # 15 minute cache
                "rate_limit": "20/minute",
                "ai_model": "claude-3-5-sonnet-20241022",
                "cors_origins": [
                    "https://ai-study-architect.vercel.app",
                    "https://www.aistudyarchitect.com",
                ],
                "features": {
                    "experimental": False,  # Only stable features
                    "verbose_logging": False,
                    "mock_ai": False,
                },
            },
        }
        
        # Default to production settings if environment not found
        return configs.get(env, configs["production"])
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production"""
        return settings.ENVIRONMENT.lower() == "production"
    
    @classmethod
    def is_staging(cls) -> bool:
        """Check if running in staging"""
        return settings.ENVIRONMENT.lower() == "staging"
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development"""
        return settings.ENVIRONMENT.lower() in ["development", "dev"]
    
    @classmethod
    def get_ai_model(cls) -> str:
        """Get the AI model for current environment"""
        config = cls.get_config()
        return config.get("ai_model", "claude-3-5-sonnet-20241022")
    
    @classmethod
    def get_rate_limit(cls) -> str:
        """Get rate limit for current environment"""
        config = cls.get_config()
        return config.get("rate_limit", "20/minute")
    
    @classmethod
    def should_use_experimental_features(cls) -> bool:
        """Check if experimental features should be enabled"""
        config = cls.get_config()
        return config.get("features", {}).get("experimental", False)

# Usage in your code:
"""
from app.core.environments import EnvironmentConfig

# In your AI service
model = EnvironmentConfig.get_ai_model()

# In your rate limiter
@limiter.limit(EnvironmentConfig.get_rate_limit())
async def some_endpoint():
    pass

# Feature gating
if EnvironmentConfig.should_use_experimental_features():
    # Use new experimental feature
    pass
"""