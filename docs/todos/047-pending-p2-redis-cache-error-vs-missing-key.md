---
status: resolved
priority: p2
issue_id: "047"
tags: [code-review, security, architecture]
resolved_in: fix/resolve-todos-047-048
---

## Problem Statement

`redis_cache.get()` returns `None` for both missing keys and transient REST errors. The refresh token rotation path treats `None` as "family invalidated" (line 275 of auth.py), so a brief Upstash outage would reject all token refreshes as stolen, locking users out.

Identified by cubic (PR #54 review, P1).

## Proposed Solution

Modify `RedisCache.get()` to distinguish missing key from error. Options:
- A: Return a sentinel (e.g., `_MISSING` vs `None`) — minimal API change
- B: Raise on connection error, let caller decide — more explicit
- C: Add `get_or_raise()` method for callers that need the distinction

Then update auth.py refresh path: on connection error, skip replay detection (same as `is_connected == False` branch) instead of treating as theft.

## Files Affected

- `backend/app/core/cache.py` (RedisCache.get)
- `backend/app/api/v1/auth.py` (refresh endpoint Redis check)

## Effort Estimate

Medium (touches cache layer used by all Redis consumers)
