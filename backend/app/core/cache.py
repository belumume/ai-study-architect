"""
Redis caching service for AI responses and agent storage
"""

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import timedelta
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CacheResult:
    """Result of a cache lookup that distinguishes found/missing/error.

    Attributes:
        value: The cached value (None when not found or on error).
        found: True only when the key exists and was successfully retrieved.
        error: True when the lookup failed due to a connection/transport error.
    """

    value: Any
    found: bool
    error: bool = False


class _NoOpCache:
    """Minimal no-op cache for local development without Redis."""

    def get(self, key):
        return None

    def set(self, key, value, ex=None):
        return True

    def delete(self, key):
        return True

    def exists(self, key):
        return False

    def keys(self, pattern):
        return []

    def ping(self):
        return False

    def info(self):
        return {}


class RedisCache:
    """Redis-based caching service for AI responses and general caching"""

    def __init__(self):
        """Initialize Redis connection"""
        self._redis_client: Any | None = None
        self._connected = False

    def _get_client(self):
        """Get Redis client with lazy initialization"""
        if self._redis_client is None:
            try:
                if os.getenv("UPSTASH_REDIS_REST_URL") and os.getenv("UPSTASH_REDIS_REST_TOKEN"):
                    logger.info("Using Upstash Redis via REST API")
                    from app.core.upstash_cache import UpstashRedisClient

                    self._redis_client = UpstashRedisClient()
                    self._connected = self._redis_client.connected
                    return self._redis_client

                logger.warning(
                    "No Redis configured (set UPSTASH_REDIS_REST_URL). Caching disabled."
                )
                self._redis_client = _NoOpCache()
                self._connected = False
                return self._redis_client

            except Exception as e:
                logger.warning(f"Cache initialization failed: {e}")
                self._redis_client = _NoOpCache()
                self._connected = False
                return self._redis_client

        return self._redis_client

    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        return self._connected

    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a consistent cache key from arguments"""
        # Create a hash of all arguments for consistent keys
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items()),  # Sort for consistency
        }

        # Create SHA256 hash of the key data
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:12]

        return f"{prefix}:{key_hash}"

    def get(self, key: str) -> Any | None:
        """Get value from cache.

        Returns None for both missing keys and connection errors.
        Use get_with_status() when the distinction matters.
        """
        result = self.get_with_status(key)
        return result.value

    def get_with_status(self, key: str) -> CacheResult:
        """Get value from cache with explicit found/error status.

        Returns CacheResult where:
        - found=True, error=False: key existed, value is the cached data
        - found=False, error=False: key genuinely does not exist
        - found=False, error=True: connection/transport error (value is None)
        """
        try:
            client = self._get_client()
            # _NoOpCache always returns None — treat as "not found" (not error)
            if isinstance(client, _NoOpCache):
                return CacheResult(value=None, found=False, error=False)

            value = client.get(key)
            if value is None:
                return CacheResult(value=None, found=False, error=False)

            # Deserialize JSON only (no unsafe deserialization)
            try:
                deserialized = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                deserialized = value
            return CacheResult(value=deserialized, found=True, error=False)

        except Exception as e:
            logger.warning(f"Cache get failed for key {key}: {e}")
            return CacheResult(value=None, found=False, error=True)

    def set(self, key: str, value: Any, ttl: int | timedelta | None = None) -> bool:
        """Set value in cache with optional TTL"""
        try:
            client = self._get_client()

            # Serialize as JSON only (no unsafe serialization)
            serialized_value = json.dumps(value, default=str)

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

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        try:
            client = self._get_client()
            info = client.info()

            return {
                "connected": self._connected,
                "used_memory": info.get("used_memory_human", "Unknown"),
                "total_connections": info.get("total_connections_received", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0), info.get("keyspace_misses", 0)
                ),
                "connected_clients": info.get("connected_clients", 0),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
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


class AIResponseCache:
    """Specialized caching for AI/LLM responses"""

    def __init__(self, cache_client: RedisCache):
        self.cache = cache_client
        self.default_ttl = timedelta(hours=24)  # AI responses cached for 24 hours

    def get_llm_response(self, model: str, prompt: str, **kwargs) -> dict[str, Any] | None:
        """Get cached LLM response"""
        cache_key = self.cache._generate_cache_key("llm_response", model, prompt, **kwargs)

        return self.cache.get(cache_key)

    def set_llm_response(
        self,
        model: str,
        prompt: str,
        response: dict[str, Any],
        ttl: timedelta | None = None,
        **kwargs,
    ) -> bool:
        """Cache LLM response"""
        cache_key = self.cache._generate_cache_key("llm_response", model, prompt, **kwargs)

        # Add metadata
        cached_response = {
            "response": response,
            "model": model,
            "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest()[:12],
            "cached_at": str(int(time.time())),
        }

        return self.cache.set(cache_key, cached_response, ttl or self.default_ttl)

    def get_embedding(self, model: str, text: str) -> list[float] | None:
        """Get cached text embedding"""
        cache_key = self.cache._generate_cache_key("embedding", model, text)

        cached = self.cache.get(cache_key)
        if cached and isinstance(cached, dict):
            return cached.get("embedding")
        return cached

    def set_embedding(
        self, model: str, text: str, embedding: list[float], ttl: timedelta | None = None
    ) -> bool:
        """Cache text embedding"""
        cache_key = self.cache._generate_cache_key("embedding", model, text)

        cached_embedding = {
            "embedding": embedding,
            "model": model,
            "text_hash": hashlib.sha256(text.encode()).hexdigest()[:12],
            "cached_at": str(int(time.time())),
        }

        return self.cache.set(
            cache_key,
            cached_embedding,
            ttl or timedelta(days=7),  # Embeddings cached longer
        )

    def clear_model_cache(self, model: str) -> int:
        """Clear all cached responses for a specific model"""
        patterns = [f"llm_response:*{model}*", f"embedding:*{model}*"]

        total_cleared = 0
        for pattern in patterns:
            total_cleared += self.cache.clear_pattern(pattern)

        logger.info(f"Cleared {total_cleared} cached responses for model {model}")
        return total_cleared


# Global cache instances
redis_cache = RedisCache()
ai_cache = AIResponseCache(redis_cache)


def cached_ai_response(
    ttl: timedelta | None = None, model_param: str = "model", prompt_param: str = "prompt"
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
            cache_kwargs = {k: v for k, v in kwargs.items() if k not in [model_param, prompt_param]}

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
                ai_cache.set_llm_response(model, prompt, response, ttl, **cache_kwargs)

            return response

        return wrapper

    return decorator
