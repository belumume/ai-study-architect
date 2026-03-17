---
title: "Session 14: Batch Todo Resolution — Auth Hardening, Full-Text Search, Performance"
category: integration-issues
date: 2026-03-17
tags: [auth, security, performance, full-text-search, redis, parallel-agents, pr-review]
severity: medium
components: [auth.py, content.py, security.py, dependencies.py, api.ts, tokenStorage.ts, AuthContext.tsx]
session: 14
prs: ["#51", "#53", "#54", "#55"]
todos_resolved: ["029-039", "041-045"]
todos_created: ["046-049"]
---

# Session 14: Batch Todo Resolution (029-045)

## Problem

17 todos (029-045) accumulated from session 13's CE review. Mix of P1 security gaps, P2 performance issues, and P3 documentation cleanup. Needed systematic resolution without quality regression.

## Approach

### PR Strategy: 3+1 Split
- **PR #51** (docs): Zero-risk documentation cleanup (042-045). Merge first.
- **PR #54** (code): 12 code todos (030-041) as one reviewable unit.
- **PR #53** (migration): Full-text search with schema change — independently revertable.
- **PR #55** (tracking): Deferred review findings as new todos (046-049).

### Parallel Agent Execution
Used `/resolve_todo_parallel` with 6 parallel agents, each handling non-overlapping files:
1. `dependencies.py` — cookie fallback (033)
2. `AuthContext.tsx` — err:unknown type guard (039)
3. New `test_concept_extraction_integration.py` — 19 integration tests (041)
4. `content.py` — 3 performance fixes in different functions (035, 036, 037)
5. `auth.py` + `security.py` — token body removal + rotation (034, 031)
6. `tokenStorage.ts` + `api.ts` — dead code + typing (030, 038)

Manual: refresh queue tests (032) — depended on agent 6 completing api.ts changes.

## Key Solutions

### 1. Refresh Token Rotation with Redis Families (`auth.py`)
- Login creates UUID family, stores SHA-256(refresh_token) in Redis key `refresh_family:{fid}` with 30-day TTL
- Refresh validates hash. Match = rotate. Mismatch = invalidate family (theft).
- Logout passes `reason="logout"` to avoid polluting theft warning logs
- **Redis-down safeguard**: `redis_cache.is_connected` check at login — skip `fid` when Redis unavailable. Prevents false theft detection on recovery.

### 2. Full-Text Search (`content.py`, migration `d1e2f3a4b5c6`)
- tsvector column + GIN index + PostgreSQL trigger
- Weighted: `setweight(title, 'A') || setweight(description, 'B') || setweight(extracted_text, 'C')`
- `plainto_tsquery` + `ts_rank` ordering replaces LIKE-based O(n*text_size) scan
- SQLAlchemy `after_create` event listener for `create_all()` environments (tests, init_db)
- Drops obsolete LOWER() btree indexes

### 3. View Count Redis Buffer (`content.py`)
- `_increment_view_count()`: atomic Redis `INCR` (not get-then-set)
- `flush_view_counts()`: exported for external scheduler, deletes keys after `db.commit()`
- Graceful no-op when Redis unavailable

### 4. Content Stats Consolidation (`content.py`)
- 5 queries → 2: scalar aggregates + UNION ALL for grouped counts
- Saves 3 Neon round-trips (~150-450ms on cold start)

### 5. Cookie-Only Auth
- `tokenStorage.ts`: 98-line class → 6-line `clearLegacyTokens()` stub
- Request interceptor: removed Bearer injection, always deletes stale Authorization header
- Login/refresh: return `{"token_type": "bearer"}` only — no tokens in response body
- `get_optional_current_user`: added cookie fallback matching `get_current_user` pattern
- `security.py`: `datetime.now(UTC)` → `utcnow()` (4 occurrences, project pattern)

## Iteration & Review Fixes

### CI Failures (2 rounds)
1. **InterceptorFn type**: `(...args: unknown[]) => unknown` caused `TS18046` on every interceptor test. Fix: `(...args: any[]) => any` with eslint-disable comment.
2. **Redis mock for rotation test**: CI has no Redis → `is_connected` returns False → no `fid` in tokens → test assertion fails. Fix: mock `redis_cache` with in-memory dict for hash storage.

### Review Findings Addressed (4 rounds across 3 reviewers)
- **Cubic P1**: `_get_client()` never raises — Redis check was a no-op. Fixed: use `is_connected` property.
- **Cubic P1**: Non-atomic view counter (get-then-set). Fixed: Redis `INCR`.
- **Cubic P2**: Redis key deleted before `db.commit()`. Fixed: delete after commit.
- **Cubic P2**: Logout logs "potential theft" on every normal logout. Fixed: `reason` parameter.
- **CodeRabbit**: `datetime.now(UTC)` in security.py (4 occurrences). Fixed: `utcnow()`.
- **CodeRabbit**: Register missing `setLoading(false)` on error. Fixed: `finally` block.

### Deferred Findings (tracked as todos)
- **046**: `plainto_tsquery` loses substring/typeahead behavior
- **047**: `redis_cache.get()` indistinguishable error vs missing key
- **048**: Refresh endpoint always sets persistent cookies (should preserve session type)
- **049**: Register catch masks login failure as registration error

## Prevention Strategies

1. **Cache wrapper design**: When wrapping external services, ensure callers can distinguish "not found" from "connection error". Return sentinels or raise — never return the same value for both.
2. **CI parity**: If production uses Redis, CI tests touching Redis-dependent code need mocks. Pattern: mock at the module level (`patch("app.api.v1.auth.redis_cache")`), not at the client level.
3. **TypeScript test types**: Use `any` for mock interceptor functions in test files — `unknown` breaks strict mode when accessing mock return values. Add eslint-disable inline.
4. **PR hygiene**: Close noisy PRs and open fresh on same branch after 2+ review fix rounds. Prevents stale comment confusion.
5. **Datetime consistency**: `utcnow()` utility exists — grep for `datetime.now(UTC)` in CI or pre-commit to catch drift.

## Test Impact

- **Before**: 431 backend + 86 frontend = 517
- **After**: 452 backend + 91 frontend = 543 (+26 new tests)
- Coverage: 54.37% (above 54% CI floor)

## Related Documentation

- [Session 13 compound](session13-content-search-refresh-token-auth-fixes-compound.md) — predecessor, surfaced the 17 todos
- [Session 10 compound](session10-security-ci-phase2-monetization-compound.md) — security hardening foundation
- Todos 046-049 in `docs/todos/` — deferred review findings from this session
