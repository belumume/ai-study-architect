"""
Tests for CacheResult and RedisCache.get_with_status()
"""

from unittest.mock import MagicMock

import pytest

from app.core.cache import CacheResult, RedisCache, _NoOpCache


class TestCacheResult:
    """Test CacheResult dataclass semantics"""

    def test_found_result(self):
        r = CacheResult(value="hello", found=True)
        assert r.value == "hello"
        assert r.found is True
        assert r.error is False

    def test_missing_result(self):
        r = CacheResult(value=None, found=False)
        assert r.value is None
        assert r.found is False
        assert r.error is False

    def test_error_result(self):
        r = CacheResult(value=None, found=False, error=True)
        assert r.value is None
        assert r.found is False
        assert r.error is True

    def test_frozen(self):
        r = CacheResult(value="x", found=True)
        with pytest.raises(AttributeError):
            r.value = "y"


class TestGetWithStatus:
    """Test RedisCache.get_with_status() three-state return"""

    def test_noop_cache_returns_not_found(self):
        """When Redis is not configured, get_with_status returns not-found (not error)"""
        cache = RedisCache()
        cache._redis_client = _NoOpCache()
        cache._connected = False

        result = cache.get_with_status("any_key")
        assert result.found is False
        assert result.error is False
        assert result.value is None

    def test_key_found(self):
        """When the underlying client returns a value, found=True"""
        cache = RedisCache()
        mock_client = MagicMock()
        mock_client.get.return_value = '"cached_value"'
        cache._redis_client = mock_client
        cache._connected = True

        result = cache.get_with_status("my_key")
        assert result.found is True
        assert result.error is False
        assert result.value == "cached_value"

    def test_key_found_non_json(self):
        """When the value is not JSON, return it as-is"""
        cache = RedisCache()
        mock_client = MagicMock()
        mock_client.get.return_value = "plain_string_not_json"
        cache._redis_client = mock_client
        cache._connected = True

        result = cache.get_with_status("my_key")
        assert result.found is True
        assert result.error is False
        assert result.value == "plain_string_not_json"

    def test_key_missing(self):
        """When the underlying client returns None, found=False, error=False"""
        cache = RedisCache()
        mock_client = MagicMock()
        mock_client.get.return_value = None
        cache._redis_client = mock_client
        cache._connected = True

        result = cache.get_with_status("missing_key")
        assert result.found is False
        assert result.error is False
        assert result.value is None

    def test_connection_error(self):
        """When the underlying client raises, error=True"""
        cache = RedisCache()
        mock_client = MagicMock()
        mock_client.get.side_effect = ConnectionError("Upstash unreachable")
        cache._redis_client = mock_client
        cache._connected = True

        result = cache.get_with_status("any_key")
        assert result.found is False
        assert result.error is True
        assert result.value is None

    def test_get_delegates_to_get_with_status(self):
        """RedisCache.get() should return the value from get_with_status()"""
        cache = RedisCache()
        mock_client = MagicMock()
        mock_client.get.return_value = '"hello"'
        cache._redis_client = mock_client
        cache._connected = True

        assert cache.get("key") == "hello"

    def test_get_returns_none_on_error(self):
        """RedisCache.get() backward compat: returns None on error"""
        cache = RedisCache()
        mock_client = MagicMock()
        mock_client.get.side_effect = ConnectionError("boom")
        cache._redis_client = mock_client
        cache._connected = True

        assert cache.get("key") is None

    def test_get_returns_none_on_miss(self):
        """RedisCache.get() backward compat: returns None on miss"""
        cache = RedisCache()
        mock_client = MagicMock()
        mock_client.get.return_value = None
        cache._redis_client = mock_client
        cache._connected = True

        assert cache.get("key") is None
