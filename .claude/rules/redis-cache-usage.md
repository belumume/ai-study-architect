# Redis Cache Usage (Project-Specific)

## When This Applies
Any code that uses `redis_cache` from `app.core.cache`.

## The Sentinel Confusion Problem
`RedisCache.get()` returns `None` for BOTH:
- Key doesn't exist (normal cache miss)
- Connection error / Redis unavailable (silent failure)

`RedisCache._get_client()` NEVER raises — it returns `_NoOpCache` on failure.

This has caused bugs in 3 sessions (10, 14, and pending todo 047).

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

### 2. Never assume `get() == None` means "key missing"
It could mean connection error. If the distinction matters (auth, rate limits, feature flags), check `is_connected` first or handle the ambiguity explicitly.

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

## Known Limitation (todo 047)
The cache wrapper API itself needs redesign to distinguish hit/miss/error. Until then, callers must work around it using `is_connected` checks.
