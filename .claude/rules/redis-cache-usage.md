# Redis Cache Usage (Project-Specific)

## When This Applies
Any code that uses `redis_cache` from `app.core.cache`.

## The Sentinel Confusion Problem
`RedisCache.get()` returns `None` for BOTH:
- Key doesn't exist (normal cache miss)
- Connection error / Redis unavailable (silent failure)

`RedisCache._get_client()` NEVER raises — it returns `_NoOpCache` on failure.

This has caused bugs in 3 sessions (10, 14, 15). Resolved in session 15 via `CacheResult` dataclass + `get_with_status()`.

## Rules

### 1. Never use `_get_client()` in try/except for availability detection
```python
# WRONG — _get_client() never raises
try:
    redis_cache._get_client()
    # assume Redis is available
except Exception:
    # this never executes

# RIGHT — use the is_connected property
redis_cache._get_client()  # ensure lazy init
if redis_cache.is_connected:
    # Redis is available
```

### 2. Use `get_with_status()` when the distinction between miss and error matters
`get()` still returns `None` for both missing keys and errors. For auth, rate limits, feature flags — use `get_with_status()` which returns a `CacheResult(value, found, error)` dataclass. Fall back to `is_connected` checks only if `get_with_status()` is not appropriate.

### 3. Use atomic Redis operations
```python
# WRONG — race condition (get-then-set)
client.set(key, (redis_cache.get(key) or 0) + 1, ex=86400)

# RIGHT — atomic increment
client.incr(key)
client.expire(key, 86400)
```

### 4. Delete after commit, not before
When flushing buffered values from Redis to DB, delete the Redis keys AFTER `db.commit()` succeeds. If you delete first and commit fails, the data is lost.

## Resolved: CacheResult pattern (todo 047, session 15)
`RedisCache.get_with_status()` returns `CacheResult(value, found, error)` to distinguish hit/miss/error. Auth refresh uses this to skip replay detection on Redis error (not lockout). The legacy `get()` method still returns `None` for both cases — prefer `get_with_status()` for new code where the distinction matters.
