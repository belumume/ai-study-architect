"""
Redis caching service for AI responses and agent storage
"""

import json
import hashlib
import pickle
import os
from typing import Any, Optional, Dict, List, Union
from datetime import timedelta
import redis
import logging
from functools import wraps

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis-based caching service for AI responses and general caching"""
    
    def __init__(self):
        """Initialize Redis connection"""
        self._redis_client: Optional[redis.Redis] = None
        self._connected = False
        
    def _get_client(self) -> redis.Redis:
        """Get Redis client with lazy initialization and connection pooling"""
        if self._redis_client is None:
            try:
                # Check for Upstash first (serverless Redis)
                if os.getenv("UPSTASH_REDIS_REST_URL") and os.getenv("UPSTASH_REDIS_REST_TOKEN"):
                    logger.info("Using Upstash Redis via REST API")
                    from app.core.upstash_cache import UpstashRedisClient
                    self._redis_client = UpstashRedisClient()
                    self._connected = self._redis_client.connected
                    return self._redis_client
                
                # Check if traditional Redis URL is configured
                if not settings.REDIS_URL or settings.REDIS_URL == "redis://localhost:6379":
                    logger.info("Redis not configured, using in-memory mock cache")
                    self._connected = False
                    return MockRedisClient()
                
                # Create connection pool for traditional Redis
                pool = redis.ConnectionPool.from_url(
                    settings.REDIS_URL,
                    max_connections=20,
                    retry_on_timeout=True,
                    decode_responses=True  # Automatically decode responses
                )
                
                self._redis_client = redis.Redis(connection_pool=pool)
                
                # Test connection
                self._redis_client.ping()
                self._connected = True
                logger.info("Redis cache connected successfully")
                
            except Exception as e:
                logger.warning(f"Redis not available, using in-memory cache: {e}")
                self._connected = False
                # Return a mock client that does nothing
                return MockRedisClient()
        
        return self._redis_client
    
    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        return self._connected
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a consistent cache key from arguments"""
        # Create a hash of all arguments for consistent keys
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())  # Sort for consistency
        }
        
        # Create SHA256 hash of the key data
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:12]
        
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            client = self._get_client()
            value = client.get(key)
            if value is None:
                return None
            
            # Try to deserialize JSON first, then pickle as fallback
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                try:
                    return pickle.loads(value.encode('latin-1'))
                except Exception:
                    return value
                    
        except Exception as e:
            logger.warning(f"Cache get failed for key {key}: {e}")
            return None
    
    def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set value in cache with optional TTL"""
        try:
            client = self._get_client()
            
            # Serialize value
            try:
                serialized_value = json.dumps(value, default=str)
            except (TypeError, ValueError):
                # Fallback to pickle for complex objects
                serialized_value = pickle.dumps(value).decode('latin-1')
            
            # Set TTL
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            
            success = client.set(key, serialized_value, ex=ttl)
            return bool(success)
            
        except Exception as e:
            logger.warning(f"Cache set failed for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            client = self._get_client()
            return bool(client.delete(key))
        except Exception as e:
            logger.warning(f"Cache delete failed for key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            client = self._get_client()
            return bool(client.exists(key))
        except Exception as e:
            logger.warning(f"Cache exists check failed for key {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        try:
            client = self._get_client()
            keys = client.keys(pattern)
            if keys:
                return client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache clear pattern failed for {pattern}: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            client = self._get_client()
            info = client.info()
            
            return {
                "connected": self._connected,
                "used_memory": info.get('used_memory_human', 'Unknown'),
                "total_connections": info.get('total_connections_received', 0),
                "keyspace_hits": info.get('keyspace_hits', 0),
                "keyspace_misses": info.get('keyspace_misses', 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get('keyspace_hits', 0), 
                    info.get('keyspace_misses', 0)
                ),
                "connected_clients": info.get('connected_clients', 0),
                "uptime_seconds": info.get('uptime_in_seconds', 0)
            }
        except Exception as e:
            logger.warning(f"Failed to get cache stats: {e}")
            return {"connected": False, "error": str(e)}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)


class MockRedisClient:
    """Mock Redis client for when Redis is not available"""
    
    def __init__(self):
        self._store = {}
    
    def get(self, key: str) -> None:
        return None
    
    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        return True
    
    def delete(self, key: str) -> bool:
        return True
    
    def exists(self, key: str) -> bool:
        return False
    
    def keys(self, pattern: str) -> List[str]:
        return []
    
    def ping(self) -> bool:
        return True
    
    def info(self) -> Dict[str, Any]:
        return {}


class AIResponseCache:
    """Specialized caching for AI/LLM responses"""
    
    def __init__(self, cache_client: RedisCache):
        self.cache = cache_client
        self.default_ttl = timedelta(hours=24)  # AI responses cached for 24 hours
    
    def get_llm_response(
        self, 
        model: str, 
        prompt: str, 
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Get cached LLM response"""
        cache_key = self.cache._generate_cache_key(
            "llm_response", 
            model, 
            prompt, 
            **kwargs
        )
        
        return self.cache.get(cache_key)
    
    def set_llm_response(
        self, 
        model: str, 
        prompt: str, 
        response: Dict[str, Any],
        ttl: Optional[timedelta] = None,
        **kwargs
    ) -> bool:
        """Cache LLM response"""
        cache_key = self.cache._generate_cache_key(
            "llm_response", 
            model, 
            prompt, 
            **kwargs
        )
        
        # Add metadata
        cached_response = {
            "response": response,
            "model": model,
            "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest()[:12],
            "cached_at": str(int(time.time()))
        }
        
        return self.cache.set(
            cache_key, 
            cached_response, 
            ttl or self.default_ttl
        )
    
    def get_embedding(
        self, 
        model: str, 
        text: str
    ) -> Optional[List[float]]:
        """Get cached text embedding"""
        cache_key = self.cache._generate_cache_key("embedding", model, text)
        
        cached = self.cache.get(cache_key)
        if cached and isinstance(cached, dict):
            return cached.get("embedding")
        return cached
    
    def set_embedding(
        self, 
        model: str, 
        text: str, 
        embedding: List[float],
        ttl: Optional[timedelta] = None
    ) -> bool:
        """Cache text embedding"""
        cache_key = self.cache._generate_cache_key("embedding", model, text)
        
        cached_embedding = {
            "embedding": embedding,
            "model": model,
            "text_hash": hashlib.sha256(text.encode()).hexdigest()[:12],
            "cached_at": str(int(time.time()))
        }
        
        return self.cache.set(
            cache_key,
            cached_embedding,
            ttl or timedelta(days=7)  # Embeddings cached longer
        )
    
    def clear_model_cache(self, model: str) -> int:
        """Clear all cached responses for a specific model"""
        patterns = [
            f"llm_response:*{model}*",
            f"embedding:*{model}*"
        ]
        
        total_cleared = 0
        for pattern in patterns:
            total_cleared += self.cache.clear_pattern(pattern)
        
        logger.info(f"Cleared {total_cleared} cached responses for model {model}")
        return total_cleared


# Global cache instances
redis_cache = RedisCache()
ai_cache = AIResponseCache(redis_cache)


def cached_ai_response(
    ttl: Optional[timedelta] = None,
    model_param: str = "model",
    prompt_param: str = "prompt"
):
    """
    Decorator to automatically cache AI responses
    
    Usage:
        @cached_ai_response(ttl=timedelta(hours=6))
        def get_ai_response(model: str, prompt: str, **kwargs):
            # Your AI call here
            return response
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract model and prompt from arguments
            model = kwargs.get(model_param)
            prompt = kwargs.get(prompt_param)
            
            if not model or not prompt:
                # If we can't identify model/prompt, just call function
                return func(*args, **kwargs)
            
            # Create cache kwargs without the model and prompt to avoid duplication
            cache_kwargs = {k: v for k, v in kwargs.items() 
                           if k not in [model_param, prompt_param]}
            
            # Try to get from cache first
            cached_response = ai_cache.get_llm_response(model, prompt, **cache_kwargs)
            if cached_response:
                logger.info(f"Cache hit for model {model}")
                return cached_response["response"]
            
            # Cache miss - call the function
            logger.info(f"Cache miss for model {model} - calling function")
            response = func(*args, **kwargs)
            
            # Cache the response
            if response:
                ai_cache.set_llm_response(
                    model, prompt, response, ttl, **cache_kwargs
                )
            
            return response
        return wrapper
    return decorator


# Import time for timestamps
import time