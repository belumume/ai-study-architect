---
status: resolved
priority: p2
issue_id: "031"
tags: [code-review, security]
---

## Problem Statement

`/auth/refresh` never invalidates old refresh tokens. Stolen token valid for 30 days. No token family tracking or blacklist.

## Resolution

Implemented refresh token rotation with Redis family tracking:

1. **Login** creates a token family (UUID `fid` claim in both access + refresh JWTs). Stores `SHA-256(refresh_token)` in Redis key `refresh_family:{fid}` with TTL = refresh token expiry (30 days).
2. **Refresh** validates the presented token hash against Redis. On match: issues new tokens in the same family, stores new hash (consuming old). On mismatch (replay): invalidates the entire family.
3. **Logout** invalidates the token family via Redis delete.
4. **Legacy migration**: Old tokens without `fid` claim are transparently migrated into a new family on first refresh.
5. **Redis unavailable**: Graceful degradation — tokens still rotate (new issued each refresh) but replay detection is skipped. Users are never locked out by Redis downtime.

### Redis key pattern
- Key: `refresh_family:{hex-uuid}`
- Value: SHA-256 hex digest of current valid refresh token
- TTL: `JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400` seconds

## Files Changed

- `backend/app/api/v1/auth.py` — rotation logic, family helpers, logout invalidation
- `backend/app/core/security.py` — `family_id` param on `create_access_token`/`create_refresh_token`, new `verify_token_claims()` function
- `backend/tests/test_auth.py` — new tests for cookie refresh, rotation claims, updated assertions
